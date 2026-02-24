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

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="60">
<title>🤖 Trading Bot Dashboard</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0d1117; color: #e6edf3;
    font-family: 'Consolas', monospace;
    padding: 20px;
  }}
  .header {{
    text-align: center; padding: 20px 0;
    border-bottom: 1px solid #30363d; margin-bottom: 24px;
  }}
  .header h1 {{ font-size: 28px; color: #58a6ff; }}
  .header .time {{ color: #8b949e; font-size: 13px; margin-top: 6px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 16px; }}
  .card {{
    background: #161b22; border-radius: 10px;
    border: 1px solid #30363d; padding: 18px;
    transition: transform 0.2s;
  }}
  .card:hover {{ transform: translateY(-2px); border-color: #58a6ff; }}
  .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }}
  .pattern {{ font-size: 16px; font-weight: bold; color: #f0f6fc; }}
  .pair {{ color: #8b949e; font-size: 13px; }}
  .direction-long  {{ background: #1a3a1a; color: #3fb950; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
  .direction-short {{ background: #3a1a1a; color: #f85149; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
  .prices {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 12px 0; }}
  .price-box {{ background: #0d1117; border-radius: 6px; padding: 10px; text-align: center; }}
  .price-box .label {{ font-size: 11px; color: #8b949e; margin-bottom: 4px; }}
  .price-box .value {{ font-size: 15px; font-weight: bold; }}
  .entry  .value {{ color: #58a6ff; }}
  .sl     .value {{ color: #f85149; }}
  .tp1    .value {{ color: #e3b341; }}
  .tp2    .value {{ color: #3fb950; }}
  .tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }}
  .tag {{ font-size: 11px; padding: 3px 8px; border-radius: 10px; }}
  .tag-sr          {{ background: #1f3a5f; color: #79c0ff; }}
  .tag-adx         {{ background: #1f3a2f; color: #56d364; }}
  .tag-qqe         {{ background: #2d2a1f; color: #e3b341; }}
  .tag-compression {{ background: #3a2a1f; color: #ffa657; }}
  .tag-htf         {{ background: #2a1f3a; color: #bc8cff; }}
  .tag-rr          {{ background: #1f2a3a; color: #58a6ff; }}
  .pine-link {{ margin-top: 12px; display: block; color: #58a6ff; font-size: 12px; text-decoration: none; }}
  .pine-link:hover {{ text-decoration: underline; }}
  .empty {{ text-align: center; color: #8b949e; padding: 80px 20px; font-size: 16px; }}
  .stats-bar {{
    display: flex; gap: 20px; justify-content: center;
    background: #161b22; border: 1px solid #30363d;
    border-radius: 10px; padding: 16px; margin-bottom: 24px;
    flex-wrap: wrap;
  }}
  .stat {{ text-align: center; }}
  .stat .n {{ font-size: 24px; font-weight: bold; color: #58a6ff; }}
  .stat .l {{ font-size: 12px; color: #8b949e; }}
  .backtest {{
    background: #161b22; border: 1px solid #30363d;
    border-radius: 10px; padding: 18px; margin-top: 30px;
  }}
  .backtest h2 {{ color: #58a6ff; margin-bottom: 14px; }}
  .bt-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }}
  .bt-box {{ background: #0d1117; border-radius: 6px; padding: 12px; text-align: center; }}
  .bt-box .val {{ font-size: 22px; font-weight: bold; }}
  .bt-box .lbl {{ font-size: 11px; color: #8b949e; margin-top: 4px; }}
  .green {{ color: #3fb950; }} .red {{ color: #f85149; }} .blue {{ color: #58a6ff; }}
</style>
</head>
<body>

<div class="header">
  <h1>🤖 Trading Bot — Dashboard</h1>
  <div class="time">Dernière mise à jour : {now} &nbsp;|&nbsp; Rafraîchi toutes les 60s</div>
</div>

<div class="stats-bar">
  <div class="stat"><div class="n">{len(signals)}</div><div class="l">Signaux actifs</div></div>
  <div class="stat"><div class="n">{sum(1 for s in signals if s.get('direction')=='LONG')}</div><div class="l">Long</div></div>
  <div class="stat"><div class="n">{sum(1 for s in signals if s.get('direction')=='SHORT')}</div><div class="l">Short</div></div>
  <div class="stat"><div class="n">{sum(1 for s in signals if s.get('compression_zone'))}</div><div class="l">Compression</div></div>
</div>

<div class="grid">
{signal_cards if signals else '<div class="empty">⏳ Aucun signal détecté — Scanner en cours...</div>'}
</div>

{backtest_html}

</body></html>"""

    def _signal_card(self, s: dict) -> str:
        direction  = s.get("direction", "LONG")
        pattern    = s.get("pattern", "—")
        pair       = s.get("pair", "—")
        tf         = s.get("timeframe", "—")
        entry      = s.get("entry", 0)
        sl         = s.get("sl") or s.get("stop_loss", 0)
        tp1        = s.get("tp1", 0)
        tp2        = s.get("tp2", 0)
        rr         = s.get("rr_ratio", 0)
        adx        = s.get("adx", 0)
        compression= s.get("compression_zone", False)
        pine_file  = s.get("pine_file", "")
        htf_label  = s.get("htf_label", "")
        qqe_status = s.get("qqe_status", "")
        timestamp  = s.get("timestamp", "")

        dir_class = "direction-long" if direction == "LONG" else "direction-short"
        dir_emoji = "⬆️ LONG" if direction == "LONG" else "⬇️ SHORT"

        tags = f'<span class="tag tag-sr">📍 S/R</span>'
        if adx >= 25:
            tags += f'<span class="tag tag-adx">ADX {round(adx,0)} ✅</span>'
        elif adx >= 20:
            tags += f'<span class="tag tag-adx">ADX {round(adx,0)} ⚠️</span>'
        if "✅" in qqe_status:
            tags += f'<span class="tag tag-qqe">QQE ✅</span>'
        if compression:
            tags += f'<span class="tag tag-compression">🔥 Compression</span>'
        if htf_label:
            tags += f'<span class="tag tag-htf">HTF: {htf_label[:20]}</span>'
        tags += f'<span class="tag tag-rr">RR 1:{rr}</span>'

        pine_html = f'<a class="pine-link" href="{pine_file}" target="_blank">📄 Ouvrir Pine Script</a>' if pine_file else ""

        return f"""
<div class="card">
  <div class="card-header">
    <div>
      <div class="pattern">{'🔥 ' if compression else ''}{pattern}</div>
      <div class="pair">{pair} | {tf} | {timestamp}</div>
    </div>
    <span class="{dir_class}">{dir_emoji}</span>
  </div>
  <div class="prices">
    <div class="price-box entry"><div class="label">⬆️/⬇️ ENTRÉE</div><div class="value">{entry:,.4f}</div></div>
    <div class="price-box sl"><div class="label">🔴 SL</div><div class="value">{sl:,.4f}</div></div>
    <div class="price-box tp1"><div class="label">🟠 TP1</div><div class="value">{tp1:,.4f}</div></div>
    <div class="price-box tp2"><div class="label">🟢 TP2</div><div class="value">{tp2:,.4f}</div></div>
  </div>
  <div class="tags">{tags}</div>
  {pine_html}
</div>"""

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
