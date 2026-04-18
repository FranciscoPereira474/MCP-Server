const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");

// Unique thread_id per browser session — keeps conversation memory isolated
const threadId = "session-" + Math.random().toString(36).slice(2, 10);

function appendMessage(role, text) {
  const div = document.createElement("div");
  div.className = "message " + role;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;

  inputEl.value = "";
  sendBtn.disabled = true;

  appendMessage("user", text);
  const thinking = appendMessage("thinking", "Thinking...");

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, thread_id: threadId }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Server error: " + res.status);
    }
    const data = await res.json();

    thinking.remove();
    appendMessage("assistant", data.response);
  } catch (err) {
    thinking.remove();
    appendMessage("assistant", "Error: " + err.message);
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

// Send on Enter (Shift+Enter = new line)
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
