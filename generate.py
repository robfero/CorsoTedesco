#!/usr/bin/env python3
"""Generatore del sito statico "Tedesco in 60 giorni".

Legge ``course.json`` (la fonte di verità) e scrive i 67 file HTML:
- index.html
- tedesco-fase-1.html … tedesco-fase-6.html
- tedesco-giorno-01.html … tedesco-giorno-60.html

Solo HTML/CSS/JS vanilla, ogni pagina è autosufficiente (CSS e JS inline).
Rigenerazione idempotente:  python3 generate.py
"""

import html
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# --- Palette base condivisa (design system) -------------------------------
PALETTE = {
    "paper": "#FBFAF6",
    "ink": "#16151A",
    "muted": "#6A6873",
    "line": "#E7E4DC",
    "card": "#FFFFFF",
    "ok": "#1F8A4C",
    "no": "#C2392F",
}

FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;900&'
    'family=Inter:wght@400;600&display=swap" rel="stylesheet">'
)


def esc(text):
    """Escape HTML-safe."""
    return html.escape(str(text), quote=True)


def day_file(n):
    return f"tedesco-giorno-{n:02d}.html"


def phase_file(n):
    return f"tedesco-fase-{n}.html"


def phase_of_day(n):
    """Mappa giorno globale (1..60) → numero di fase (1..6)."""
    return (n - 1) // 10 + 1


# --- Audio: sintesi vocale tedesca (Web Speech API) ------------------------
# Nessuna dipendenza, nessun file: il browser legge il testo in tedesco.
# I pulsanti spariscono se il browser non supporta la sintesi vocale.
TTS_SCRIPT = """
<script>
(function () {
  var synth = window.speechSynthesis;
  var audioEls = document.querySelectorAll('[data-speak], [data-speak-all], [data-tts-speed], [data-tts-voice]');
  if (!synth) { audioEls.forEach(function (b) { b.remove(); }); return; }

  // --- Stato (persistito nell'URL, senza localStorage) -------------------
  var params = new URLSearchParams(location.search);
  var pRate = parseFloat(params.get('rate'));
  var rate = (!isNaN(pRate) && pRate > 0) ? pRate : 0.95;   // "Normale"
  var wantVoice = params.get('voice') || '';
  var voice = null;

  var FEM = /anna|petra|katja|viktoria|marlene|hedda|vicki|conchita|paulina|sabina|female|frau|weiblich/i;
  var MAS = /markus|yannick|stefan|hans|conrad|viktor|male|mann|männlich/i;
  function genderLabel(v) {
    if (FEM.test(v.name)) return ' (f)';
    if (MAS.test(v.name)) return ' (m)';
    return '';
  }
  function germanVoices() {
    return (synth.getVoices() || []).filter(function (v) {
      return v.lang && v.lang.toLowerCase().indexOf('de') === 0;
    });
  }
  function pickVoice() {
    var vs = germanVoices();
    voice = (wantVoice && vs.filter(function (v) { return v.name === wantVoice; })[0])
         || vs.filter(function (v) { return v.lang === 'de-DE'; })[0]
         || vs[0] || null;
  }

  function clearSpeaking() {
    document.querySelectorAll('.speak.speaking').forEach(function (b) { b.classList.remove('speaking'); });
  }
  function utter(text) {
    var u = new SpeechSynthesisUtterance(text);
    u.lang = 'de-DE'; u.rate = rate;
    if (voice) u.voice = voice;
    return u;
  }
  // iOS/Safari: la sintesi può auto-mettersi in pausa → forziamo il resume.
  function kick() { try { if (synth.paused) synth.resume(); } catch (e) {} }
  // iOS richiede un primo speak dentro un gesto utente per "sbloccare" l'audio.
  var primed = false;
  function prime() {
    if (primed) return; primed = true;
    try {
      var u = new SpeechSynthesisUtterance(' ');
      u.volume = 0; u.lang = 'de-DE';
      synth.speak(u); kick();
    } catch (e) {}
    // iOS espone spesso l'elenco completo delle voci solo dopo il primo gesto.
    refreshVoices(); setTimeout(refreshVoices, 400);
  }

  function speakOne(text, btn) {
    synth.cancel(); clearSpeaking();
    var u = utter(text);
    if (btn) {
      btn.classList.add('speaking');
      u.onend = u.onerror = function () { btn.classList.remove('speaking'); };
    }
    synth.speak(u); kick();
  }
  // Riproduzione in catena (più affidabile di una coda lunga su iOS).
  function speakMany(list) {
    synth.cancel(); clearSpeaking();
    var i = 0;
    (function next() {
      if (i >= list.length) return;
      var u = utter(list[i++]);
      u.onend = next;
      synth.speak(u); kick();
    })();
  }

  // --- Controlli UI ------------------------------------------------------
  function buildSpeedControls() {
    document.querySelectorAll('[data-tts-speed]').forEach(function (h) {
      h.innerHTML = '<span>Velocità</span><span class="seg">'
        + '<button type="button" data-rate="0.95">Normale</button>'
        + '<button type="button" data-rate="0.6">Lenta 🐢</button></span>';
    });
    markRate();
  }
  function markRate() {
    document.querySelectorAll('[data-tts-speed] button').forEach(function (b) {
      b.classList.toggle('active', parseFloat(b.getAttribute('data-rate')) === rate);
    });
  }
  function buildVoiceControls() {
    var vs = germanVoices();
    document.querySelectorAll('[data-tts-voice]').forEach(function (h) {
      h.innerHTML = '';
      h.style.display = '';
      var label = document.createElement('span'); label.textContent = 'Voce';
      label.title = vs.length + ' voci tedesche disponibili nel browser';
      h.appendChild(label);
      if (vs.length >= 2) {
        // Più voci: menu di scelta.
        var sel = document.createElement('select'); sel.className = 'tts-voice-select';
        vs.forEach(function (v) {
          var o = document.createElement('option');
          o.value = v.name; o.textContent = v.name + genderLabel(v);
          if (voice && v.name === voice.name) o.selected = true;
          sel.appendChild(o);
        });
        h.appendChild(sel);
      } else {
        // Una sola (o nessuna) voce esposta dal browser: mostra solo il nome.
        var name = document.createElement('strong'); name.className = 'tts-voice-name';
        name.textContent = voice ? (voice.name + genderLabel(voice)) : 'predefinita di sistema';
        h.appendChild(name);
      }
    });
  }

  // --- Persistenza: aggiorna URL e link interni --------------------------
  function query() {
    var p = new URLSearchParams();
    p.set('rate', String(rate));
    if (wantVoice) p.set('voice', wantVoice);
    return '?' + p.toString();
  }
  function syncLinks() {
    var q = query();
    document.querySelectorAll('a[href]').forEach(function (a) {
      var href = a.getAttribute('href');
      if (!href || /^(https?:|mailto:|#)/.test(href)) return;
      var base = href.split('#')[0].split('?')[0];
      if (!/\\.html$/.test(base)) return;
      var hash = href.indexOf('#') >= 0 ? href.slice(href.indexOf('#')) : '';
      a.setAttribute('href', base + q + hash);
    });
  }
  function syncState() {
    try { history.replaceState(null, '', location.pathname + query() + location.hash); } catch (e) {}
    syncLinks();
  }

  function setRate(r) { rate = r; markRate(); syncState(); }
  function setVoice(name) { wantVoice = name; pickVoice(); buildVoiceControls(); syncState(); }

  // --- Eventi ------------------------------------------------------------
  document.addEventListener('click', function (e) {
    var sp = e.target.closest('[data-tts-speed] [data-rate]');
    if (sp) { e.preventDefault(); setRate(parseFloat(sp.getAttribute('data-rate'))); return; }
    var one = e.target.closest('[data-speak]');
    if (one) { e.preventDefault(); speakOne(one.getAttribute('data-speak'), one); return; }
    var all = e.target.closest('[data-speak-all]');
    if (all) {
      e.preventDefault();
      try { speakMany(JSON.parse(all.getAttribute('data-speak-all'))); } catch (err) {}
    }
  });
  document.addEventListener('change', function (e) {
    var s = e.target.closest('.tts-voice-select');
    if (s) setVoice(s.value);
  });
  // Sblocco audio iOS al primo gesto, e resume periodico contro l'auto-pausa.
  ['touchstart', 'pointerdown'].forEach(function (ev) {
    document.addEventListener(ev, prime, { once: true, passive: true });
  });
  setInterval(function () { if (synth.speaking) kick(); }, 5000);
  window.addEventListener('beforeunload', function () { synth.cancel(); });

  // --- Avvio -------------------------------------------------------------
  function refreshVoices() { pickVoice(); buildVoiceControls(); syncLinks(); }

  // iOS: onvoiceschanged è inaffidabile → riprovo la lista più volte.
  var voiceTries = 0;
  (function pollVoices() {
    refreshVoices();
    voiceTries++;
    if (voiceTries < 25 && germanVoices().length < 2) setTimeout(pollVoices, 300);
  })();

  buildSpeedControls();
  if (typeof synth.onvoiceschanged !== 'undefined') {
    synth.onvoiceschanged = refreshVoices;
  }
})();
</script>
"""


def speak_btn(text):
    """Pulsante 🔊 per leggere una singola frase tedesca."""
    return (f'<button type="button" class="speak" data-speak="{esc(text)}"'
            f' aria-label="Ascolta in tedesco" title="Ascolta">🔊</button>')


def speak_all_btn(de_list, label="🔊 Ascolta tutto"):
    """Pulsante che legge in sequenza più frasi tedesche."""
    data = esc(json.dumps(de_list, ensure_ascii=False))
    return (f'<button type="button" class="btn ghost btn-speak-all" data-speak-all="{data}"'
            f' aria-label="Ascolta gli esempi in tedesco">{label}</button>')


# --- CSS condiviso ---------------------------------------------------------
def base_css(accent="#D7263D"):
    p = PALETTE
    return f"""
:root {{
  --paper: {p['paper']};
  --ink: {p['ink']};
  --muted: {p['muted']};
  --line: {p['line']};
  --card: {p['card']};
  --ok: {p['ok']};
  --no: {p['no']};
  --accent: {accent};
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-weight: 400;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}
h1, h2, h3, .display {{
  font-family: "Archivo", "Arial Black", Impact, system-ui, sans-serif;
  font-weight: 900;
  line-height: 1.1;
  letter-spacing: -0.01em;
}}
a {{ color: inherit; }}
.wrap {{ width: min(960px, 92vw); margin-inline: auto; }}
.eyebrow {{
  font-family: "Archivo", system-ui, sans-serif;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.78rem;
  color: var(--accent);
}}

/* Header sticky */
.site-header {{
  position: sticky; top: 0; z-index: 50;
  background: color-mix(in srgb, var(--paper) 88%, transparent);
  backdrop-filter: saturate(140%) blur(8px);
  border-bottom: 1px solid var(--line);
}}
.header-inner {{
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; padding: 12px 0; flex-wrap: wrap;
}}
.brand {{
  font-family: "Archivo", system-ui, sans-serif; font-weight: 900;
  font-size: 1rem; text-decoration: none; color: var(--ink);
  display: inline-flex; align-items: center; gap: 8px;
}}
.brand .dot {{ width: 14px; height: 14px; border-radius: 50%; background: var(--accent); display: inline-block; }}
.header-link {{
  text-decoration: none; font-weight: 600; font-size: 0.9rem;
  color: var(--ink); padding: 6px 12px; border: 1px solid var(--line);
  border-radius: 999px; background: var(--card);
}}
.header-link:hover {{ border-color: var(--accent); color: var(--accent); }}

/* Pallini fasi */
.dots {{ display: flex; gap: 8px; align-items: center; }}
.dots a {{
  width: 30px; height: 30px; border-radius: 50%;
  display: grid; place-items: center;
  font-family: "Archivo", system-ui, sans-serif; font-weight: 700; font-size: 0.85rem;
  text-decoration: none; border: 2px solid var(--line); color: var(--muted);
  background: var(--card); transition: transform .12s ease;
}}
.dots a:hover {{ transform: translateY(-2px); }}
.dots a.active {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
.dots a[data-accent] {{ border-color: var(--line); }}

/* Hero */
.hero {{ position: relative; padding: 56px 0 36px; overflow: hidden; }}
.hero .bignum {{
  position: absolute; right: -2vw; top: -2vw; font-family: "Archivo", system-ui, sans-serif;
  font-weight: 900; font-size: clamp(140px, 34vw, 360px); line-height: 0.8;
  color: var(--accent); opacity: 0.10; pointer-events: none; user-select: none; z-index: 0;
}}
.hero > * {{ position: relative; z-index: 1; }}
.hero h1 {{ font-size: clamp(2rem, 6vw, 3.4rem); margin: 10px 0 12px; }}
.hero .subtitle {{ font-size: clamp(1.05rem, 2.4vw, 1.3rem); color: var(--muted); max-width: 46ch; }}

/* Chips */
.chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }}
.chip {{
  font-size: 0.82rem; font-weight: 600; padding: 6px 12px; border-radius: 999px;
  background: color-mix(in srgb, var(--accent) 10%, var(--card));
  border: 1px solid color-mix(in srgb, var(--accent) 30%, var(--line));
  color: color-mix(in srgb, var(--accent) 75%, var(--ink));
}}

/* Progress bar */
.progress {{ margin: 8px 0 0; }}
.progress .bar {{ height: 8px; border-radius: 999px; background: var(--line); overflow: hidden; }}
.progress .bar > span {{ display: block; height: 100%; background: var(--accent); border-radius: 999px; }}
.progress .label {{ font-size: 0.8rem; color: var(--muted); margin-top: 6px; font-weight: 600; }}

/* Cards giorno */
.day-list {{ display: grid; gap: 16px; padding: 8px 0 24px; }}
.day-card {{
  background: var(--card); border: 1px solid var(--line); border-radius: 16px;
  padding: 20px; display: grid; grid-template-columns: 56px 1fr; gap: 18px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03); transition: border-color .15s ease, transform .15s ease;
}}
.day-card:hover {{ border-color: var(--accent); transform: translateY(-2px); }}
.day-card .marker {{
  width: 56px; height: 56px; border-radius: 14px;
  background: color-mix(in srgb, var(--accent) 12%, var(--card));
  color: var(--accent); display: grid; place-items: center;
  font-family: "Archivo", system-ui, sans-serif; font-weight: 900; font-size: 1.4rem;
}}
.day-card h3 {{ margin: 0 0 6px; font-size: 1.15rem; }}
.day-card .lead {{ color: var(--muted); margin: 0 0 10px; }}
.day-card .task {{
  font-size: 0.92rem; margin: 0 0 14px;
  padding: 8px 12px; border-left: 3px solid var(--accent);
  background: color-mix(in srgb, var(--accent) 6%, var(--card)); border-radius: 0 8px 8px 0;
}}
.day-card .task b {{ color: var(--accent); }}

/* Buttons */
.btn {{
  display: inline-flex; align-items: center; gap: 8px;
  text-decoration: none; font-weight: 600; font-size: 0.95rem;
  padding: 10px 16px; border-radius: 10px; border: 1px solid var(--accent);
  background: var(--accent); color: #fff; transition: opacity .15s ease, transform .15s ease;
}}
.btn:hover {{ opacity: 0.92; transform: translateY(-1px); }}
.btn.ghost {{ background: var(--card); color: var(--ink); border-color: var(--line); }}
.btn.ghost:hover {{ border-color: var(--accent); color: var(--accent); }}

/* Pulsanti audio (Web Speech API) */
.speak {{
  cursor: pointer; font: inherit; line-height: 1.2; vertical-align: middle;
  border: 1px solid var(--line); background: var(--card); color: var(--accent);
  border-radius: 8px; padding: 2px 8px; font-size: 0.9rem; margin-left: 6px;
  transition: background .12s ease, border-color .12s ease;
}}
.speak:hover {{ border-color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, var(--card)); }}
.speak.speaking {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
.btn-speak-all {{ font-size: 0.88rem; padding: 7px 13px; }}
.ex-head {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }}
.ex-actions {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
.day-card .card-actions {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
.tts-speed {{ display: inline-flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--muted); }}
.tts-speed .seg {{ display: inline-flex; border: 1px solid var(--line); border-radius: 999px; overflow: hidden; }}
.tts-speed button {{ font: inherit; cursor: pointer; border: 0; background: var(--card); color: var(--ink); padding: 5px 13px; }}
.tts-speed button + button {{ border-left: 1px solid var(--line); }}
.tts-speed button.active {{ background: var(--accent); color: #fff; }}
.tts-bar {{ display: inline-flex; align-items: center; gap: 14px; flex-wrap: wrap; }}
.tts-voice {{ display: inline-flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--muted); }}
.tts-voice select {{ font: inherit; padding: 5px 10px; border: 1px solid var(--line); border-radius: 999px; background: var(--card); color: var(--ink); cursor: pointer; max-width: 220px; }}
.tts-voice .tts-voice-name {{ color: var(--ink); font-weight: 600; }}

/* Content blocks (pagina giorno) */
.section {{ padding: 8px 0; }}
.section h2 {{ font-size: 1.5rem; margin: 28px 0 12px; display: flex; align-items: center; gap: 10px; }}
.section h2 .num {{
  width: 32px; height: 32px; border-radius: 9px; background: var(--accent); color: #fff;
  display: grid; place-items: center; font-size: 0.95rem;
}}
.prose p {{ font-size: 1.05rem; }}
.prose ul {{ padding-left: 1.2em; }}
.prose li {{ margin: 6px 0; }}

table.ex {{
  width: 100%; border-collapse: collapse; background: var(--card);
  border: 1px solid var(--line); border-radius: 12px; overflow: hidden; margin: 8px 0;
}}
table.ex caption {{ caption-side: top; text-align: left; font-weight: 600; color: var(--muted); padding: 4px 2px 10px; }}
table.ex th {{
  text-align: left; font-family: "Archivo", system-ui, sans-serif; font-size: 0.78rem;
  text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted);
  padding: 10px 14px; border-bottom: 2px solid var(--line); background: color-mix(in srgb, var(--accent) 5%, var(--card));
}}
table.ex td {{ padding: 11px 14px; border-bottom: 1px solid var(--line); vertical-align: top; }}
table.ex tr:last-child td {{ border-bottom: none; }}
table.ex td.de {{ font-weight: 600; color: var(--ink); }}
table.ex td.it {{ color: var(--muted); }}

.callout {{
  border-radius: 14px; padding: 18px 20px; margin: 16px 0;
  background: color-mix(in srgb, var(--accent) 8%, var(--card));
  border: 1px solid color-mix(in srgb, var(--accent) 28%, var(--line));
}}
.callout h3 {{ margin: 0 0 6px; font-size: 1.05rem; color: var(--accent); }}
.callout p {{ margin: 0; }}

.exercise {{
  border-radius: 14px; padding: 18px 20px; margin: 16px 0;
  background: var(--card); border: 1px dashed color-mix(in srgb, var(--accent) 45%, var(--line));
}}
.exercise h3 {{ margin: 0 0 8px; font-size: 1.05rem; }}
.exercise details {{ margin-top: 10px; }}
.exercise summary {{
  cursor: pointer; font-weight: 600; color: var(--accent);
  padding: 8px 12px; border-radius: 8px; background: color-mix(in srgb, var(--accent) 8%, var(--card));
  display: inline-block; list-style: none;
}}
.exercise summary::-webkit-details-marker {{ display: none; }}
.exercise summary::before {{ content: "▸ "; }}
.exercise details[open] summary::before {{ content: "▾ "; }}
.exercise .solution {{ margin-top: 12px; padding: 12px 14px; border-left: 3px solid var(--ok); background: color-mix(in srgb, var(--ok) 6%, var(--card)); border-radius: 0 8px 8px 0; }}

/* Quiz */
.quiz {{ margin: 8px 0 8px; }}
.quiz .qcard {{
  background: var(--card); border: 1px solid var(--line); border-radius: 14px;
  padding: 18px 20px; margin: 14px 0;
}}
.quiz .qcard p.q {{ font-weight: 600; font-size: 1.05rem; margin: 0 0 12px; }}
.quiz .qcard p.q .qn {{ color: var(--accent); font-family: "Archivo", system-ui, sans-serif; }}
.quiz .opts {{ display: grid; gap: 8px; }}
.quiz button.opt {{
  text-align: left; font: inherit; cursor: pointer; width: 100%;
  padding: 11px 14px; border-radius: 10px; border: 1px solid var(--line);
  background: var(--paper); color: var(--ink); transition: border-color .12s ease, background .12s ease;
}}
.quiz button.opt:hover:not(:disabled) {{ border-color: var(--accent); }}
.quiz button.opt:disabled {{ cursor: default; }}
.quiz button.opt.correct {{ border-color: var(--ok); background: color-mix(in srgb, var(--ok) 14%, var(--card)); color: var(--ok); font-weight: 600; }}
.quiz button.opt.wrong {{ border-color: var(--no); background: color-mix(in srgb, var(--no) 12%, var(--card)); color: var(--no); }}
.quiz .why {{
  margin-top: 10px; font-size: 0.92rem; color: var(--muted);
  padding: 8px 12px; border-left: 3px solid var(--accent); border-radius: 0 8px 8px 0;
  background: color-mix(in srgb, var(--accent) 5%, var(--card)); display: none;
}}
.quiz .why.show {{ display: block; }}
.quiz-bar {{
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  flex-wrap: wrap; margin: 8px 0 4px;
}}
.quiz-score {{ font-family: "Archivo", system-ui, sans-serif; font-weight: 700; font-size: 1.1rem; }}
.quiz-score b {{ color: var(--accent); }}
.quiz-final {{
  display: none; margin-top: 14px; padding: 16px 18px; border-radius: 14px;
  background: color-mix(in srgb, var(--accent) 10%, var(--card));
  border: 1px solid color-mix(in srgb, var(--accent) 30%, var(--line)); font-weight: 600;
}}
.quiz-final.show {{ display: block; }}

/* Nav footer */
.navfoot {{
  display: flex; gap: 12px; justify-content: space-between; align-items: stretch;
  flex-wrap: wrap; padding: 24px 0 48px; border-top: 1px solid var(--line); margin-top: 24px;
}}
.navfoot a {{ flex: 1 1 240px; min-width: 220px; }}
.navfoot .btn {{ width: 100%; justify-content: space-between; }}
.navfoot .spacer {{ flex: 1 1 240px; min-width: 220px; }}

footer.site-footer {{
  border-top: 1px solid var(--line); padding: 24px 0 40px; color: var(--muted);
  font-size: 0.88rem; text-align: center;
}}

@media (max-width: 560px) {{
  .day-card {{ grid-template-columns: 44px 1fr; gap: 12px; padding: 16px; }}
  .day-card .marker {{ width: 44px; height: 44px; font-size: 1.1rem; }}
  .header-inner {{ gap: 8px; }}
  .dots a {{ width: 26px; height: 26px; font-size: 0.78rem; }}
}}

@media (prefers-reduced-motion: reduce) {{
  * {{ animation: none !important; transition: none !important; scroll-behavior: auto !important; }}
}}
"""


# --- Componenti riutilizzabili --------------------------------------------
def dots_nav(phases, current_num):
    items = []
    for ph in phases:
        n = ph["num"]
        cls = "active" if n == current_num else ""
        title = esc(f"Fase {n}: {ph['title']}")
        items.append(
            f'<a href="{phase_file(n)}" class="{cls}" title="{title}"'
            f' aria-label="{title}">{n}</a>'
        )
    return '<nav class="dots" aria-label="Le 6 fasi">' + "".join(items) + "</nav>"


# --- Pagina di FASE --------------------------------------------------------
def render_phase(course, phase):
    phases = course["phases"]
    n = phase["num"]
    accent = phase["accent"]
    first_day = phase["days"][0]["n"]
    last_day = phase["days"][-1]["n"]
    title = phase["title"]

    chips = "".join(f'<span class="chip">{esc(c)}</span>' for c in phase["chips"])

    # Cards dei giorni
    cards = []
    for d in phase["days"]:
        de_list = [de for de, _ in d["ex"]]
        listen = speak_all_btn(de_list, label="🔊 Ascolta") if de_list else ""
        cards.append(f"""
      <article class="day-card">
        <div class="marker" aria-hidden="true">{d['n']}</div>
        <div class="day-body">
          <h3>Giorno {d['n']} · {esc(d['title'])}</h3>
          <p class="lead">{esc(d['lead'])}</p>
          <p class="task"><b>Compito:</b> {esc(d['task'])}</p>
          <div class="card-actions">
            <a class="btn" href="{day_file(d['n'])}">Apri la lezione →</a>
            {listen}
          </div>
        </div>
      </article>""")
    cards_html = "".join(cards)

    # Quiz data → JSON sicuro per <script>
    quiz_json = json.dumps(phase["quiz"], ensure_ascii=False).replace("</", "<\\/")

    # Navigazione footer
    prev_html = '<div class="spacer"></div>'
    if n > 1:
        prev = next(p for p in phases if p["num"] == n - 1)
        prev_html = (
            f'<a href="{phase_file(n-1)}"><span class="btn ghost">'
            f'← Fase {n-1} ({esc(prev["title"])})</span></a>'
        )
    if n < 6:
        nxt = next(p for p in phases if p["num"] == n + 1)
        next_html = (
            f'<a href="{phase_file(n+1)}"><span class="btn">'
            f'Fase {n+1} ({esc(nxt["title"])}) →</span></a>'
        )
    else:
        next_html = (
            f'<a href="{phase_file(1)}"><span class="btn">'
            f'Hai finito! 🎉 Ricomincia il ripasso →</span></a>'
        )

    page_title = f"Fase {n}: {title} · {course['title']}"

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page_title)}</title>
<meta name="description" content="Fase {n} di 6 ({esc(phase['accentName'])}) · Giorni {first_day}–{last_day}. {esc(phase['subtitle'])}">
{FONTS_LINK}
<style>{base_css(accent)}</style>
</head>
<body>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="index.html"><span class="dot"></span>{esc(course['title'])}</a>
    {dots_nav(phases, n)}
  </div>
</header>

<main>
  <section class="hero">
    <div class="wrap">
      <div class="bignum" aria-hidden="true">{n}</div>
      <p class="eyebrow">Fase {n} di 6 · {esc(phase['accentName'])} · Giorni {first_day}–{last_day}</p>
      <h1>{esc(title)}</h1>
      <p class="subtitle">{esc(phase['subtitle'])}</p>
      <div class="chips">{chips}</div>
    </div>
  </section>

  <section class="wrap">
    <div class="ex-head">
      <h2 class="display" style="font-size:1.5rem;margin:8px 0 4px;">I 10 giorni della fase</h2>
      <div class="tts-bar">
        <span class="tts-speed" data-tts-speed></span>
        <span class="tts-voice" data-tts-voice></span>
      </div>
    </div>
    <div class="day-list">{cards_html}</div>
  </section>

  <section class="wrap quiz">
    <h2 class="display" style="font-size:1.6rem;margin:8px 0 4px;">Mini-quiz della Fase {n}</h2>
    <p style="color:var(--muted);margin:0 0 10px;">5 domande per verificare cosa hai imparato.</p>
    <div class="quiz-bar">
      <div class="quiz-score">Punteggio: <b id="score">0</b> / 5</div>
      <button class="btn ghost" id="reset" type="button">↺ Rifai il quiz</button>
    </div>
    <div id="quiz-root"></div>
    <div class="quiz-final" id="final"></div>
  </section>

  <nav class="wrap navfoot" aria-label="Navigazione fasi">
    {prev_html}
    {next_html}
  </nav>
</main>

<footer class="site-footer">
  <div class="wrap">{esc(course['title'])} · Fase {n} di 6 · <a href="index.html">Torna all'indice</a></div>
</footer>

<script>
const QUIZ = {quiz_json};
const root = document.getElementById('quiz-root');
const scoreEl = document.getElementById('score');
const finalEl = document.getElementById('final');
let score = 0, answered = 0;

function buildQuiz() {{
  score = 0; answered = 0;
  scoreEl.textContent = '0';
  finalEl.className = 'quiz-final';
  finalEl.textContent = '';
  root.innerHTML = '';
  QUIZ.forEach((item, qi) => {{
    const card = document.createElement('div');
    card.className = 'qcard';
    const q = document.createElement('p');
    q.className = 'q';
    q.innerHTML = '<span class="qn">' + (qi + 1) + '.</span> ' + escapeHtml(item.q);
    card.appendChild(q);
    const opts = document.createElement('div');
    opts.className = 'opts';
    item.opts.forEach((opt, oi) => {{
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'opt';
      b.textContent = opt;
      b.addEventListener('click', () => choose(card, opts, item, oi));
      opts.appendChild(b);
    }});
    card.appendChild(opts);
    const why = document.createElement('div');
    why.className = 'why';
    why.textContent = item.why;
    card.appendChild(why);
    root.appendChild(card);
  }});
}}

function choose(card, opts, item, oi) {{
  if (card.dataset.done) return;
  card.dataset.done = '1';
  answered++;
  const buttons = opts.querySelectorAll('button.opt');
  buttons.forEach((b, i) => {{
    b.disabled = true;
    if (i === item.a) b.classList.add('correct');
    else if (i === oi) b.classList.add('wrong');
  }});
  if (oi === item.a) {{ score++; scoreEl.textContent = String(score); }}
  card.querySelector('.why').classList.add('show');
  if (answered === QUIZ.length) showFinal();
}}

function showFinal() {{
  let msg;
  if (score === QUIZ.length) msg = 'Perfetto! Hai fatto ' + score + '/5. Sei pronto per la prossima fase!';
  else if (score >= 3) msg = 'Bene! ' + score + '/5. Ancora un piccolo ripasso e ci sei.';
  else msg = 'Rivedi e riprova: ' + score + '/5. Rileggi i giorni della fase e ritenta.';
  finalEl.textContent = msg;
  finalEl.className = 'quiz-final show';
}}

function escapeHtml(s) {{
  return String(s).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
}}

document.getElementById('reset').addEventListener('click', buildQuiz);
buildQuiz();
</script>
{TTS_SCRIPT}
</body>
</html>
"""


# --- Espansione contenuti pagina GIORNO ------------------------------------
def expand_explanation(d):
    """Sviluppa i `points` in prosa. Se mancano, usa il lead."""
    pts = d.get("points", [])
    if not pts:
        return f"<p>{esc(d['lead'])} In questa lezione concentrati sul vocabolario qui sotto: leggilo ad alta voce e prova a ripeterlo a memoria.</p>"
    paras = [f"<p>{esc(d['lead'])}</p>"]
    intro = ("Vediamo i punti chiave di oggi, uno alla volta:"
             if len(pts) > 1 else "Ecco il punto chiave di oggi:")
    items = "".join(f"<li>{esc(p)}</li>" for p in pts)
    paras.append(f"<p>{intro}</p><ul>{items}</ul>")
    paras.append("<p>Non avere fretta: rileggi gli esempi qui sotto finché lo schema non ti sembra naturale.</p>")
    return "".join(paras)


def render_day(course, day, phase):
    phases = course["phases"]
    n = day["n"]
    pnum = phase["num"]
    accent = phase["accent"]

    # Esempi → tabella (con pulsanti audio per ogni frase tedesca)
    rows = "".join(
        f'<tr><td class="de"><span>{esc(de)}</span> {speak_btn(de)}</td>'
        f'<td class="it">{esc(it)}</td></tr>'
        for de, it in day["ex"]
    )
    de_list = [de for de, _ in day["ex"]]
    listen_all = speak_all_btn(de_list)
    ex_table = f"""<table class="ex">
  <caption>Leggi a voce alta: prima il tedesco, poi l'italiano. Tocca 🔊 per ascoltare.</caption>
  <thead><tr><th>Tedesco</th><th>Italiano</th></tr></thead>
  <tbody>{rows}</tbody>
</table>"""

    # Callout: usa il primo point, o il lead
    tip = day["points"][0] if day.get("points") else day["lead"]

    # Progress
    pct = round(n / 60 * 100)

    # Navigazione footer
    back = (f'<a href="{phase_file(pnum)}"><span class="btn ghost">'
            f'↩ Torna alla Fase {pnum}</span></a>')
    if n < 60:
        nxt = (f'<a href="{day_file(n+1)}"><span class="btn">'
               f'Giorno {n+1} →</span></a>')
    else:
        nxt = ('<a href="index.html"><span class="btn">'
               '🎉 Corso completato — torna all\'indice</span></a>')

    page_title = f"Giorno {n}: {day['title']} · {course['title']}"

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page_title)}</title>
<meta name="description" content="Giorno {n} di 60 — Fase {pnum} ({esc(phase['title'])}). {esc(day['lead'])}">
{FONTS_LINK}
<style>{base_css(accent)}</style>
</head>
<body>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="{phase_file(pnum)}"><span class="dot"></span>Tedesco · Fase {pnum}</a>
    <a class="header-link" href="{phase_file(pnum)}">↩ Indice Fase {pnum}</a>
  </div>
</header>

<main>
  <section class="hero">
    <div class="wrap">
      <div class="bignum" aria-hidden="true">{n}</div>
      <p class="eyebrow">Giorno {n} / 60 · Fase {pnum} — {esc(phase['title'])}</p>
      <h1>{esc(day['title'])}</h1>
      <p class="subtitle">{esc(day['lead'])}</p>
      <div class="progress">
        <div class="bar"><span style="width:{pct}%"></span></div>
        <div class="label">Giorno {n} / 60 · <a href="index.html" style="color:var(--accent);">indice</a></div>
      </div>
    </div>
  </section>

  <section class="wrap">
    <div class="section prose">
      <h2><span class="num">1</span> Spiegazione</h2>
      {expand_explanation(day)}
    </div>

    <div class="section">
      <div class="ex-head">
        <h2><span class="num">2</span> Esempi</h2>
        <div class="ex-actions">
          <span class="tts-speed" data-tts-speed></span>
          <span class="tts-voice" data-tts-voice></span>
          {listen_all}
        </div>
      </div>
      {ex_table}
    </div>

    <div class="section">
      <h2><span class="num">3</span> Trucco del giorno</h2>
      <div class="callout">
        <h3>💡 Tienilo a mente</h3>
        <p>{esc(tip)}</p>
      </div>
    </div>

    <div class="section">
      <h2><span class="num">4</span> Mini-esercizio</h2>
      <div class="exercise">
        <h3>Il tuo compito di oggi</h3>
        <p>{esc(day['task'])}</p>
        <details>
          <summary>Mostra soluzione / esempio</summary>
          <div class="solution">
            <p><b>Esempio svolto:</b></p>
            <table class="ex" style="margin-top:8px;">
              <tbody>{rows}</tbody>
            </table>
            <p style="margin-top:10px;color:var(--muted);">Confronta con quello che hai prodotto: l'importante è che articoli, ordine delle parole e desinenze corrispondano agli esempi.</p>
          </div>
        </details>
      </div>
    </div>
  </section>

  <nav class="wrap navfoot" aria-label="Navigazione giorni">
    {back}
    {nxt}
  </nav>
</main>

<footer class="site-footer">
  <div class="wrap">{esc(course['title'])} · Giorno {n} di 60 · <a href="{phase_file(pnum)}">Fase {pnum}</a> · <a href="index.html">Indice</a></div>
</footer>
{TTS_SCRIPT}
</body>
</html>
"""


# --- index.html ------------------------------------------------------------
def render_index(course):
    phases = course["phases"]
    cards = []
    for ph in phases:
        n = ph["num"]
        first = ph["days"][0]["n"]
        last = ph["days"][-1]["n"]
        cards.append(f"""
      <a class="pcard" href="{phase_file(n)}" style="--accent:{ph['accent']};">
        <div class="pcard-num" aria-hidden="true">{n}</div>
        <div class="pcard-body">
          <p class="eyebrow">Fase {n} · {esc(ph['accentName'])} · Giorni {first}–{last}</p>
          <h3>{esc(ph['title'])}</h3>
          <p class="pcard-sub">{esc(ph['subtitle'])}</p>
          <span class="pcard-go">Inizia la fase →</span>
        </div>
      </a>""")
    cards_html = "".join(cards)

    extra_css = """
.index-hero { padding: 64px 0 32px; }
.index-hero h1 { font-size: clamp(2.4rem, 8vw, 4.2rem); margin: 8px 0 16px; }
.index-hero .subtitle { font-size: clamp(1.1rem, 2.6vw, 1.4rem); color: var(--muted); max-width: 54ch; }
.index-meta { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 22px; }
.index-meta span {
  font-weight: 600; font-size: 0.85rem; padding: 8px 14px; border-radius: 999px;
  background: var(--card); border: 1px solid var(--line);
}
.phase-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; padding: 16px 0 48px; }
.pcard {
  position: relative; overflow: hidden; text-decoration: none; color: var(--ink);
  background: var(--card); border: 1px solid var(--line); border-radius: 18px;
  padding: 24px; display: block; border-top: 5px solid var(--accent);
  transition: transform .15s ease, border-color .15s ease, box-shadow .15s ease;
}
.pcard:hover { transform: translateY(-4px); border-color: var(--accent); box-shadow: 0 10px 30px rgba(0,0,0,0.06); }
.pcard-num {
  position: absolute; right: 10px; top: -6px; font-family: "Archivo", system-ui, sans-serif;
  font-weight: 900; font-size: 120px; line-height: 1; color: var(--accent); opacity: 0.10;
}
.pcard-body { position: relative; z-index: 1; }
.pcard h3 { font-size: 1.5rem; margin: 8px 0 8px; }
.pcard-sub { color: var(--muted); margin: 0 0 16px; }
.pcard-go { font-weight: 600; color: var(--accent); }
"""

    og = (
        '<meta property="og:type" content="website">\n'
        f'<meta property="og:title" content="{esc(course["title"])}">\n'
        '<meta property="og:description" content="Corso di tedesco A1 in 60 giorni per italiani: 6 fasi, pochi minuti al giorno.">\n'
        '<meta property="og:locale" content="it_IT">\n'
        '<meta name="twitter:card" content="summary">'
    )

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(course['title'])} · Corso A1 per italiani</title>
<meta name="description" content="Impara il tedesco da zero in 60 giorni: 6 fasi, pochi minuti al giorno, fino al livello A1. In italiano, con esempi e quiz.">
{og}
{FONTS_LINK}
<style>{base_css('#D7263D')}{extra_css}</style>
</head>
<body>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="index.html"><span class="dot"></span>{esc(course['title'])}</a>
    {dots_nav(phases, 0)}
  </div>
</header>

<main>
  <section class="index-hero">
    <div class="wrap">
      <p class="eyebrow">Corso di tedesco · livello A1</p>
      <h1>{esc(course['title'])}</h1>
      <p class="subtitle">Dallo zero all'A1 in circa 60 giorni. Pochi minuti al giorno, 6 fasi chiare, esempi tedesco→italiano e un mini-quiz alla fine di ogni fase.</p>
      <div class="index-meta">
        <span>🗓️ 60 giorni</span>
        <span>⏱️ Pochi minuti al giorno</span>
        <span>🎯 Obiettivo A1</span>
        <span>🇮🇹 Spiegato in italiano</span>
      </div>
    </div>
  </section>

  <section class="wrap">
    <h2 class="display" style="font-size:1.6rem;margin:8px 0 4px;">Le 6 fasi del corso</h2>
    <div class="phase-grid">{cards_html}</div>
  </section>
</main>

<footer class="site-footer">
  <div class="wrap">{esc(course['title'])} · Corso gratuito di tedesco A1 · 60 giorni, 6 fasi.</div>
</footer>
</body>
</html>
"""


# --- Main ------------------------------------------------------------------
def main():
    with open(os.path.join(BASE, "course.json"), encoding="utf-8") as f:
        course = json.load(f)

    written = []

    # index
    path = os.path.join(BASE, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(render_index(course))
    written.append("index.html")

    # fasi e giorni
    for phase in course["phases"]:
        path = os.path.join(BASE, phase_file(phase["num"]))
        with open(path, "w", encoding="utf-8") as f:
            f.write(render_phase(course, phase))
        written.append(phase_file(phase["num"]))

        for day in phase["days"]:
            assert phase_of_day(day["n"]) == phase["num"], (
                f"Giorno {day['n']} non appartiene alla fase {phase['num']}"
            )
            path = os.path.join(BASE, day_file(day["n"]))
            with open(path, "w", encoding="utf-8") as f:
                f.write(render_day(course, day, phase))
            written.append(day_file(day["n"]))

    print(f"Generati {len(written)} file:")
    print(f"  - 1 index.html")
    print(f"  - {sum(1 for w in written if w.startswith('tedesco-fase'))} pagine di fase")
    print(f"  - {sum(1 for w in written if w.startswith('tedesco-giorno'))} pagine di giorno")
    assert len(written) == 67, f"Attesi 67 file, generati {len(written)}"
    print("OK: 67 file totali.")


if __name__ == "__main__":
    main()
