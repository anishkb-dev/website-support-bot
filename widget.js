/* Support chat widget. Embed with:
   <script src="https://your-bot.example.com/widget.js" data-api="https://your-bot.example.com" data-title="Help"></script> */
(function () {
  var tag = document.currentScript;
  var API = (tag.getAttribute("data-api") || new URL(tag.src).origin).replace(/\/$/, "");
  var TITLE = tag.getAttribute("data-title") || "Ask us anything";
  var COLOR = tag.getAttribute("data-color") || "#1f5e4b";

  var host = document.createElement("div");
  document.body.appendChild(host);
  var root = host.attachShadow({ mode: "open" }); // keeps the host site's CSS out
  root.innerHTML =
    "<style>" +
    "*{box-sizing:border-box;font:14px/1.45 system-ui,-apple-system,sans-serif}" +
    ".bubble{position:fixed;right:20px;bottom:20px;width:56px;height:56px;border-radius:50%;border:0;background:" + COLOR + ";color:#fff;font-size:24px;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.25);z-index:2147483646}" +
    ".panel{position:fixed;right:20px;bottom:88px;width:340px;max-width:calc(100vw - 32px);height:460px;max-height:calc(100vh - 110px);display:none;flex-direction:column;background:#fff;color:#1d1d1b;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.25);overflow:hidden;z-index:2147483647}" +
    ".panel.open{display:flex}" +
    ".head{background:" + COLOR + ";color:#fff;padding:12px 14px;font-weight:600}" +
    ".log{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;background:#f6f7f6}" +
    ".msg{max-width:85%;padding:8px 11px;border-radius:12px;white-space:pre-wrap}" +
    ".me{align-self:flex-end;background:" + COLOR + ";color:#fff}" +
    ".bot{align-self:flex-start;background:#fff;border:1px solid #e2e5e3}" +
    ".src{display:block;margin-top:5px;font-size:12px;color:#6b706d}" +
    "form{display:flex;gap:6px;padding:10px;border-top:1px solid #e2e5e3}" +
    "input{flex:1;padding:9px 10px;border:1px solid #cfd4d1;border-radius:8px;color:#1d1d1b;background:#fff}" +
    "form button{padding:9px 12px;border:0;border-radius:8px;background:" + COLOR + ";color:#fff;cursor:pointer}" +
    "</style>" +
    '<button class="bubble" aria-label="Open support chat">&#128172;</button>' +
    '<div class="panel" role="dialog" aria-label="Support chat"><div class="head"></div><div class="log" aria-live="polite"></div>' +
    '<form><input aria-label="Your question" placeholder="Type your question..." maxlength="500"><button>Send</button></form></div>';

  var $ = function (s) { return root.querySelector(s); };
  var panel = $(".panel"), log = $(".log"), input = $("input");
  $(".head").textContent = TITLE;

  function add(cls, text, sources) {
    var div = document.createElement("div");
    div.className = "msg " + cls;
    div.textContent = text; // textContent, never innerHTML: answers are untrusted
    if (sources && sources.length) {
      var s = document.createElement("span");
      s.className = "src";
      s.textContent = "Source: " + sources.map(function (x) { return x.source + " \u203a " + x.location; }).join(", ");
      div.appendChild(s);
    }
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
    return div;
  }

  $(".bubble").onclick = function () {
    panel.classList.toggle("open");
    if (!log.children.length) add("bot", "Hi! Ask me about orders, shipping, returns and more.");
    input.focus();
  };

  $("form").onsubmit = function (e) {
    e.preventDefault();
    var q = input.value.trim();
    if (!q) return;
    input.value = "";
    add("me", q);
    var wait = add("bot", "...");
    fetch(API + "/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q }) })
      .then(function (r) { if (!r.ok) throw r; return r.json(); })
      .then(function (d) { wait.remove(); add("bot", d.answer, d.sources); })
      .catch(function () { wait.textContent = "Sorry, something went wrong. Please try again."; });
  };
})();
