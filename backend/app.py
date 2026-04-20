import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
import logging
from dotenv import load_dotenv

import requests

try:
    from langchain_community.vectorstores import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
except Exception:
    Chroma = None
    HuggingFaceEmbeddings = None

# -----------------------
# INIT / PATHS
# -----------------------
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
CHROMA_DIR = BACKEND_DIR / "chroma"
FEEDBACK_FILE = BACKEND_DIR / "feedback.json"

# Load environment variables from backend/.env, project/.env, or project/api.env
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "api.env")

# Ollama configuration: local Ollama server will be used for generation.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost").strip()
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral").strip()

# Allow running the backend without contacting Ollama (offline/local fallback)
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").strip().lower() in ("1", "true", "yes")

def _ollama_url(path: str) -> str:
    return f"http://{OLLAMA_HOST}:{OLLAMA_PORT}{path}"

# Serve project files so frontend can be opened from this Flask server.
app = Flask(__name__, static_folder=str(PROJECT_ROOT), static_url_path="")

# Configure simple logging to stderr so errors are visible in the terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Small premade FAQ fallback set. Edit these to suit your project.
PREMADE_FAQ = [
    ("admission", "For admissions information, check the FAU admissions page or contact the admissions office."),
    ("hours", "Campus hours vary by building — please check the official FAU website for current hours."),
    ("location", "FAU has multiple campuses; please specify which campus or check the FAU campus locations page."),
]


@app.after_request
def add_cors_headers(response):
    # Allow frontend calls when page is served from VS Code Live Server.
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

# -----------------------
# VECTOR DB (HUGGINGFACE)
# -----------------------
db = None
vector_init_error = None

try:
    if Chroma is None or HuggingFaceEmbeddings is None:
        raise RuntimeError("langchain/chroma dependencies are not installed")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings
    )
except Exception as e:
    vector_init_error = str(e)


@app.get("/")
def home():
    index_dir = PROJECT_ROOT / "Index"
    index_file = index_dir / "index.html"

    if index_file.exists():
        return send_from_directory(index_dir, "index.html")

    return jsonify({"error": f"Frontend file not found at {index_file}"}), 404


@app.get("/Index/index.html")
def home_index():
    index_dir = PROJECT_ROOT / "Index"
    index_file = index_dir / "index.html"

    if index_file.exists():
        return send_from_directory(index_dir, "index.html")

    return jsonify({"error": f"Frontend file not found at {index_file}"}), 404


@app.get("/health")
def health():
    # Check Ollama availability quickly
    ollama_ok = False
    try:
        ping = requests.get(_ollama_url("/api/tags"), timeout=2)
        ollama_ok = ping.ok
    except Exception:
        ollama_ok = False

    return jsonify(
        {
            "ok": True,
            "ollamaHost": OLLAMA_HOST,
            "ollamaPort": OLLAMA_PORT,
            "useOllama": bool(USE_OLLAMA),
            "ollamaModel": OLLAMA_MODEL,
            "ollamaAvailable": bool(ollama_ok),
            "chromaDir": str(CHROMA_DIR),
            "vectorDbReady": db is not None,
            "vectorInitError": vector_init_error,
        }
    )


def generate_with_ollama(prompt: str, timeout_secs: int = 10) -> str:
    """
    Send a prompt to the local Ollama API and return text output.
    """
    url = _ollama_url("/api/generate")
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "temperature": 0.2,
        "stream": False,
        "num_predict": 1024
        }

    try:
        logger.info("Sending request to Ollama: %s (timeout=%ss)", url, timeout_secs)
        resp = requests.post(url, json=payload, timeout=timeout_secs)
    except Exception as exc:
        # Log full exception to help terminal debugging and re-raise for upstream handling
        logger.exception("Ollama request failed")
        raise RuntimeError(f"Ollama request failed: {exc}") from exc

    if not resp.ok:
        logger.error("Ollama HTTP %s: %s", resp.status_code, resp.text)
        raise RuntimeError(f"Ollama HTTP {resp.status_code}: {resp.text}")

    try:
        parsed = resp.json()
    except Exception:
        # Some Ollama setups may return plain text
        return resp.text.strip()

    # Parse common keys returned by various Ollama versions
    if isinstance(parsed, dict):
        if "output" in parsed:
            out = parsed.get("output")
            if isinstance(out, str):
                return out.strip()
            if isinstance(out, list):
                return "".join([str(x) for x in out]).strip()
        if "text" in parsed:
            return parsed.get("text", "").strip()
        if "result" in parsed:
            res = parsed.get("result")
            if isinstance(res, list):
                text = "".join([r.get("content", "") if isinstance(r, dict) else str(r) for r in res])
                if text.strip():
                    return text.strip()
        choices = parsed.get("choices") or []
        if choices:
            first = choices[0]
            if isinstance(first, dict):
                return (first.get("text") or first.get("message") or "").strip()
            return str(first).strip()
        
        if "response" in parsed:
            return parsed["response"].strip()
# -----------------------
# CONTEXT RETRIEVAL
# -----------------------
def get_context(question):
    if not question:
        return "", []

    if db is None:
        return "", []

    try:
        docs = db.similarity_search(question, k=3)
    except Exception:
        docs = []

    context = "\n\n".join([doc.page_content for doc in docs])
    sources = []
    for doc in docs:
        text = (doc.page_content or "").strip().replace("\n", " ")
        excerpt = text[:220] + ("..." if len(text) > 220 else "")
        title = doc.metadata.get("source", "FAU knowledge base") if doc.metadata else "FAU knowledge base"
        sources.append({"title": title, "excerpt": excerpt})

    return "", []


def build_local_fallback_answer(question, context, sources):
    """
    Create a concise fallback answer from local context or a small premade FAQ set.
    Returns a short answer string or 'No answer available.' if nothing matches.
    """
    q = (question or "").strip()
    # Prefer local context if available
    if context:
        snippet = context.strip().replace("\n", " ")
        # Keep it short
        return snippet[:800].strip()

    # Check premade FAQ for simple keyword matches
    qlow = q.lower()
    for keyword, answer in PREMADE_FAQ:
        if keyword in qlow:
            return answer

    return "No answer available."

# -----------------------
# CHAT ENDPOINT
# -----------------------
@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    try:
        if request.method == "OPTIONS":
            return ("", 204)

        data = request.get_json(silent=True) or {}
        question = str(data.get("question", "")).strip()

        if not question:
            return jsonify({"error": "question required"}), 400

        context = ""
        sources = []

        prompt = f"""
You are a helpful assistant, you answer questions only related to Florida Atlantic University. Make your answers contain factual information from fau itself, and public opinion.

Question: {question}

Answer in 1-2 sentences only:
"""

        provider_used = None
        provider_errors = []
        answer = ""

        # Use Ollama if enabled; otherwise use the local fallback directly.
        if USE_OLLAMA:
            try:
                # Attempt to get an answer from Ollama; wait up to 10 seconds.
                answer = generate_with_ollama(prompt, timeout_secs=10)
                provider_used = "ollama"
            except Exception as ollama_exc:
                logger.warning("Ollama attempt failed (timeout or error): %s", ollama_exc)
                provider_errors.append(f"ollama: {ollama_exc}")
                # Fallback: create a concise answer from local context or premade FAQ
                answer = build_local_fallback_answer(question, context, sources)

        if not answer:
            # Either Ollama unavailable or disabled — use local fallback
            answer = build_local_fallback_answer(question, context, sources)

        response_payload = {"answer": answer, "sources": sources}
        if provider_used:
            response_payload["provider"] = provider_used
        if provider_errors:
            response_payload["providerErrors"] = provider_errors
            # Provide a short status message that can be surfaced in the frontend / terminal
            response_payload["statusMessage"] = "; ".join(provider_errors)

        return jsonify(response_payload)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/query", methods=["POST", "OPTIONS"])
def query_alias():
    # Compatibility alias for frontend versions that still call /query.
    return chat()


@app.route("/feedback", methods=["POST", "OPTIONS"])
def feedback():
    try:
        if request.method == "OPTIONS":
            return ("", 204)

        data = request.get_json(silent=True) or {}
        feedback_text = str(data.get("feedback", "")).strip()

        if not feedback_text:
            return jsonify({"error": "feedback required"}), 400

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": str(data.get("question", "")).strip(),
            "error": str(data.get("error", "")).strip(),
            "feedback": feedback_text,
            "client": str(data.get("client", "web")).strip() or "web",
        }

        FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

        existing_feedback = []
        if FEEDBACK_FILE.exists():
            try:
                with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                    parsed = json.load(f)
                    if isinstance(parsed, list):
                        existing_feedback = parsed
            except Exception:
                # If file is malformed, start fresh instead of crashing feedback collection.
                existing_feedback = []

        existing_feedback.append(entry)

        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_feedback, f, ensure_ascii=False, indent=2)

        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# OCR functionality removed — Ollama-only setup
# -----------------------
# RUN SERVER
# -----------------------
if __name__ == "__main__":
    app.run(debug=False)