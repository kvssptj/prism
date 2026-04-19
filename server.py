import asyncio
import base64
import json
import os
import shutil
import threading
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from templates import DEFAULT_PERSONAS, generate_scenario
from llm import parse_settings, generate_llm, LLMGenerationError

BASE_DIR = Path(__file__).parent
SCENARIOS_DIR = BASE_DIR / "scenarios"
QUEUE_DIR = SCENARIOS_DIR / ".queue"
PERSONAS_FILE = SCENARIOS_DIR / ".personas.json"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI()

# --- WebSocket connection manager ---

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        for ws in list(self.active):
            try:
                await ws.send_json(message)
            except Exception:
                self.active.remove(ws)

manager = ConnectionManager()

# --- File watcher ---

last_known: dict[str, dict] = {}

def diff_scenario(filepath: Path) -> list[dict]:
    """Compare current file content against last known state, return new chunks."""
    try:
        with open(filepath) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    file_key = filepath.name
    prev = last_known.get(file_key, {})
    chunks = []

    # New scenario or metadata changed
    if not prev or data.get("title") != prev.get("title"):
        chunks.append({
            "type": "metadata",
            "id": data.get("id"),
            "title": data.get("title"),
            "scenario": data.get("scenario"),
            "mode": data.get("mode"),
            "personas": data.get("personas", []),
        })

    # New perspectives
    prev_perspectives = prev.get("perspectives", [])
    curr_perspectives = data.get("perspectives", [])
    for p in curr_perspectives[len(prev_perspectives):]:
        chunks.append({"type": "perspective", **p})

    # New dialogue turns
    prev_dialogue = prev.get("dialogue", [])
    curr_dialogue = data.get("dialogue", [])
    for d in curr_dialogue[len(prev_dialogue):]:
        chunks.append({"type": "dialogue", **d})

    last_known[file_key] = data
    return chunks


loop: asyncio.AbstractEventLoop | None = None

class ScenarioHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".json"):
            return
        self._handle(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".json"):
            return
        self._handle(event.src_path)

    def _handle(self, src_path: str):
        filepath = Path(src_path)
        chunks = diff_scenario(filepath)
        if chunks and loop:
            asyncio.run_coroutine_threadsafe(self._send_chunks(chunks), loop)

    async def _send_chunks(self, chunks: list[dict]):
        for chunk in chunks:
            await manager.broadcast(chunk)
            await asyncio.sleep(0.3)


observer = Observer()
observer.schedule(ScenarioHandler(), str(SCENARIOS_DIR), recursive=False)

# --- Helpers ---

def _load_custom_personas() -> list[dict]:
    if PERSONAS_FILE.exists():
        try:
            with open(PERSONAS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return []

def _save_custom_personas(personas: list[dict]):
    with open(PERSONAS_FILE, 'w') as f:
        json.dump(personas, f, indent=2)

def _build_persona_list(persona_ids: list[str], custom_personas: list[dict] | None = None) -> list[dict]:
    """Build full persona objects from IDs, merging defaults with custom."""
    custom_map = {}
    if custom_personas:
        for cp in custom_personas:
            custom_map[cp["id"]] = cp

    saved_custom = {p["id"]: p for p in _load_custom_personas()}
    custom_map.update(saved_custom)

    result = []
    for pid in persona_ids:
        if pid in DEFAULT_PERSONAS:
            p = DEFAULT_PERSONAS[pid]
            result.append({"id": pid, **p})
        elif pid in custom_map:
            result.append(custom_map[pid])
        else:
            result.append({"id": pid, "name": pid.title(), "role": "Stakeholder", "color": "#475569", "avatar": pid[:2].upper()})
    return result

# --- Routes ---

@app.on_event("startup")
async def startup():
    global loop
    loop = asyncio.get_event_loop()
    SCENARIOS_DIR.mkdir(exist_ok=True)
    QUEUE_DIR.mkdir(exist_ok=True)
    observer.start()
    asyncio.create_task(_process_queue())


async def _process_queue():
    """Poll queue dir every 3s; auto-process pending items via claude CLI."""
    while True:
        await asyncio.sleep(3)
        for queue_file in list(QUEUE_DIR.glob("*.json")):
            try:
                with open(queue_file) as f:
                    item = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
            if item.get("status") in ("processing", "done", "error"):
                continue
            # Mark as processing
            item["status"] = "processing"
            try:
                with open(queue_file, 'w') as f:
                    json.dump(item, f, indent=2)
            except OSError:
                continue
            threading.Thread(target=_run_queue_item, args=(queue_file,), daemon=True).start()


def _run_queue_item(queue_file: Path):
    from llm import generate_with_claude_code
    try:
        generate_with_claude_code(queue_file, SCENARIOS_DIR)
        queue_file.unlink(missing_ok=True)
    except Exception as e:
        try:
            with open(queue_file) as f:
                item = json.load(f)
            item["status"] = "error"
            item["error"] = str(e)
            with open(queue_file, 'w') as f:
                json.dump(item, f, indent=2)
        except OSError:
            pass

@app.on_event("shutdown")
async def shutdown():
    observer.stop()
    observer.join()

@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")

# --- Scenario CRUD ---

@app.get("/scenarios")
async def list_scenarios():
    scenarios = []
    for f in sorted(SCENARIOS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
        try:
            with open(f) as fh:
                data = json.load(fh)
            scenarios.append({
                "id": data.get("id", f.stem),
                "title": data.get("title", f.stem),
                "filename": f.name,
            })
        except (json.JSONDecodeError, OSError):
            continue
    return JSONResponse(scenarios)

@app.get("/scenarios/{filename}")
async def get_scenario(filename: str):
    filepath = SCENARIOS_DIR / filename
    if not filepath.exists() or not filepath.suffix == ".json":
        return JSONResponse({"error": "not found"}, status_code=404)
    with open(filepath) as f:
        return JSONResponse(json.load(f))

@app.delete("/scenarios/{filename}")
async def delete_scenario(filename: str):
    filepath = SCENARIOS_DIR / filename
    if not filepath.exists() or not filepath.suffix == ".json":
        return JSONResponse({"error": "not found"}, status_code=404)
    filepath.unlink()
    return JSONResponse({"deleted": True})

# --- Generate (template engine) ---

@app.post("/generate")
async def generate(request: Request):
    body = await request.json()
    scenario_text = body.get("scenario", "")
    persona_ids = body.get("personas", ["pm", "eng", "sales", "cs"])
    custom_personas = body.get("custom_personas", [])
    mode = body.get("mode", "both")
    context = body.get("context") or {}

    if not scenario_text.strip():
        return JSONResponse({"error": "scenario text is required"}, status_code=400)

    personas = _build_persona_list(persona_ids, custom_personas)

    settings_header = request.headers.get("X-LLM-Settings")
    settings = parse_settings(settings_header)
    provider = settings.get("provider", "none")

    def _run():
        if provider not in ("none", "claude_code"):
            try:
                generate_llm(settings, scenario_text, persona_ids, personas, mode, context, SCENARIOS_DIR)
            except LLMGenerationError:
                generate_scenario(scenario_text, persona_ids, personas, mode, context)
        else:
            generate_scenario(scenario_text, persona_ids, personas, mode, context)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return JSONResponse({"status": "generating", "personas": len(persona_ids)})


@app.get("/ollama/models")
async def list_ollama_models(url: str = "http://localhost:11434"):
    """Proxy to Ollama /api/tags. Returns {models: [...]} or {models: [], error: '...'}"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url.rstrip('/')}/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return JSONResponse({"models": models})
    except Exception as e:
        return JSONResponse({"models": [], "error": str(e)})

# --- Queue (for Claude Code) ---

@app.post("/queue")
async def queue_scenario(request: Request):
    body = await request.json()
    scenario_text = body.get("scenario", "")
    persona_ids = body.get("personas", ["pm", "eng", "sales", "cs"])
    custom_personas = body.get("custom_personas", [])
    mode = body.get("mode", "both")
    context = body.get("context") or {}

    if not scenario_text.strip():
        return JSONResponse({"error": "scenario text is required"}, status_code=400)

    import time
    filename = f"{int(time.time())}.json"
    config = {
        "scenario": scenario_text,
        "personas": persona_ids,
        "custom_personas": custom_personas,
        "mode": mode,
        "context": context,
    }
    with open(QUEUE_DIR / filename, 'w') as f:
        json.dump(config, f, indent=2)

    return JSONResponse({"queued": True, "filename": filename})

@app.get("/queue")
async def list_queue():
    items = []
    for f in sorted(QUEUE_DIR.glob("*.json"), key=os.path.getmtime):
        try:
            with open(f) as fh:
                data = json.load(fh)
            items.append({"filename": f.name, **data})
        except (json.JSONDecodeError, OSError):
            continue
    return JSONResponse(items)

@app.delete("/queue/{filename}")
async def delete_queue_item(filename: str):
    filepath = QUEUE_DIR / filename
    if filepath.exists():
        filepath.unlink()
        return JSONResponse({"deleted": True})
    return JSONResponse({"error": "not found"}, status_code=404)

# --- Custom Personas ---

@app.get("/personas")
async def get_personas():
    defaults = [{"id": k, **v, "custom": False} for k, v in DEFAULT_PERSONAS.items()]
    custom = [{"custom": True, **p} for p in _load_custom_personas()]
    return JSONResponse(defaults + custom)

@app.post("/personas")
async def save_persona(request: Request):
    body = await request.json()
    required = ["id", "name", "role", "color", "avatar"]
    if not all(k in body for k in required):
        return JSONResponse({"error": f"required fields: {required}"}, status_code=400)

    custom = _load_custom_personas()
    # Update existing or append
    found = False
    for i, p in enumerate(custom):
        if p["id"] == body["id"]:
            custom[i] = body
            found = True
            break
    if not found:
        custom.append(body)

    _save_custom_personas(custom)
    return JSONResponse({"saved": True})

# --- WebSocket ---

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
