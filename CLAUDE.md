# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Project

```bash
# First-time setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the server
python server.py
# → http://127.0.0.1:8000
```

No build step, test suite, or linter is configured.

## Architecture

Perspective is a FastAPI web app that generates multi-stakeholder decision simulations using deterministic persona templates (no LLM). A user submits a scenario, and the tool produces perspectives and dialogue from 8 built-in organizational roles.

**Stack**: Python/FastAPI backend, vanilla JS frontend, JSON file storage (no database).

### Key Files

| File | Purpose |
|------|---------|
| `server.py` | FastAPI app — routes, WebSocket manager, file watcher, persona/queue management |
| `templates.py` | Persona template engine — generates perspectives and dialogue via string templates |
| `static/app.js` | Frontend state, WebSocket client, rendering logic |
| `static/index.html` | Main UI structure |
| `scenarios/` | Persisted scenario JSON files |
| `scenarios/.queue/` | Queue directory for Claude Code agent integration |
| `scenarios/.personas.json` | Custom user-defined personas (runtime-created) |

### Data Flow

1. User submits scenario form → `POST /generate`
2. Background thread runs `templates.py:generate_scenario()`, writing scenario JSON incrementally in 3 phases: metadata → perspectives → dialogue
3. `watchdog` file watcher detects changes and broadcasts diffs over WebSocket (`/ws`)
4. Frontend receives chunks and renders them with animations

### Scenario JSON Shape

```json
{
  "id": "scenario_{timestamp}",
  "title": "...",
  "scenario": "...",
  "mode": "split | dialogue | both",
  "personas": [{ "id": "pm", "name": "Product Manager", "role": "...", "color": "...", "avatar": "PM" }],
  "perspectives": [{ "persona_id": "pm", "thinking": "...", "tag_label": "...", "tag_content": "..." }],
  "dialogue": [{ "persona_id": "pm", "said": "...", "thought": "..." }]
}
```

### Persona Archetypes

8 built-in personas in `templates.py`: `pm`, `eng`, `sales`, `cs`, `design`, `uxr`, `sc`, `exec`. Each defines `concerns`, `strategies`, `dialogue_openers`, `dialogue_thoughts`, `tags`, and `vocab` — template strings with `{detail}`, `{topic}`, `{timeframe}` placeholders filled by `extract_details()`.

### Claude Code Queue Integration

The "Export for Claude Code" button writes a config to `scenarios/.queue/{timestamp}.json`. This is designed for an external Claude Code agent to monitor, process with an actual LLM, and write results back to `scenarios/`.
