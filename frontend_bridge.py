import os
import re
import threading
import queue
import subprocess
from pathlib import Path

from flask import Flask, jsonify, render_template, request


MAX_CHARS = 1200
PROMPT = "You: "

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, template_folder="templates", static_folder="static")

_process = None
_output_queue: "queue.Queue[str]" = queue.Queue()
_io_lock = threading.Lock()


def _reader_thread(proc: subprocess.Popen):
    """Continuously read chatbot stdout one char at a time into a queue."""
    while True:
        ch = proc.stdout.read(1)
        if ch == "":
            break
        _output_queue.put(ch)


def _start_chatbot_process():
    global _process

    if _process is not None and _process.poll() is None:
        return

    _process = subprocess.Popen(
        ["python3", "-u", str(BASE_DIR / "chatbot.py")],
        cwd=str(BASE_DIR),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=0,
    )

    threading.Thread(target=_reader_thread, args=(_process,), daemon=True).start()
    _read_until_prompt(timeout=30)


def _read_until_prompt(timeout: float = 20.0) -> str:
    """Read buffered output until terminal prompt appears."""
    buffer = ""
    while True:
        try:
            ch = _output_queue.get(timeout=timeout)
        except queue.Empty as exc:
            raise TimeoutError("Timed out waiting for chatbot output.") from exc

        buffer += ch
        if buffer.endswith(PROMPT):
            return buffer


def _extract_answer(raw_text: str) -> str:
    """Parse AI answer from terminal-style output block."""
    text = raw_text
    if text.endswith(PROMPT):
        text = text[: -len(PROMPT)]

    match = re.search(r"AI:\s*(.*)", text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()

    return text.strip() or "(No response received)"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(silent=True) or {}
    user_message = (body.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Please enter a message."}), 400

    if len(user_message) > MAX_CHARS:
        return jsonify({"error": f"Message too long (max {MAX_CHARS} characters)."}), 400

    with _io_lock:
        try:
            _start_chatbot_process()

            assert _process is not None and _process.stdin is not None
            _process.stdin.write(user_message + "\n")
            _process.stdin.flush()

            raw_output = _read_until_prompt(timeout=60)
            answer = _extract_answer(raw_output)
            return jsonify({"reply": answer})
        except Exception as exc:
            return jsonify({"error": f"Bridge error: {exc}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
