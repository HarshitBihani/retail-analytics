"""Shared look for the report pages: editorial headlines, KPI cards, numbered action cards, chips, light and dark mode.

Self-contained (no web fonts, no CDN): serif headlines use the system's Georgia/Charter, so the page works offline and in a file viewer.
Copied into each project so each repository stays independent.
"""
from __future__ import annotations
import html as _h

CSS = """
:root{--bg:#f6f4ee;--card:#fffdf9;--ink:#161a22;--muted:#6a7080;--line:#e7e2d6;--accent:__ACCENT__;--soft:__SOFT__;
--good:#0f7b5f;--goodbg:#e2f3ec;--bad:#b4372f;--badbg:#f9e4e1;--warn:#9a5b00;--warnbg:#fdf1d9;--shadow:0 1px 2px rgba(20,24,32,.05),0 8px 24px rgba(20,24,32,.04)}
:root[data-theme=dark]{--bg:#0d1015;--card:#151a21;--ink:#ecebe6;--muted:#98a0ae;--line:#262c36;--soft:__SOFTDARK__;
--goodbg:#10352b;--good:#6fd3b0;--badbg:#3a1d1b;--bad:#f09a92;--warnbg:#3a2b0e;--warn:#f0c26a;--shadow:none}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 Inter,"Segoe UI",system-ui,-apple-system,Arial,sans-serif}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px 80px}
.top{display:flex;justify-content:space-between;align-items:center;padding:22px 0}
.brand{display:flex;align-items:center;gap:10px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.logo{width:30px;height:30px;border-radius:9px;background:var(--ink);color:var(--bg);display:grid;place-items:center;font-weight:700;font-size:14px;letter-spacing:0}
.toggle{border:1px solid var(--line);background:var(--card);color:var(--muted);border-radius:999px;padding:7px 14px;font:inherit;font-size:12px;letter-spacing:.1em;text-transform:uppercase;cursor:pointer}
.toggle:hover{color:var(--ink)}
.eyebrow{display:flex;align-items:center;gap:10px;margin-top:46px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.dot{width:7px;height:7px;border-radius:50%;background:var(--accent)}
h1{font:600 clamp(38px,7vw,76px)/1.02 Georgia,"Iowan Old Style",Charter,"Times New Roman",serif;letter-spacing:-.025em;margin:18px 0 18px}
h1 em{color:var(--accent);font-weight:500}
.lede{max-width:640px;color:var(--muted);font-size:17px;margin:0 0 8px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:38px 0 6px}
.kpi{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--accent);border-radius:14px;padding:16px 18px;box-shadow:var(--shadow)}
.kpi:nth-child(2){border-top-color:#e0803a}.kpi:nth-child(3){border-top-color:#3d8fb8}.kpi:nth-child(4){border-top-color:#d96a9a}.kpi:nth-child(5){border-top-color:#e2b53c}
.kl{font-size:12px;letter-spacing:.06em;color:var(--muted);text-transform:uppercase}.kv{font:600 25px/1.15 Georgia,Charter,serif;white-space:nowrap;margin-top:8px;letter-spacing:-.01em}.ks{font-size:12.5px;color:var(--muted);margin-top:4px}
section{margin-top:76px}
.kicker{font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:600}
.sh{display:flex;justify-content:space-between;align-items:end;gap:24px;flex-wrap:wrap;margin:8px 0 22px}
h2{font:600 clamp(28px,4.4vw,44px)/1.08 Georgia,"Iowan Old Style",Charter,serif;letter-spacing:-.02em;margin:0}
.aside{max-width:340px;color:var(--muted);font-size:13.5px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;box-shadow:var(--shadow);margin:14px 0;overflow:hidden}
.card h3{margin:0 0 4px;font:600 18px/1.3 Georgia,Charter,serif}
.cap{color:var(--muted);font-size:13.5px;margin:2px 0 10px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.actions{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px}
.act{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;display:flex;gap:16px;box-shadow:var(--shadow)}
.num{flex:none;width:34px;height:34px;border-radius:50%;background:var(--soft);color:var(--accent);display:grid;place-items:center;font:600 14px Georgia,serif}
.act h3{margin:2px 0 6px;font:600 19px/1.25 Georgia,Charter,serif}.act p{margin:0;color:var(--muted);font-size:14px}
.note-chip{display:inline-block;margin-top:9px;padding:3px 10px;border-radius:999px;background:var(--warnbg);color:var(--warn);font-size:12px}
.chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:12px}
.chip{display:inline-block;padding:4px 12px;border-radius:999px;font-size:13px}
.chip.good{background:var(--goodbg);color:var(--good)}.chip.bad{background:var(--badbg);color:var(--bad)}.chip.neutral{background:var(--soft);color:var(--accent)}
.tablewrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px}
th{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:left;font-weight:600;padding:10px 12px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:12px;border-bottom:1px solid var(--line);vertical-align:top}tr:last-child td{border-bottom:0}
td.n{text-align:right;font-variant-numeric:tabular-nums}.big{font:600 22px Georgia,serif}
.callout{border-radius:14px;padding:14px 18px;margin:14px 0;font-size:14.5px}
.callout.warn{background:var(--warnbg);color:var(--warn)}.callout.info{background:var(--soft);color:var(--ink)}
.callout b{font-weight:600}
details{margin:14px 0}summary{cursor:pointer;color:var(--muted);font-size:13px;letter-spacing:.08em;text-transform:uppercase}
.foot{margin-top:70px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}
a{color:var(--accent)}
@media(max-width:760px){.grid2{grid-template-columns:1fr}.actions{grid-template-columns:1fr}.wrap{padding:0 16px 60px}section{margin-top:56px}.eyebrow{margin-top:30px}}
"""

JS = """
(function(){
  var root=document.documentElement, KEY='report-theme';
  function stored(){try{return localStorage.getItem(KEY)}catch(e){return null}}
  function save(v){try{localStorage.setItem(KEY,v)}catch(e){}}
  function colors(dark){return dark?{font:'#c9ced8',grid:'#2a313c'}:{font:'#3a4150',grid:'#e9e5da'}}
  function recolor(){
    if(!window.Plotly) return;
    var c=colors(root.getAttribute('data-theme')==='dark');
    document.querySelectorAll('.js-plotly-plot').forEach(function(d){
      try{Plotly.relayout(d,{'font.color':c.font,'xaxis.gridcolor':c.grid,'yaxis.gridcolor':c.grid,'xaxis.zerolinecolor':c.grid,'yaxis.zerolinecolor':c.grid,'legend.font.color':c.font})}catch(e){}
    });
  }
  function apply(t){root.setAttribute('data-theme',t);var b=document.getElementById('toggle');if(b)b.textContent=t==='dark'?'Light mode':'Dark mode';recolor()}
  var t=(location.hash==='#dark'?'dark':null)||stored()||(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
  window.addEventListener('DOMContentLoaded',function(){apply(t);document.getElementById('toggle').onclick=function(){t=root.getAttribute('data-theme')==='dark'?'light':'dark';save(t);apply(t)};setTimeout(recolor,400)});
})();
"""

PLOT = dict(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, Segoe UI, Arial", color="#3a4150", size=13), margin=dict(l=50, r=20, t=24, b=40), height=360,
            xaxis=dict(gridcolor="#e9e5da"), yaxis=dict(gridcolor="#e9e5da"))

PALETTE = ["#6a5cff", "#e0803a", "#3d8fb8", "#d96a9a", "#e2b53c", "#8a8f9c"]


def esc(s) -> str:
    return _h.escape(str(s))


def page(title: str, brand: str, eyebrow: str, h1: str, accent_word: str, lede: str, body: str, plotly_js: str = "",
         accent: str = "#6a5cff", soft: str = "#ecebff", soft_dark: str = "#23223f", logo: str = "R") -> str:
    css = CSS.replace("__ACCENT__", accent).replace("__SOFT__", soft).replace("__SOFTDARK__", soft_dark)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><script>{plotly_js}</script><style>{css}</style><script>{JS}</script></head><body><div class="wrap">
<div class="top"><div class="brand"><span class="logo">{esc(logo)}</span>{esc(brand)}</div><button id="toggle" class="toggle" type="button">Dark mode</button></div>
<div class="eyebrow"><span class="dot"></span>{esc(eyebrow)}</div>
<h1>{esc(h1)} <em>{esc(accent_word)}</em></h1><p class="lede">{lede}</p>
{body}
</div></body></html>"""


def kpis(items) -> str:
    """items: (label, value, optional small line)"""
    return '<div class="kpis">' + "".join(
        f'<div class="kpi"><div class="kl">{esc(l)}</div><div class="kv">{esc(v)}</div>' + (f'<div class="ks">{esc(s[0])}</div>' if (s := rest) else "") + "</div>"
        for l, v, *rest in items) + "</div>"


def section(kicker: str, title: str, body: str, aside: str = "") -> str:
    return (f'<section><div class="sh"><div><div class="kicker">{esc(kicker)}</div><h2>{title}</h2></div>'
            + (f'<div class="aside">{aside}</div>' if aside else "") + f"</div>{body}</section>")


def action_cards(items) -> str:
    """items: (number, title, text html, optional note)"""
    out = []
    for n, title, text, *note in items:
        chip = f'<span class="note-chip">{esc(note[0])}</span>' if note and note[0] else ""
        out.append(f'<div class="act"><div class="num">{esc(n)}</div><div><h3>{esc(title)}</h3><p>{text}</p>{chip}</div></div>')
    return '<div class="actions">' + "".join(out) + "</div>"


def chips(items, kind="neutral") -> str:
    return '<div class="chips">' + "".join(f'<span class="chip {kind}">{esc(i)}</span>' for i in items) + "</div>"


def card(inner: str, title: str = "", caption: str = "") -> str:
    return '<div class="card">' + (f"<h3>{title}</h3>" if title else "") + (f'<div class="cap">{caption}</div>' if caption else "") + inner + "</div>"


def callout(inner: str, kind: str = "info") -> str:
    return f'<div class="callout {kind}">{inner}</div>'


def table(headers, rows, numeric_cols=()) -> str:
    """headers: list of str. rows: list of lists of already-safe HTML or text (escaped by caller where needed)."""
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f'<td class="{"n" if i in numeric_cols else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f'<div class="tablewrap"><table><tr>{th}</tr>{trs}</table></div>'


def fig_html(fig, **layout) -> str:
    fig.update_layout(**{**PLOT, **layout})
    return fig.to_html(full_html=False, include_plotlyjs=False, config=dict(displayModeBar=False, responsive=True))
