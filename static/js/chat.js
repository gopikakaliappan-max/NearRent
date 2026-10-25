document.addEventListener("DOMContentLoaded", () => {
  const app = document.getElementById("chat-app");
  if (!app) return;
  const api = app.dataset.api;
  const list = document.getElementById("chat-messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  let lastId = 0;
  let loading = false;

  function addMessage(message) {
    const row = document.createElement("div");
    row.className = "chat-message " + (message.mine ? "mine" : "theirs");
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    const author = document.createElement("strong");
    author.textContent = message.mine ? "You" : message.sender;
    const body = document.createElement("p");
    body.textContent = message.body; // textContent prevents user messages being interpreted as HTML.
    const time = document.createElement("small");
    time.textContent = message.created_at;
    bubble.append(author, body, time);
    row.appendChild(bubble);
    list.appendChild(row);
    lastId = Math.max(lastId, message.id);
  }

  async function refresh() {
    if (loading) return;
    loading = true;
    try {
      const response = await fetch(api + "?after=" + lastId, {headers: {"X-Requested-With": "XMLHttpRequest"}});
      if (!response.ok) throw new Error("Unable to load messages");
      const data = await response.json();
      const loadingNote = list.querySelector(".chat-loading");
      if (loadingNote) loadingNote.remove();
      data.messages.forEach(addMessage);
      if (data.messages.length) list.scrollTop = list.scrollHeight;
      if (!list.children.length) list.innerHTML = '<p class="chat-empty">No messages yet. Start by agreeing on the handover details.</p>';
    } catch (err) {
      if (!list.children.length) list.textContent = "Could not load messages. Refresh the page to try again.";
    } finally {
      loading = false;
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const body = input.value.trim();
    if (!body) return;
    const csrf = form.querySelector('[name="csrfmiddlewaretoken"]').value;
    const submit = form.querySelector("button[type='submit']");
    submit.disabled = true;
    try {
      const response = await fetch(api, {
        method: "POST",
        headers: {"X-CSRFToken": csrf, "Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest"},
        body: new URLSearchParams({body})
      });
      if (!response.ok) throw new Error("Message could not be sent");
      input.value = "";
      await refresh();
    } catch (err) {
      alert("Message could not be sent. Please try again.");
    } finally {
      submit.disabled = false;
      input.focus();
    }
  });

  refresh();
  window.setInterval(refresh, 3000); // Lightweight polling; no Channels/WebSocket setup required.
});
