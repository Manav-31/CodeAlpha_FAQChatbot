(() => {
  const { college, popular, categories } = JSON.parse(document.getElementById("bot-data").textContent);
  const MIN_TYPING_MS = 500; // short pause so replies don't appear instantly
  const TEASER_DELAY_MS = 2000;

  const $ = (id) => document.getElementById(id);
  const panel = $("chat-panel");
  const launcher = $("chat-launcher");
  const teaser = $("chat-teaser");
  const messages = $("messages");
  const form = $("chat-form");
  const input = $("message-input");
  const sendBtn = $("send-btn");

  let busy = false;
  const asked = new Set(); // FAQ questions answered in this chat; the server won't suggest them again

  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const timeNow = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  // ---------- Opening and closing the widget ----------

  function openChat() {
    panel.classList.add("is-open");
    launcher.classList.add("is-open");
    launcher.setAttribute("aria-expanded", "true");
    teaser.hidden = true;
    input.focus();
  }

  function closeChat() {
    panel.classList.remove("is-open");
    launcher.classList.remove("is-open");
    launcher.setAttribute("aria-expanded", "false");
    launcher.focus();
  }

  // ---------- Rendering messages ----------

  function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  function addUserMessage(text) {
    const msg = element("div", "msg user");
    msg.append(element("div", "bubble", text), element("div", "meta", timeNow()));
    messages.append(msg);
    scrollToBottom();
  }

  // `chips` are {label, question} to ask, {label, category} to list a topic, or {label, browse: true}.
  function addBotMessage({ text, meta = "", chips = [], isError = false }) {
    const msg = element("div", isError ? "msg bot error" : "msg bot");
    msg.append(element("div", "bubble", text));
    msg.append(element("div", "meta", meta ? `${timeNow()} · ${meta}` : timeNow()));
    if (chips.length) {
      const row = element("div", "chips");
      for (const chip of chips) {
        const button = element("button", chip.browse ? "chip chip-browse" : "chip", chip.label);
        button.type = "button";
        if (asked.has(chip.question)) {
          button.classList.add("chip-asked");
          button.title = "Already asked";
        }
        if (chip.question) button.dataset.question = chip.question;
        if (chip.category) button.dataset.category = chip.category;
        if (chip.browse) button.dataset.browse = "";
        row.append(button);
      }
      msg.append(row);
    }
    messages.append(msg);
    scrollToBottom();
  }

  function showTyping() {
    const msg = element("div", "msg bot");
    const bubble = element("div", "bubble typing");
    bubble.setAttribute("aria-label", "Assistant is typing");
    bubble.append(element("span"), element("span"), element("span"));
    msg.append(bubble);
    messages.append(msg);
    scrollToBottom();
    return msg;
  }

  const questionChips = (questions) => questions.map((question) => ({ label: question, question }));
  const BROWSE_CHIP = { label: "Browse all topics", browse: true };

  function showWelcome() {
    asked.clear();
    messages.replaceChildren();
    addBotMessage({
      text: `Hello! I can help with questions about admissions at ${college} (a fictional college made up `
        + "for this demo). Choose an option below or type your question.",
      chips: [...questionChips(popular), BROWSE_CHIP],
    });
  }

  function showTopics() {
    addBotMessage({
      text: "Select a topic:",
      chips: Object.keys(categories).map((category) => ({ label: category, category })),
    });
  }

  function showTopic(category) {
    addBotMessage({ text: `Questions about ${category.toLowerCase()}:`, chips: questionChips(categories[category]) });
  }

  function describeMatch(reply) {
    if (!reply.matched_question || reply.category === "Small talk") return "";
    return `Matched: ${reply.matched_question} (${reply.score.toFixed(2)})`;
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
        body: JSON.stringify({ message: question, asked: [...asked] }),
      });
      const reply = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(reply.error || `Request failed (HTTP ${response.status}).`);
      if (reply.matched_question && reply.category !== "Small talk") asked.add(reply.matched_question);
      const chips = questionChips(reply.suggestions);
      if (!reply.matched_question) chips.push(BROWSE_CHIP);
      message = { text: reply.answer, meta: describeMatch(reply), chips };
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

  launcher.addEventListener("click", () => (panel.classList.contains("is-open") ? closeChat() : openChat()));
  $("chat-close").addEventListener("click", closeChat);
  $("chat-restart").addEventListener("click", () => {
    if (!busy) showWelcome();
    input.focus();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && panel.classList.contains("is-open")) closeChat();
  });

  // Buttons on the page: open the chat, optionally asking a question straight away.
  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-ask], [data-open-chat]");
    if (!trigger) return;
    openChat();
    if (trigger.dataset.ask) ask(trigger.dataset.ask);
  });

  messages.addEventListener("click", (event) => {
    const chip = event.target.closest(".chip");
    if (!chip || busy) return;
    if (chip.dataset.question) ask(chip.dataset.question);
    else if (chip.dataset.category) showTopic(chip.dataset.category);
    else if ("browse" in chip.dataset) showTopics();
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    ask(input.value);
  });

  $("teaser-close").addEventListener("click", () => {
    teaser.hidden = true;
  });

  showWelcome();
  setTimeout(() => {
    if (!panel.classList.contains("is-open")) teaser.hidden = false;
  }, TEASER_DELAY_MS);
})();
