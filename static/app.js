/* Monico Jarvis console: chat, voice wave, mic input, optional TTS. */
(function () {
  "use strict";

  var log = document.getElementById("log");
  var form = document.getElementById("composer");
  var input = document.getElementById("input");
  var micBtn = document.getElementById("mic");
  var ttsBox = document.getElementById("tts");
  var statusLine = document.getElementById("status-line");
  var chips = document.getElementById("chips");
  var hintsBox = document.getElementById("hints");
  var waveLabel = document.getElementById("wave-label");

  /* ------------------------------------------------ voice wave canvas */
  var canvas = document.getElementById("wave");
  var ctx = canvas.getContext("2d");
  var energy = 0.25, targetEnergy = 0.25, t = 0;

  function sizeCanvas() {
    var r = canvas.getBoundingClientRect();
    canvas.width = Math.max(300, r.width * devicePixelRatio);
    canvas.height = 120 * devicePixelRatio;
  }
  window.addEventListener("resize", sizeCanvas);
  sizeCanvas();

  function drawWave() {
    t += 0.045;
    energy += (targetEnergy - energy) * 0.06;
    var w = canvas.width, h = canvas.height, mid = h / 2;
    ctx.clearRect(0, 0, w, h);
    ctx.lineWidth = 2 * devicePixelRatio;
    for (var pass = 0; pass < 3; pass++) {
      var amp = (h * 0.38 * energy) / (pass + 1);
      ctx.strokeStyle = pass === 0
        ? "rgba(0,229,255,.9)"
        : "rgba(0,229,255," + (0.35 - pass * 0.12) + ")";
      ctx.beginPath();
      for (var x = 0; x <= w; x += 4) {
        var y = mid
          + Math.sin(x * 0.012 + t * (1.6 + pass * 0.4)) * amp
          + Math.sin(x * 0.03 - t * 2.2) * amp * 0.4;
        if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
    // scan line
    var sx = ((t * 60) % (w + 80)) - 40;
    var grad = ctx.createLinearGradient(sx - 40, 0, sx + 40, 0);
    grad.addColorStop(0, "rgba(0,229,255,0)");
    grad.addColorStop(0.5, "rgba(0,229,255,.18)");
    grad.addColorStop(1, "rgba(0,229,255,0)");
    ctx.fillStyle = grad;
    ctx.fillRect(sx - 40, 0, 80, h);
    requestAnimationFrame(drawWave);
  }
  drawWave();

  function spike() { targetEnergy = 1; setTimeout(function () { targetEnergy = 0.25; }, 900); }

  /* ------------------------------------------------ messages */
  function addMsg(text, who, skill) {
    var div = document.createElement("div");
    div.className = "msg " + who;
    if (who === "jarvis") {
      var tag = document.createElement("span");
      tag.className = "skill-tag";
      tag.textContent = "jarvis" + (skill ? " · " + skill : "");
      div.appendChild(tag);
      var body = document.createElement("span");
      div.appendChild(body);
      typeInto(body, text);
    } else {
      div.textContent = text;
    }
    log.appendChild(div);
    div.scrollIntoView({ behavior: "smooth", block: "nearest" });
    return div;
  }

  function typeInto(el, text) {
    var i = 0;
    el.innerHTML = "";
    var cursor = document.createElement("span");
    cursor.className = "cursor";
    cursor.textContent = "▍";
    (function tick() {
      if (i < text.length) {
        el.textContent = text.slice(0, i + 2);
        el.appendChild(cursor);
        i += 2;
        setTimeout(tick, 8);
      } else {
        el.textContent = text;
      }
    })();
  }

  function speak(text) {
    if (!ttsBox.checked || !("speechSynthesis" in window)) return;
    try {
      speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(text.slice(0, 400));
      u.rate = 1.05;
      speechSynthesis.speak(u);
    } catch (e) { /* TTS unavailable — stay silent */ }
  }

  /* ------------------------------------------------ chat */
  var busy = false;
  function send(text) {
    text = (text || "").trim();
    if (!text || busy) return;
    busy = true;
    spike();
    addMsg(text, "user");
    input.value = "";
    waveLabel.textContent = "PROCESSING";
    waveLabel.classList.add("live");

    fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: text })
    })
      .then(function (r) { return r.json().then(function (j) { return { status: r.status, body: j }; }); })
      .then(function (res) {
        var b = res.body || {};
        var reply = b.response || (b.error && b.error.message) || "No response.";
        var div = addMsg(reply, "jarvis", b.skill);
        if (b.ok === false && !b.skill) div.classList.add("typing-err");
        speak(reply);
      })
      .catch(function () {
        addMsg("Link to the core is down. Is the server running?", "jarvis", "error")
          .classList.add("typing-err");
      })
      .finally(function () {
        busy = false;
        waveLabel.textContent = "LISTENING";
        waveLabel.classList.remove("live");
        input.focus();
      });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    send(input.value);
  });

  /* ------------------------------------------------ mic (Web Speech API) */
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  var rec = null;
  if (SR) {
    rec = new SR();
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.onresult = function (e) {
      var said = e.results[0][0].transcript;
      input.value = said;
      send(said);
    };
    rec.onend = function () { micBtn.classList.remove("rec"); };
    rec.onerror = function () { micBtn.classList.remove("rec"); };
    micBtn.addEventListener("click", function () {
      try {
        if (micBtn.classList.contains("rec")) { rec.stop(); return; }
        micBtn.classList.add("rec");
        rec.start();
      } catch (e) { micBtn.classList.remove("rec"); }
    });
  } else {
    micBtn.style.opacity = "0.35";
    micBtn.title = "Voice input not supported in this browser";
    micBtn.addEventListener("click", function () {
      addMsg("Voice input isn't supported in this browser — type instead.", "jarvis", "system");
    });
  }

  /* ------------------------------------------------ boot: status + skills */
  function boot() {
    fetch("/health").then(function (r) { return r.json(); }).then(function (h) {
      statusLine.innerHTML = '<span class="dot"></span> online · v' + (h.version || "?");
      var c = document.createElement("span");
      c.className = "chip on"; c.textContent = "online";
      chips.appendChild(c);
      var k = document.createElement("span");
      k.className = "chip on"; k.textContent = "keyless";
      chips.appendChild(k);
    }).catch(function () {
      statusLine.innerHTML = '<span class="dot" style="background:#ff5470;box-shadow:0 0 10px #ff5470"></span> offline';
    });

    fetch("/skills").then(function (r) { return r.json(); }).then(function (d) {
      (d.skills || []).forEach(function (s) {
        if (!s.examples || !s.examples.length) return;
        var b = document.createElement("button");
        b.type = "button";
        b.className = "hint";
        b.textContent = s.examples[0];
        b.addEventListener("click", function () { send(s.examples[0]); });
        hintsBox.appendChild(b);
      });
      addMsg("Systems online. All skills running local — no keys, no cloud calls. Try a command below, or speak.", "jarvis", "boot");
    }).catch(function () {
      addMsg("Core unreachable — check the server.", "jarvis", "error");
    });
  }

  boot();
})();
