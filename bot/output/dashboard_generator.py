"""
dashboard_generator.py
──────────────────────
Génère un dashboard HTML mis à jour en temps réel.
Affiche tous les signaux détectés avec leurs figures.
Ouvre dans le navigateur → tu vois les signaux sans TradingView.
"""

import os
import json
from datetime import datetime
from typing import List


class DashboardGenerator:
    """
    Génère outputs/dashboard.html
    Rafraîchi automatiquement toutes les 60 secondes.
    """

    def __init__(self, output_path: str = "outputs/dashboard.html"):
        self.output_path = output_path
        os.makedirs("outputs", exist_ok=True)

    def generate(self, signals: list, backtest_report=None):
        """Génère le dashboard avec les signaux en cours."""
        html = self._build_html(signals, backtest_report)
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(html)

    def _build_html(self, signals: list, report=None) -> str:
        now         = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        signal_cards= "".join(self._signal_card(s) for s in signals)
        backtest_html = self._backtest_section(report) if report else ""
        n_long  = sum(1 for s in signals if s.get('direction') == 'LONG')
        n_short = sum(1 for s in signals if s.get('direction') == 'SHORT')
        n_comp  = sum(1 for s in signals if s.get('compression_zone'))

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="60">
<title>Trading Bot — Dashboard</title>
<style>
  :root {{
    --bg: #0d0d0d; --bg2: #141414; --panel: #1a1a1a; --panel2: #222;
    --border: #2a2a2a; --border2: #333; --text: #e0e0e0; --muted: #666;
    --long: #2dcc74; --long-bg: #0a1f12;
    --short: #e84545; --short-bg: #200a0a;
    --accent: #4f8ef7; --warn: #f5a623; --purple: #9b7ef5;
    --r: 10px; --rs: 6px;
  }}
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 13px; padding: 0; }}
  ::-webkit-scrollbar {{ width: 4px; }} ::-webkit-scrollbar-track {{ background: var(--bg); }} ::-webkit-scrollbar-thumb {{ background: var(--border2); border-radius: 4px; }}

  .topbar {{ background: var(--bg2); border-bottom: 1px solid var(--border); padding: 12px 20px; display: flex; align-items: center; gap: 0; }}
  .brand {{ font-size: 15px; font-weight: 800; color: #fff; padding-right: 16px; border-right: 1px solid var(--border); }}
  .brand em {{ color: var(--accent); font-style: normal; }}
  .tstats {{ display: flex; padding-left: 16px; gap: 0; }}
  .tstat {{ display: flex; flex-direction: column; align-items: center; padding: 0 14px; border-right: 1px solid var(--border); }}
  .tstat:last-child {{ border-right: none; }}
  .tv {{ font-size: 18px; font-weight: 800; line-height: 1; }} .tl {{ font-size: 9px; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; margin-top: 2px; }}
  .tv.g {{ color: var(--long); }} .tv.r {{ color: var(--short); }} .tv.b {{ color: var(--accent); }} .tv.o {{ color: var(--warn); }}
  .time {{ margin-left: auto; font-size: 11px; color: var(--muted); }}

  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 16px; padding: 20px; }}

  .card {{ background: var(--panel); border: 1px solid var(--border); border-radius: var(--r); overflow: hidden; }}
  .card.long  {{ border-left: 3px solid var(--long); }}
  .card.short {{ border-left: 3px solid var(--short); }}
  .card.wait  {{ border-left: 3px solid var(--muted); }}

  .card-top {{ padding: 12px 14px 10px; display: flex; align-items: flex-start; gap: 10px; }}
  .verdict {{ font-size: 20px; font-weight: 900; min-width: 62px; padding: 5px 10px; border-radius: 7px; text-align: center; flex-shrink: 0; }}
  .verdict.long  {{ background: var(--long-bg); color: var(--long); border: 1px solid rgba(45,204,116,.3); }}
  .verdict.short {{ background: var(--short-bg); color: var(--short); border: 1px solid rgba(232,69,69,.3); }}
  .verdict.wait  {{ background: rgba(70,70,70,.15); color: var(--muted); border: 1px solid var(--border); }}
  .vmeta {{ flex: 1; min-width: 0; }}
  .vpair {{ font-size: 15px; font-weight: 800; color: #fff; }}
  .vtf   {{ font-size: 11px; color: var(--muted); margin-top: 2px; }}
  .vpatt {{ font-size: 11px; color: var(--accent); margin-top: 3px; font-weight: 600; }}

  .score-wrap {{ padding: 0 14px 10px; }}
  .score-hd {{ display: flex; justify-content: space-between; font-size: 10px; color: var(--muted); margin-bottom: 4px; }}
  .score-bar {{ height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; }}
  .score-fill {{ height: 100%; border-radius: 2px; }}

  .patt-wrap {{ padding: 0 14px 10px; }}
  .patt-svg {{ width: 100%; height: 80px; display: block; background: #0d0d0d; border-radius: 6px; }}

  .thumbnail {{ display: block; width: calc(100% - 28px); margin: 0 14px 10px; height: 120px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border); }}

  .prices {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 6px; padding: 0 14px 10px; }}
  .pbox {{ background: var(--panel2); border-radius: var(--rs); padding: 6px 8px; text-align: center; }}
  .pbox .pl {{ font-size: 9px; color: var(--muted); text-transform: uppercase; margin-bottom: 2px; }}
  .pbox .pv {{ font-size: 12px; font-weight: 700; }}
  .pbox.entry .pv {{ color: var(--accent); }} .pbox.sl .pv {{ color: var(--short); }}
  .pbox.tp1 .pv {{ color: var(--warn); }} .pbox.tp2 .pv {{ color: var(--long); }}

  .gates {{ padding: 0 14px 8px; display: flex; gap: 6px; }}
  .gate {{ font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 10px; }}
  .gate.ok   {{ background: rgba(45,204,116,.12); color: var(--long); border: 1px solid rgba(45,204,116,.25); }}
  .gate.fail {{ background: rgba(232,69,69,.12); color: var(--short); border: 1px solid rgba(232,69,69,.25); }}

  .tags {{ padding: 0 14px 10px; display: flex; flex-wrap: wrap; gap: 5px; }}
  .tag {{ font-size: 10px; padding: 2px 8px; border-radius: 10px; }}
  .tsr  {{ background: rgba(79,142,247,.1); color: #79c0ff; }}
  .tadx {{ background: rgba(45,204,116,.1); color: #56d364; }}
  .tqqe {{ background: rgba(243,179,65,.1); color: #f5a623; }}
  .thtf {{ background: rgba(155,126,245,.1); color: var(--purple); }}
  .tcomp {{ background: rgba(245,166,35,.1); color: var(--warn); }}
  .trr  {{ background: rgba(79,142,247,.1); color: var(--accent); }}

  .summary {{ padding: 8px 14px 12px; font-size: 11px; color: #888; line-height: 1.5; border-top: 1px solid var(--border); }}

  .empty {{ text-align: center; color: var(--muted); padding: 80px 20px; font-size: 14px; }}

  .backtest {{ background: var(--panel); border: 1px solid var(--border); border-radius: var(--r); padding: 18px; margin: 0 20px 20px; }}
  .backtest h2 {{ color: var(--accent); margin-bottom: 14px; font-size: 14px; }}
  .bt-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 10px; }}
  .bt-box {{ background: var(--panel2); border-radius: var(--rs); padding: 10px; text-align: center; }}
  .bt-box .val {{ font-size: 20px; font-weight: bold; }} .bt-box .lbl {{ font-size: 10px; color: var(--muted); margin-top: 3px; }}
  .green {{ color: var(--long); }} .red {{ color: var(--short); }} .blue {{ color: var(--accent); }}
</style>
</head>
<body>

<div class="topbar">
  <div class="brand">Trading Bot <em>Ultimate</em></div>
  <div class="tstats">
    <div class="tstat"><div class="tv b">{len(signals)}</div><div class="tl">Signaux</div></div>
    <div class="tstat"><div class="tv g">{n_long}</div><div class="tl">Long</div></div>
    <div class="tstat"><div class="tv r">{n_short}</div><div class="tl">Short</div></div>
    <div class="tstat"><div class="tv o">{n_comp}</div><div class="tl">Compression</div></div>
  </div>
  <div class="time">Mis à jour : {now} — Rafraîchi toutes les 60s</div>
</div>

<div class="grid">
{signal_cards if signals else '<div class="empty">⏳ Aucun signal détecté — Scanner en cours...</div>'}
</div>

{backtest_html}

</body></html>"""

    def _pattern_svg(self, pattern_name: str, direction: str) -> str:
        """Retourne un SVG inline illustrant le pattern."""
        n = (pattern_name or "").lower()
        L = direction == "LONG"
        G, R, W = "#2dcc74", "#e84545", "#f5a623"
        GR, RR = "rgba(45,204,116,0.12)", "rgba(232,69,69,0.12)"
        MC = G if L else R
        SR_Y = 78 if L else 22

        def candle(cx, o, c, hi, lo, col):
            bx = min(o, c)
            bh = max(2, abs(c - o))
            return (f'<line x1="{cx}" y1="{hi}" x2="{cx}" y2="{lo}" stroke="{col}" stroke-width="1.5"/>'
                    f'<rect x="{cx-6}" y="{bx}" width="12" height="{bh}" fill="{col}" rx="1"/>')

        def sr_line(y, label, col, above=True):
            dy = y - 3 if above else y + 9
            return (f'<line x1="0" y1="{y}" x2="320" y2="{y}" stroke="{col}" stroke-width="1" stroke-dasharray="4,3"/>'
                    f'<text x="4" y="{dy}" fill="{col}" font-size="8">{label}</text>')

        def arrow(x, y, up):
            sym = "↑" if up else "↓"
            col = G if up else R
            return f'<text x="{x}" y="{y}" fill="{col}" font-size="18" font-weight="bold">{sym}</text>'

        def polyline(pts, col, w=1.5):
            d = " ".join(f"{x},{y}" for x, y in pts)
            return f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="{w}"/>'

        body = ""

        if "pin bar" in n or "pin_bar" in n:
            sy = 78 if L else 22
            body = f'<rect x="0" y="{sy-8}" width="320" height="16" fill="{GR if L else RR}"/>'
            body += sr_line(sy, "Support" if L else "Résistance", MC, L)
            if L:
                body += candle(160, 30, 26, 24, 78, G)
                body += arrow(240, 44, True)
            else:
                body += candle(160, 60, 64, 22, 68, R)
                body += arrow(240, 62, False)

        elif "hammer" in n and "shooting" not in n:
            body = f'<rect x="0" y="70" width="320" height="16" fill="{GR}"/>'
            body += sr_line(76, "Support", G, True)
            body += candle(160, 33, 27, 25, 78, G)
            body += arrow(240, 50, True)

        elif "shooting star" in n or "shooting_star" in n:
            body = f'<rect x="0" y="14" width="320" height="16" fill="{RR}"/>'
            body += sr_line(22, "Résistance", R, False)
            body += candle(160, 62, 68, 22, 72, R)
            body += arrow(240, 55, False)

        elif "engulf" in n:
            sy = 78 if L else 22
            body = f'<rect x="0" y="{sy-8}" width="320" height="16" fill="{GR if L else RR}"/>'
            body += sr_line(sy, "Support" if L else "Résistance", MC, L)
            if L:
                body += candle(120, 42, 52, 38, 55, R)
                body += candle(200, 56, 30, 26, 60, G)
            else:
                body += candle(120, 55, 45, 40, 58, G)
                body += candle(200, 35, 60, 30, 64, R)
            body += arrow(260, 50, L)

        elif "doji" in n:
            sy = 78 if L else 22
            body = f'<rect x="0" y="{sy-8}" width="320" height="16" fill="{GR if L else RR}"/>'
            body += sr_line(sy, "Support" if L else "Résistance", MC, L)
            body += candle(160, 47, 49, 28, 72, "#4a5568")
            body += arrow(240, 50, L)

        elif "morning star" in n:
            body = f'<rect x="0" y="70" width="320" height="16" fill="{GR}"/>'
            body += sr_line(76, "Support", G, True)
            body += candle(70, 30, 58, 25, 62, R)
            body += candle(160, 65, 68, 62, 72, "#4a5568")
            body += candle(250, 60, 34, 28, 64, G)
            body += arrow(278, 52, True)

        elif "evening star" in n:
            body = f'<rect x="0" y="14" width="320" height="16" fill="{RR}"/>'
            body += sr_line(22, "Résistance", R, False)
            body += candle(70, 68, 40, 35, 72, G)
            body += candle(160, 32, 28, 24, 36, "#4a5568")
            body += candle(250, 38, 65, 34, 68, R)
            body += arrow(278, 55, False)

        elif "double top" in n or "double_top" in n:
            body += sr_line(28, "Résistance", R, False)
            body += sr_line(72, "Neckline", W, True)
            pts = [(0,82),(38,76),(83,28),(121,52),(160,28),(198,50),(230,72),(275,88)]
            body += polyline(pts, "#4a5568")
            body += f'<text x="110" y="20" fill="{R}" font-size="13" font-weight="bold">M</text>'
            body += arrow(282, 72, False)

        elif "double bottom" in n or "double_bottom" in n:
            body += sr_line(72, "Support", G, True)
            body += sr_line(28, "Neckline", W, False)
            pts = [(0,18),(38,24),(83,72),(121,48),(160,72),(198,50),(230,28),(275,12)]
            body += polyline(pts, "#4a5568")
            body += f'<text x="110" y="88" fill="{G}" font-size="13" font-weight="bold">W</text>'
            body += arrow(282, 28, True)

        elif "head" in n or "épaule" in n or "epaule" in n or "ete" in n:
            if L:  # Inverse H&S
                body += sr_line(32, "Neckline", W, False)
                pts = [(0,20),(38,32),(70,58),(96,32),(128,32),(160,82),(192,32),(224,32),(256,58),(282,32),(320,18)]
                body += polyline(pts, "#4a5568")
                body += arrow(290, 28, True)
            else:  # H&S
                body += sr_line(68, "Neckline", W, True)
                pts = [(0,80),(38,68),(70,42),(96,68),(128,68),(160,18),(192,68),(224,68),(256,42),(282,68),(320,82)]
                body += polyline(pts, "#4a5568")
                body += arrow(290, 72, False)

        elif "flag" in n or "drapeau" in n or "fanion" in n:
            if L:
                body += polyline([(25,80),(112,20)], G, 2.5)
                body += polyline([(112,20),(144,30),(179,25),(211,35)], "#4a5568")
                body += polyline([(112,32),(144,42),(179,37),(211,47)], "#4a5568")
                body += polyline([(211,35),(288,12)], G, 2)
                body += arrow(262, 22, True)
            else:
                body += polyline([(25,20),(112,80)], R, 2.5)
                body += polyline([(112,80),(144,70),(179,75),(211,65)], "#4a5568")
                body += polyline([(112,68),(144,58),(179,63),(211,53)], "#4a5568")
                body += polyline([(211,65),(288,88)], R, 2)
                body += arrow(262, 75, False)

        elif "compress" in n:
            body += f'<rect x="26" y="35" width="186" height="30" fill="rgba(245,166,35,0.08)"/>'
            body += f'<rect x="26" y="35" width="186" height="30" fill="none" stroke="{W}" stroke-width="1" stroke-dasharray="3,3"/>'
            body += f'<text x="119" y="54" fill="{W}" font-size="8" text-anchor="middle">COMPRESSION</text>'
            col = G if L else R
            body += polyline([(211,50),(294,22 if L else 78)], col, 2.5)
            body += arrow(266, 35 if L else 65, L)

        else:
            # Generic arrow
            sym = "↑" if L else "↓" if direction == "SHORT" else "—"
            col = G if L else R if direction == "SHORT" else "#4a5568"
            body += f'<text x="160" y="52" fill="#3a3a3a" font-size="10" text-anchor="middle">{pattern_name[:20]}</text>'
            body += f'<text x="160" y="72" fill="{col}" font-size="26" font-weight="bold" text-anchor="middle">{sym}</text>'

        return (
            f'<svg class="patt-svg" viewBox="0 0 320 100" xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="320" height="100" fill="#0d0d0d" rx="6"/>'
            f'{body}'
            f'</svg>'
        )

    def _signal_card(self, s: dict) -> str:
        # Detect visual analysis type
        is_visual = s.get("analysis_type") == "visual"

        if is_visual:
            return self._visual_signal_card(s)
        return self._api_signal_card(s)

    def _build_card(self, s: dict) -> str:
        """Card unifiée pour tous les types de signaux."""
        direction  = (s.get("direction") or "NEUTRAL").upper()
        pattern    = s.get("pattern", "Signal")
        pair       = s.get("pair", "—")
        tf         = s.get("timeframe", "—")
        entry      = float(s.get("entry") or 0)
        sl         = float(s.get("sl") or s.get("stop_loss") or 0)
        tp1        = float(s.get("tp1") or 0)
        tp2        = float(s.get("tp2") or 0)
        rr         = s.get("rr_ratio", 0)
        score      = int(s.get("confluence_score") or 0)
        summary    = s.get("summary", "")
        warnings   = s.get("warnings", [])
        timestamp  = (s.get("timestamp") or "")[:16]
        template   = s.get("template", "") or (s.get("_meta") or {}).get("template", "")
        adx        = float(s.get("adx") or 0)
        qqe_status = s.get("qqe_status", "")
        compression= bool(s.get("compression_zone") or s.get("compression"))
        htf_label  = s.get("htf_label", "")
        pine_file  = s.get("pine_file", "")

        # Image path (direct field or via _meta)
        img_raw = s.get("image_path") or (s.get("_meta") or {}).get("image_path", "")
        img_fn  = os.path.basename(img_raw) if img_raw else ""

        dc = "long" if direction == "LONG" else "short" if direction == "SHORT" else "wait"
        vt = "BUY"  if direction == "LONG" else "SELL"  if direction == "SHORT" else "WAIT"

        sc_col = "#2dcc74" if score >= 7 else "#f5a623" if score >= 5 else "#e84545"

        # Pattern SVG
        svg_html = self._pattern_svg(pattern, direction)

        # Thumbnail
        thumb_html = ""
        if img_fn:
            thumb_html = f'<img class="thumbnail" src="/screenshots/{img_fn}" alt="chart" onerror="this.style.display=\'none\'">'

        # Gates
        g1 = s.get("gate1_sr")
        g2 = s.get("gate2_pattern")
        g1ok = bool(g1)
        g2ok = bool(g2)

        # Tags
        tags = f'<span class="tag trr">RR 1:{rr}</span>'
        tags += '<span class="tag tsr">S/R ✓</span>'
        if adx >= 20:
            tags += f'<span class="tag tadx">ADX {round(adx)}</span>'
        if qqe_status and "crois" in qqe_status:
            tags += '<span class="tag tqqe">QQE ✓</span>'
        if compression:
            tags += '<span class="tag tcomp">Compression 🔥</span>'
        if htf_label:
            tags += f'<span class="tag thtf">{htf_label[:24]}</span>'
        for w in (warnings or [])[:2]:
            tags += f'<span class="tag" style="background:rgba(232,69,69,.1);color:#e84545">⚠ {w[:28]}</span>'

        pine_html = f'<a href="/pine/{os.path.basename(pine_file)}" style="font-size:10px;color:#4f8ef7;padding:0 14px 10px;display:block">Pine Script ↗</a>' if pine_file else ""

        sum_html = f'<div class="summary">{summary[:240]}{"…" if len(summary)>240 else ""}</div>' if summary else ""

        def fv(v):
            return f"{v:,.4f}" if v else "—"

        return f"""
<div class="card {dc}">
  <div class="card-top">
    <div class="verdict {dc}">{vt}</div>
    <div class="vmeta">
      <div class="vpair">{pair}</div>
      <div class="vtf">{tf}{" · " + template if template else ""}{" · " + timestamp if timestamp else ""}</div>
      <div class="vpatt">{pattern}</div>
    </div>
  </div>

  <div class="score-wrap">
    <div class="score-hd"><span>Confluence</span><span style="color:{sc_col}">{score} / 10</span></div>
    <div class="score-bar"><div class="score-fill" style="width:{score*10}%;background:{sc_col}"></div></div>
  </div>

  <div class="patt-wrap">{svg_html}</div>

  {thumb_html}

  <div class="prices">
    <div class="pbox entry"><div class="pl">Entrée</div><div class="pv">{fv(entry)}</div></div>
    <div class="pbox sl"><div class="pl">Stop</div><div class="pv">{fv(sl)}</div></div>
    <div class="pbox tp1"><div class="pl">TP1</div><div class="pv">{fv(tp1)}</div></div>
    <div class="pbox tp2"><div class="pl">TP2</div><div class="pv">{fv(tp2)}</div></div>
  </div>

  <div class="gates">
    <span class="gate {"ok" if g1ok else "fail"}">{"✓" if g1ok else "✗"} Porte 1 S/R</span>
    <span class="gate {"ok" if g2ok else "fail"}">{"✓" if g2ok else "✗"} Porte 2 Figure</span>
  </div>

  <div class="tags">{tags}</div>

  {pine_html}
  {sum_html}
</div>"""

    def _visual_signal_card(self, s: dict) -> str:
        return self._build_card(s)

    def _api_signal_card(self, s: dict) -> str:
        return self._build_card(s)

    def _backtest_section(self, r) -> str:
        wr_color = "green" if r.winrate_pct >= 50 else "red"
        pnl_color= "green" if r.total_pnl_pct >= 0 else "red"
        return f"""
<div class="backtest">
  <h2>📊 Résultats Backtesting</h2>
  <div class="bt-grid">
    <div class="bt-box"><div class="val blue">{r.total_trades}</div><div class="lbl">Trades testés</div></div>
    <div class="bt-box"><div class="val {wr_color}">{r.winrate_pct:.1f}%</div><div class="lbl">Winrate</div></div>
    <div class="bt-box"><div class="val green">{r.wins}</div><div class="lbl">Gagnants</div></div>
    <div class="bt-box"><div class="val red">{r.losses}</div><div class="lbl">Perdants</div></div>
    <div class="bt-box"><div class="val blue">1:{r.avg_rr:.1f}</div><div class="lbl">RR moyen</div></div>
    <div class="bt-box"><div class="val {pnl_color}">{r.total_pnl_pct:+.2f}%</div><div class="lbl">PnL total</div></div>
  </div>
</div>"""
