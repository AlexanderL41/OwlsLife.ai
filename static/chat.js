(function () {
  const form = document.getElementById("chat-form");
  const messageEl = document.getElementById("message");
  const chatEl = document.getElementById("chat");
  const charsEl = document.getElementById("chars");
  const errorEl = document.getElementById("error");
  const sendButton = document.getElementById("send");
  const MAX_CHARS = 1200;

  function addMessage(text, kind) {
    const item = document.createElement("div");
    item.className = `message ${kind}`;
    item.textContent = text;
    chatEl.appendChild(item);
    chatEl.scrollTop = chatEl.scrollHeight;
    return item;
  }

  function setError(msg) {
    errorEl.textContent = msg || "";
  }

  function refreshCounter() {
    const len = messageEl.value.length;
    charsEl.textContent = String(len);
    sendButton.disabled = len === 0 || len > MAX_CHARS;
  }

  messageEl.addEventListener("input", refreshCounter);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    setError("");

    const message = messageEl.value.trim();
    if (!message) {
      setError("Please enter a message.");
      return;
    }
    if (message.length > MAX_CHARS) {
      setError("Message exceeds 1200 characters.");
      return;
    }

    addMessage(message, "user");
    messageEl.value = "";
    refreshCounter();

    const pending = addMessage("Thinking...", "bot");

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Request failed.");
      }

      pending.textContent = payload.reply || "(No response)";
    } catch (err) {
      pending.remove();
      setError(err.message || "Failed to fetch reply.");
    }
  });

  refreshCounter();
})();
