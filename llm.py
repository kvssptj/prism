"""LLM provider abstraction for PRISM — The Stakeholder Simulator."""

import base64
import json
import re
import shutil
import subprocess
import time
from pathlib import Path


class LLMGenerationError(Exception):
    pass


def parse_settings(header_value: str | None) -> dict:
    """Decode base64 header → settings dict. Returns {} on failure."""
    if not header_value:
        return {}
    try:
        return json.loads(base64.b64decode(header_value).decode())
    except Exception:
        return {}


def build_prompt(scenario_text: str, persona_ids: list, personas: list, mode: str, context: dict, settings: dict) -> str:
    """Construct LLM prompt requesting JSON-only response in scenario schema format."""
    from templates import ARCHETYPES

    domain = settings.get("domain", "product management at a B2B SaaS company")
    stage = context.get("stage", "series_a")
    market = context.get("market", "b2b")
    deadline = context.get("deadline", "this_week")

    # Build few-shot examples from archetypes for 2 personas
    example_lines = []
    for pid in persona_ids[:2]:
        arch = ARCHETYPES.get(pid, ARCHETYPES.get("pm"))
        concern_example = arch["concerns"][0].replace("{detail}", "this change").replace("{topic}", "the situation").replace("{timeframe}", "this quarter")
        strategy_example = arch["strategies"][0]
        example_lines.append(f'- {pid} thinking style: "{concern_example}"')
        example_lines.append(f'- {pid} recommendation style: "{strategy_example}"')
    examples_block = "\n".join(example_lines)

    # Personas list
    personas_block = "\n".join(f'- {p["id"]}: {p["name"]}, {p["role"]}' for p in personas)
    persona_ids_str = ", ".join(persona_ids)

    include_dialogue = mode in ("dialogue", "both")
    dialogue_instruction = (
        f'\n  "dialogue": [\n    {{"persona_id": "pm", "said": "<what they say aloud, 1-3 sentences, direct>", "thought": "<inner monologue, 1-2 sentences>"}}\n  ]'
        if include_dialogue else ""
    )
    n_turns = len(persona_ids)

    prompt = f"""You are generating a multi-stakeholder decision simulation for {domain}.
Return ONLY a valid JSON object. No markdown fences, no explanation, no extra text.

Output format:
{{
  "perspectives": [
    {{
      "persona_id": "pm",
      "thinking": "<2-4 sentences, 1st person, specific to this scenario>",
      "tag_label": "<one of: Strategy|Technical Reality|Impact|Risk Assessment|Urgency|Key Question|Blind Spot|Mitigation|Priority>",
      "tag_content": "<1-2 sentences concrete recommendation>"
    }}
  ]{(',' + dialogue_instruction) if include_dialogue else ''}
}}

Style guide — write in this voice (drawn from actual persona templates):
{examples_block}
Keep the same specificity, directness, and internal tension.

Company context: {stage} stage, {market} market, deadline: {deadline}
Domain: {domain}

Personas in this scenario:
{personas_block}

Scenario:
{scenario_text}

Produce JSON for exactly these personas in this order: {persona_ids_str}
{"Dialogue should have " + str(n_turns) + " turns, one per persona. First speaker frames the problem. Last speaker proposes a path forward." if include_dialogue else ""}"""

    return prompt


def _extract_json(text: str) -> dict:
    """Strip markdown fences, parse JSON."""
    text = text.strip()
    # Remove markdown code fences
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMGenerationError(f"Failed to parse LLM JSON response: {e}\nResponse: {text[:500]}")


def _write_incremental(filepath: Path, scenario_data: dict, perspectives: list, dialogue: list, delay: float = 0.35):
    """Write metadata first, then perspectives one-by-one, then dialogue turns."""
    data = {**scenario_data, "perspectives": [], "dialogue": []}
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    time.sleep(0.8)

    for p in perspectives:
        data["perspectives"].append(p)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        time.sleep(delay)

    for d in dialogue:
        data["dialogue"].append(d)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        time.sleep(delay + 0.1)


def generate_with_claude(settings: dict, filepath: Path, scenario_data: dict, prompt: str) -> None:
    """Call Anthropic SDK to generate perspectives."""
    try:
        import anthropic
    except ImportError:
        raise LLMGenerationError("anthropic package not installed. Run: pip install anthropic")

    api_key = settings.get("claudeApiKey", "").strip()
    if not api_key:
        raise LLMGenerationError("Claude API key not configured")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text
    result = _extract_json(text)
    _write_incremental(filepath, scenario_data, result.get("perspectives", []), result.get("dialogue", []))


def generate_with_openai(settings: dict, filepath: Path, scenario_data: dict, prompt: str) -> None:
    """Call OpenAI SDK to generate perspectives."""
    try:
        import openai
    except ImportError:
        raise LLMGenerationError("openai package not installed. Run: pip install openai")

    api_key = settings.get("openaiApiKey", "").strip()
    if not api_key:
        raise LLMGenerationError("OpenAI API key not configured")

    model = settings.get("openaiModel", "gpt-4o")
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
    )
    text = response.choices[0].message.content
    result = _extract_json(text)
    _write_incremental(filepath, scenario_data, result.get("perspectives", []), result.get("dialogue", []))


def generate_with_ollama(settings: dict, filepath: Path, scenario_data: dict, prompt: str) -> None:
    """POST to Ollama /api/generate."""
    try:
        import httpx
    except ImportError:
        raise LLMGenerationError("httpx package not installed. Run: pip install httpx")

    base_url = settings.get("ollamaUrl", "http://localhost:11434").rstrip("/")
    model = settings.get("ollamaModel", "llama3")

    try:
        response = httpx.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120.0,
        )
        response.raise_for_status()
        text = response.json().get("response", "")
    except Exception as e:
        raise LLMGenerationError(f"Ollama request failed: {e}")

    result = _extract_json(text)
    _write_incremental(filepath, scenario_data, result.get("perspectives", []), result.get("dialogue", []))


def generate_with_claude_code(queue_file: Path, scenarios_dir: Path) -> None:
    """Invoke claude CLI to process a queue item."""
    if not shutil.which("claude"):
        raise LLMGenerationError("claude CLI not found. Install Claude Code to use this feature.")

    with open(queue_file) as f:
        item = json.load(f)

    scenario_text = item.get("scenario", "")
    persona_ids = item.get("personas", ["pm", "eng", "sales", "cs"])
    mode = item.get("mode", "both")
    context = item.get("context") or {}

    # Build minimal personas list
    personas = [{"id": pid, "name": pid.title(), "role": "Stakeholder"} for pid in persona_ids]
    try:
        from server import _build_persona_list
        personas = _build_persona_list(persona_ids)
    except Exception:
        pass

    settings = item.get("settings") or {}
    settings.setdefault("domain", "product management at a B2B SaaS company")
    prompt = build_prompt(scenario_text, persona_ids, personas, mode, context, settings)

    try:
        result = subprocess.run(
            ["claude", "--print", prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise LLMGenerationError(f"claude CLI error: {result.stderr[:500]}")
        text = result.stdout
    except subprocess.TimeoutExpired:
        raise LLMGenerationError("claude CLI timed out after 120s")

    parsed = _extract_json(text)

    import re as _re
    clean_name = _re.sub(r'[^a-z0-9]+', '_', scenario_text[:50].lower()).strip('_')
    timestamp = int(time.time())
    filename = f"{clean_name}_{timestamp}.json"
    filepath = scenarios_dir / filename

    title = scenario_text[:80].rstrip('.')
    scenario_data = {
        "id": f"scenario_{timestamp}",
        "title": title,
        "scenario": scenario_text,
        "mode": mode,
        "context": context,
        "personas": personas,
    }
    _write_incremental(filepath, scenario_data, parsed.get("perspectives", []), parsed.get("dialogue", []))


def generate_llm(settings: dict, scenario_text: str, persona_ids: list, personas: list, mode: str, context: dict, scenarios_dir: Path) -> str:
    """Main entry point. Write metadata first, dispatch to provider, return filename."""
    import re as _re

    provider = settings.get("provider", "none")
    timestamp = int(time.time())
    clean_name = _re.sub(r'[^a-z0-9]+', '_', scenario_text[:50].lower()).strip('_')
    filename = f"{clean_name}_{timestamp}.json"
    filepath = scenarios_dir / filename

    title = scenario_text[:80].rstrip('.')
    scenario_data = {
        "id": f"scenario_{timestamp}",
        "title": title,
        "scenario": scenario_text,
        "mode": mode,
        "context": context or {},
        "personas": personas,
    }

    prompt = build_prompt(scenario_text, persona_ids, personas, mode, context or {}, settings)

    if provider == "claude":
        generate_with_claude(settings, filepath, scenario_data, prompt)
    elif provider == "openai":
        generate_with_openai(settings, filepath, scenario_data, prompt)
    elif provider == "ollama":
        generate_with_ollama(settings, filepath, scenario_data, prompt)
    else:
        raise LLMGenerationError(f"Unknown provider: {provider}")

    return filename
