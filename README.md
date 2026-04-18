# FAU Chatbot (Frontend + Simple Flask backend)

This project contains a minimal frontend and a small Flask backend to demonstrate a chat UI with a 1200-character input limit and Florida Atlantic University-inspired colors.

Files of interest

- `chatbot.py` — Flask app that serves the UI and exposes `POST /chat`. Reads `OPENAI_API_KEY` from environment to call the model; otherwise it returns a safe mock response (echo) for demoing the UI.
- `templates/index.html` — Chat UI (textarea with `maxlength=1200`, live char counter).
- `static/styles.css` — FAU-inspired styles (blue + red) and layout.
- `static/chat.js` — Client JS: handles input, shows messages, POSTs to `/chat`, and displays replies.
- `requirements.txt` — minimal dependencies.

Quick run (macOS / zsh)

1. Create and activate a virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Set your OpenAI-compatible API key to get real model responses. If omitted, the server returns a mock response so the UI is functional.

```bash
export OPENAI_API_KEY="sk_your_key_here"
# Optional: set a custom base URL
# export OPENAI_BASE_URL="https://api.groq.com/openai/v1"
```

4. Run the Flask app:

```bash
python3 chatbot.py
```

5. Open the UI:

- Navigate to `http://127.0.0.1:5000/` in your browser.

Notes

- The 1200-character limit is enforced both client-side (textarea `maxlength`) and server-side (`/chat` returns 400 if exceeded).
- The server uses an environment variable for the API key instead of embedding secrets in code.
- For production use, run behind a WSGI server (gunicorn/uvicorn) and add authentication/CORS as needed.

If you'd like, I can:
- Add per-session conversation memory (session cookie) so the assistant can keep context.
- Add a small automated sanity test that POSTs to `/chat` and asserts a reply.
- Tweak the UI branding (fonts, icons) or export a single-file HTML demo.
