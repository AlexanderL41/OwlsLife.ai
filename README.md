# FAU Chatbot (Frontend + Simple Flask backend), Scroll to Bottom for Run Instructions Once Ready

This project contains a minimal frontend and a small Flask backend to demonstrate a FAU chat UI with a 1200-character input limit and university inspired colors.

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




# INSTRUCTIONS for chatbot.py (Old Prototype):
The .env file for my project has been hidden in recent patches to keep API keys private (API keys leaked in previous versions have been deactivated),
so the user reading this must obtain a Groq API key (can be done for free as of April 2026) and insert this into their own .env file 
```bash
GROQ_API_KEY="INSERT_API_KEY_HERE"
```
Once all relevant imports to this python file have been downloaded and Groq API key obtained, do the following to run (VS Code):
1. Click the run tab at the top of VS Code, then click the option called "Run Without Debugging" (Ctrl+F5)
(no front end was developed for this prototype, the AI responses will appear in terminal)

# INSTRUCTIONS for FAU AI Assistant (Latest):
Once all requirements, imports, llama3 AI model etc. are downloaded, do the following to run the project (VS Code):
1. Open new VS Code terminal, then split into two terminals
2. In first terminal, type the following to activate the llama3 AI model
```bash
ollama run llama3
```
3. In second terminal, type the following to enter the backend directory, where app.py is located
```bash
cd backend
```
4. Continuing in second terminal, type this to run the app.py python file
```bash
python app.py
```
5. Navigate to index.html, then in the bottom right corner of VS Code press the "Go Live" button to open the user interface
(if a run is currently active or you want to repeat, press the "discard" button in the same location then press again once it says "go live")
6. If all steps are followed, then you should have been redirected to a user interface, where you can ask any question that the FAU AI assistant will respond to accordingly
7. Enjoy!

