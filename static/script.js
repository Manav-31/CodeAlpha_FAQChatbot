(() => {
  const { college, popular } = JSON.parse(document.getElementById("bot-data").textContent);
  const MIN_TYPING_MS = 500; // short pause so replies don't appear instantly

  const $ = (id) => document.getElementById(id);
  const messages = $("messages");
  const form = $("chat-form");
  const input = $("message-input");
  const sendBtn = $("send-btn");

  let busy = false;

  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  // ---------- Rendering ----------

  function addUserMessage(text) {
    const msg = element("div", "msg user");
    msg.append(element("div", "bubble", text));
    messages.append(msg);
    scrollToBottom();
  }

  function addBotMessage({ text, meta = "", suggestions = [], isError = false }) {
    const msg = element("div", isError ? "msg bot error" : "msg bot");
    const body = element("div", "msg-body");
    body.append(element("div", "bubble", text));
    if (meta) body.append(element("div", "meta", meta));
    if (suggestions.length) {
      const chips = element("div", "chips");
      for (const question of suggestions) {
        const chip = element("button", "chip", question);
        chip.type = "button";
        chip.dataset.question = question;
        chips.append(chip);
      }
      body.append(chips);
    }
    msg.append(element("div", "avatar", "a"), body);
    messages.append(msg);
    scrollToBottom();
  }

  function showTyping() {
    const msg = element("div", "msg bot");
    const bubble = element("div", "bubble typing");
    bubble.setAttribute("aria-label", "Assistant is typing");
    bubble.append(element("span"), element("span"), element("span"));
    const body = element("div", "msg-body");
    body.append(bubble);
    msg.append(element("div", "avatar", "a"), body);
    messages.append(msg);
    scrollToBottom();
    return msg;
  }

  function showWelcome() {
    messages.replaceChildren();
    addBotMessage({
      text: `Hi! I'm the admissions assistant for ${college}, a fictional college made up for this demo. `
        + "Ask me about applying, courses, fees, hostel or deadlines.",
      suggestions: popular,
    });
  }

  function describeMatch(reply) {
    if (!reply.matched_question || reply.category === "Small talk") return "";
    return `Matched “${reply.matched_question}” · similarity ${reply.score.toFixed(2)}`;
  }

  // ---------- Asking ----------

  async function ask(question) {
    question = question.trim();
    if (!question || busy) return;

    busy = true;
    sendBtn.disabled = true;
    input.value = "";
    addUserMessage(question);
    const typing = showTyping();
    const started = Date.now();

    let message;
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      });
      const reply = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(reply.error || `Request failed (HTTP ${response.status}).`);
      message = { text: reply.answer, meta: describeMatch(reply), suggestions: reply.suggestions };
    } catch (err) {
      message = {
        text: err instanceof TypeError ? "I can't reach the server. Make sure app.py is running." : err.message,
        isError: true,
      };
    }

    await wait(MIN_TYPING_MS - (Date.now() - started));
    typing.remove();
    addBotMessage(message);
    busy = false;
    sendBtn.disabled = false;
    input.focus();
  }

  // ---------- Events ----------

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    ask(input.value);
  });

  messages.addEventListener("click", (event) => {
    const chip = event.target.closest(".chip");
    if (chip) ask(chip.dataset.question);
  });

  document.querySelectorAll(".topic-question").forEach((button) => {
    button.addEventListener("click", () => ask(button.dataset.question));
  });

  $("new-chat").addEventListener("click", () => {
    if (!busy) showWelcome();
    input.focus();
  });

  showWelcome();
})();
