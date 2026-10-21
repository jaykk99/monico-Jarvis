/* Jarvis console: chat, voice wave, mic with honest capability detection, TTS. */
(function () {
  "use strict";

  var log = document.getElementById("log");
  var form = document.getElementById("composer");
  var input = document.getElementById("input");
  var micBtn = document.getElementById("mic");
  var voiceNote = document.getElementById("voice-note");
  var ttsBox = document.getElementById("tts");
  var statusText = document.getElementById("status-text");
  var sideStatus = document.getElementById("side-status");
  var topbarDot = document.getElementById("topbar-dot");
  var topbarStatus = document.getElementById("topbar-status");
  var chips = document.getElementById("chips");
  var hintsBox = document.getElementById("hints");
  var skillGrid = document.getElementById("skill-grid");
  var waveLabel = document.getElementById("wave-label");
  var sidebar = document.getElementById("sidebar");
  var scrim = document.getElementById("side-scrim");

  /* ------------------------------------------------ sidebar (mobile drawer) */
  function openSide() { sidebar.classList.add("open"); scrim.classList.add("open"); }
  function closeSide() { sidebar.classList.remove("open"); scrim.classList.remove("open"); }
  document.getElementById("menu-btn").addEventListener("click", openSide);
  document.getElementById("side-close").addEventListener("click", closeSide);
  scrim.addEventListener("click", closeSide);
  document.getElementById("help-btn").addEventListener("click", function () { send("help"); });

  /* ------------------------------------------------ voice wave canvas */
  var canvas = document.getElementById("wave");
  var ctx = canvas.getContext("2d");
  var energy = 0.25, targetEnergy = 0.25, t = 0;

  function sizeCanvas() {
    var r = canvas.getBoundingClientRect();
    var dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(300, r.width * dpr);
    canvas.height = 84 * dpr;
  }
  window.addEventListener("resize", sizeCanvas);
  sizeCanvas();

  function drawWave() {
    t += 0.045;
    energy += (targetEnergy - energy) * 0.06;
    var w = canvas.width, h = canvas.height, mid = h / 2;
    var dpr = window.devicePixelRatio || 1;
    ctx.clearRect(0, 0, w, h);
    ctx.lineWidth = 2 * dpr;
    for (var pass = 0; pass < 3; pass++) {
      var amp = (h * 0.38 * energy) / (pass + 1);
      ctx.strokeStyle = pass === 0
        ? "rgba(34,211,238,.9)"
        : "rgba(34,211,238," + (0.35 - pass * 0.12) + ")";
      ctx.beginPath();
      for (var x = 0; x <= w; x += 4) {
        var y = mid
          + Math.sin(x * 0.012 + t * (1.6 + pass * 0.4)) * amp
          + Math.sin(x * 0.03 - t * 2.2) * amp * 0.4;
        if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
    requestAnimationFrame(drawWave);
  }
  drawWave();

  function spike() { targetEnergy = 1; setTimeout(function () { targetEnergy = 0.25; }, 900); }

  /* ------------------------------------------------ messages */
  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function rich(text) {
    // light markdown: `code` and **bold**
    var h = esc(text);
    h = h.replace(/`([^`]+)`/g, "<code>$1</code>");
    h = h.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    return h;
  }

  function addMsg(text, who, skill, meta) {
    var div = document.createElement("div");
    div.className = "msg " + who;
    div.dataset.plain = text; // raw text for chat export
    div.dataset.when = new Date().toISOString();
    if (who === "jarvis") {
      var tag = document.createElement("span");
      tag.className = "skill-tag";
      tag.textContent = "jarvis" + (skill ? " · " + skill : "") + (meta ? " · " + meta : "");
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
    var html = rich(text);
    (function tick() {
      if (i < text.length) {
        // type plain, then swap to rich html at the end (keeps markup safe)
        el.textContent = text.slice(0, i + 2);
        el.appendChild(cursor);
        i += 2;
        setTimeout(tick, 7);
      } else {
        el.innerHTML = html;
      }
    })();
  }

  function speak(text) {
    if (!ttsBox.checked || !("speechSynthesis" in window)) return;
    try {
      speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(text.replace(/[*`]/g, "").slice(0, 400));
      u.rate = 1.05;
      var pick = ttsVoice.value;
      if (pick) {
        var v = speechSynthesis.getVoices().filter(function (vv) { return vv.name === pick; })[0];
        if (v) u.voice = v;
      }
      speechSynthesis.speak(u);
    } catch (e) { /* TTS unavailable — stay silent */ }
  }

  /* TTS voice picker: populated from the browser's voice list, persisted. */
  var ttsVoice = document.getElementById("tts-voice");
  function fillVoices() {
    if (!("speechSynthesis" in window)) return;
    var voices = speechSynthesis.getVoices();
    if (!voices.length) return;
    ttsVoice.innerHTML = "";
    voices.forEach(function (v) {
      var o = document.createElement("option");
      o.value = v.name;
      o.textContent = v.name + (v.lang ? " (" + v.lang + ")" : "");
      ttsVoice.appendChild(o);
    });
    var saved = null;
    try { saved = localStorage.getItem("jarvis-tts-voice"); } catch (e) {}
    if (saved) ttsVoice.value = saved;
    ttsVoice.hidden = false;
  }
  if ("speechSynthesis" in window) {
    fillVoices();
    speechSynthesis.onvoiceschanged = fillVoices;
    ttsVoice.addEventListener("change", function () {
      try { localStorage.setItem("jarvis-tts-voice", ttsVoice.value); } catch (e) {}
    });
  }

  /* ------------------------------------------------ command history */
  var history = [];
  try { history = JSON.parse(localStorage.getItem("jarvis-history") || "[]"); } catch (e) { history = []; }
  var histIdx = -1;

  function pushHistory(text) {
    if (history[history.length - 1] === text) return;
    history.push(text);
    if (history.length > 100) history = history.slice(-100);
    try { localStorage.setItem("jarvis-history", JSON.stringify(history)); } catch (e) {}
    histIdx = -1;
  }

  input.addEventListener("keydown", function (e) {
    if (e.key !== "ArrowUp" && e.key !== "ArrowDown") return;
    if (!history.length) return;
    e.preventDefault();
    if (e.key === "ArrowUp") {
      histIdx = histIdx < 0 ? history.length - 1 : Math.max(0, histIdx - 1);
    } else {
      histIdx = histIdx < 0 ? -1 : histIdx + 1;
      if (histIdx >= history.length) histIdx = -1;
    }
    input.value = histIdx < 0 ? "" : history[histIdx];
  });

  /* ------------------------------------------------ chat */
  var busy = false;
  function send(text) {
    text = (text || "").trim();
    if (!text || busy) return;
    busy = true;
    spike();
    pushHistory(text);
    addMsg(text, "user");
    input.value = "";
    setWave("PROCESSING", true);
    var t0 = performance.now();

    fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: text })
    })
      .then(function (r) { return r.json().then(function (j) { return { status: r.status, body: j }; }); })
      .then(function (res) {
        var ms = Math.round(performance.now() - t0);
        var b = res.body || {};
        var reply = b.response || (b.error && b.error.message) || "No response.";
        var div = addMsg(reply, "jarvis", b.skill, ms + "ms");
        if (b.ok === false && !b.skill) div.classList.add("typing-err");
        speak(reply);
      })
      .catch(function () {
        addMsg("Link to the core is down. Is the server running?", "jarvis", "error")
          .classList.add("typing-err");
      })
      .finally(function () {
        busy = false;
        setWave("READY", false);
        input.focus();
      });
  }

  function setWave(label, live) {
    waveLabel.textContent = label;
    waveLabel.classList.toggle("live", !!live);
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    send(input.value);
  });

  /* ------------------------------------------------ voice input: honest capability detection */
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  var rec = null;
  var listening = false;

  function showVoiceNote(html) {
    voiceNote.innerHTML = html;
    voiceNote.hidden = false;
  }
  function hideVoiceNote() { voiceNote.hidden = true; }

  function voiceWhyNot() {
    // Explain precisely why voice transcription is unavailable.
    var reasons = [];
    if (!SR) {
      reasons.push("this browser has no speech-recognition engine (Web Speech API missing)");
    }
    if (!window.isSecureContext) {
      reasons.push("the page isn't on HTTPS or localhost — browsers block mic access on plain HTTP");
    }
    if (location.protocol === "http:" && location.hostname !== "localhost" && location.hostname !== "127.0.0.1") {
      reasons.push("you're on plain HTTP — serve over HTTPS or use localhost");
    }
    var ua = navigator.userAgent;
    if (/iPhone|iPad|iPod/.test(ua) && !/CriOS|FxiOS/.test(ua)) {
      reasons.push("iOS Safari only supports it in limited contexts");
    }
    if (!reasons.length) reasons.push("unknown — the browser refused to start recognition");
    return reasons;
  }

  var VOICE_ERRORS = {
    "not-allowed": "Mic blocked — allow microphone access in the browser prompt, then tap the mic again.",
    "service-not-allowed": "Mic blocked — allow microphone access, then try again.",
    "no-speech": "Didn't hear anything — try again, a bit louder.",
    "audio-capture": "No microphone found on this device.",
    "network": "Speech service unreachable — check your connection and try again.",
    "aborted": "Listening stopped.",
    "language-not-supported": "This language isn't supported by the recognizer."
  };

  function setMicState(state, title) {
    micBtn.classList.toggle("rec", state === "rec");
    micBtn.classList.toggle("unsupported", state === "unsupported");
    if (title) micBtn.title = title;
  }

  if (SR) {
    try {
      rec = new SR();
      rec.lang = "en-US";
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      rec.onresult = function (e) {
        var said = e.results[0][0].transcript;
        hideVoiceNote();
        input.value = said;
        send(said);
      };
      rec.onend = function () {
        listening = false;
        setMicState("idle", "Voice input — tap to speak");
        setWave("READY", false);
      };
      rec.onerror = function (e) {
        listening = false;
        setMicState("idle", "Voice input — tap to speak");
        setWave("READY", false);
        var msg = VOICE_ERRORS[e.error] || ("Voice error: " + e.error + " — type instead.");
        if (e.error === "not-allowed" || e.error === "service-not-allowed" || e.error === "audio-capture") {
          showVoiceNote("<strong>Voice input blocked.</strong> " + msg);
        } else if (e.error !== "aborted" && e.error !== "no-speech") {
          showVoiceNote(msg);
        }
      };
      micBtn.addEventListener("click", function () {
        hideVoiceNote();
        try {
          if (listening) { rec.stop(); return; }
          if (!window.isSecureContext) {
            showVoiceNote("<strong>Voice needs a secure page.</strong> Browsers block the mic on plain HTTP — use HTTPS or localhost, or just type.");
            return;
          }
          listening = true;
          setMicState("rec", "Listening — tap to stop");
          setWave("LISTENING", true);
          rec.start();
        } catch (e) {
          listening = false;
          setMicState("idle", "Voice input — tap to speak");
          showVoiceNote("<strong>Couldn't start listening.</strong> " + (e.message || "Type instead."));
        }
      });
      setMicState("idle", "Voice input — tap to speak");
    } catch (e) {
      voiceUnsupported("setup failed: " + e.message);
    }
  } else {
    voiceUnsupported();
  }

  function voiceUnsupported(extra) {
    setMicState("unsupported", "Voice transcription unavailable — tap for details");
    micBtn.addEventListener("click", function () {
      var reasons = voiceWhyNot();
      if (extra) reasons.push(extra);
      showVoiceNote(
        "<strong>Voice transcription isn't available here.</strong><br>" +
        reasons.map(function (r) { return "• " + r; }).join("<br>") +
        "<br>Typing works everywhere — go ahead."
      );
    });
  }

  /* ------------------------------------------------ boot: status + skills */
  function setStatus(online, text) {
    statusText.textContent = text;
    topbarStatus.textContent = online ? "Jarvis · online" : "Jarvis · offline";
    var dot = sideStatus.querySelector(".dot");
    if (dot) dot.classList.toggle("off", !online);
    topbarDot.classList.toggle("off", !online);
  }

  function boot() {
    fetch("/health").then(function (r) { return r.json(); }).then(function (h) {
      setStatus(true, "online · v" + (h.version || "?"));
      [["online", 1], ["keyless", 1], ["local", 1]].forEach(function (c) {
        var s = document.createElement("span");
        s.className = "chip on"; s.textContent = c[0];
        chips.appendChild(s);
      });
    }).catch(function () {
      setStatus(false, "offline — server down?");
    });

    fetch("/skills").then(function (r) { return r.json(); }).then(function (d) {
      var skills = d.skills || [];
      // sidebar grid
      skills.forEach(function (s) {
        var card = document.createElement("button");
        card.type = "button";
        card.className = "skill-card";
        var nm = document.createElement("span");
        nm.className = "sk-name"; nm.textContent = s.name;
        var ds = document.createElement("span");
        ds.className = "sk-desc"; ds.textContent = s.description;
        card.appendChild(nm); card.appendChild(ds);
        card.title = s.usage;
        card.addEventListener("click", function () {
          closeSide();
          if (s.examples && s.examples.length) send(s.examples[0]);
          else { input.value = s.name + " "; input.focus(); }
        });
        skillGrid.appendChild(card);
      });
      // hint chips under the log
      skills.forEach(function (s) {
        if (!s.examples || !s.examples.length) return;
        var b = document.createElement("button");
        b.type = "button";
        b.className = "hint";
        b.textContent = s.examples[0];
        b.addEventListener("click", function () { send(s.examples[0]); });
        hintsBox.appendChild(b);
      });
      addMsg(
        "Systems online. Every skill runs on this box — no keys, no cloud calls.\n" +
        "Tap a skill on the left or type `help` for the full list.",
        "jarvis", "boot"
      );
    }).catch(function () {
      addMsg("Core unreachable — check the server.", "jarvis", "error");
    });
  }

  /* ------------------------------------------------ theme (dark/light) */
  var themeBtn = document.getElementById("theme-btn");
  function applyTheme(name) {
    document.documentElement.dataset.theme = name;
    try { localStorage.setItem("jarvis-theme", name); } catch (e) {}
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = name === "light" ? "#f4f6fa" : "#08090d";
  }
  (function initTheme() {
    var saved = null;
    try { saved = localStorage.getItem("jarvis-theme"); } catch (e) {}
    applyTheme(saved === "light" ? "light" : "dark");
  })();
  themeBtn.addEventListener("click", function () {
    applyTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light");
  });

  /* ------------------------------------------------ export + clear chat */
  document.getElementById("export-btn").addEventListener("click", function () {
    var lines = [];
    Array.prototype.forEach.call(log.children, function (div) {
      var when = div.dataset.when ? new Date(div.dataset.when).toLocaleString() : "";
      var who = div.classList.contains("user") ? "you" : "jarvis";
      lines.push("[" + when + "] " + who + ": " + (div.dataset.plain || div.textContent));
    });
    var blob = new Blob([lines.join("\n\n") + "\n"], { type: "text/plain" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "jarvis-chat-" + new Date().toISOString().slice(0, 10) + ".txt";
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  });

  document.getElementById("clear-btn").addEventListener("click", function () {
    log.innerHTML = "";
    addMsg("Chat cleared. What next?", "jarvis", "console");
  });

  /* ------------------------------------------------ skill search filter */
  var skillSearch = document.getElementById("skill-search");
  skillSearch.addEventListener("input", function () {
    var q = skillSearch.value.trim().toLowerCase();
    Array.prototype.forEach.call(skillGrid.children, function (card) {
      var hay = (card.textContent || "").toLowerCase();
      card.style.display = !q || hay.indexOf(q) !== -1 ? "" : "none";
    });
  });

  boot();
})();
