"""
save_analysis.py
────────────────
Sauvegarde les résultats d'analyse visuelle en JSON.
Utilisé par Claude Code après avoir analysé un screenshot.

Usage depuis le terminal :
  python -m bot.analysis.save_analysis \\
    --pair GBPUSD --tf H1 --template Momentum \\
    --image outputs/screenshots/GBPUSD_H1.png \\
    --score 7 --direction LONG \\
    --pattern "Double Bottom W" \\
    --entry 1.2650 --sl 1.2600 --tp1 1.2750 --tp2 1.2850 \\
    --summary "Double bottom sur support fort" \\
    --gate1 "Support horizontal testé 3 fois" \\
    --gate2 "Double Bottom W clair"

Ou depuis Python :
  from bot.analysis.save_analysis import save
  save(pair="GBP/USD", tf="H1", score=7, direction="LONG", ...)
"""

import argparse
import json
import os
import sys
from datetime import datetime


ANALYSES_DIR = "outputs/analyses"


def save(
    pair: str,
    tf: str,
    score: int,
    direction: str,
    pattern: str = "",
    entry: float = 0,
    sl: float = 0,
    tp1: float = 0,
    tp2: float = 0,
    rr: float = 0,
    summary: str = "",
    gate1: str = "",
    gate2: str = "",
    template: str = "",
    image: str = "",
    warnings: list = None,
    adx: float = 0,
    rsi: float = 0,
    qqe: str = "",
    ema: str = "",
    ichimoku: str = "",
    harmonics: str = "",
    compression: bool = False,
) -> str:
    """
    Sauvegarde une analyse en JSON dans outputs/analyses/.

    Returns:
        Chemin du fichier JSON créé
    """
    os.makedirs(ANALYSES_DIR, exist_ok=True)

    # Calculer RR si pas fourni
    if rr == 0 and entry and sl and tp1 and entry != sl:
        risk = abs(entry - sl)
        if risk > 0:
            rr = round(abs(tp1 - entry) / risk, 1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pair_clean = pair.replace("/", "_")

    analysis = {
        "pair": pair,
        "timeframe": tf,
        "template": template,
        "image_path": image,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        # Score & direction
        "confluence_score": score,
        "direction": direction,
        "pattern": pattern,

        # Niveaux
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "rr_ratio": rr,

        # Gates
        "gate1_sr": gate1,
        "gate2_pattern": gate2,

        # Indicateurs
        "adx": adx,
        "rsi": rsi,
        "qqe": qqe,
        "ema": ema,
        "ichimoku": ichimoku,
        "harmonics": harmonics,
        "compression": compression,

        # Résumé
        "summary": summary,
        "warnings": warnings or [],

        # Meta
        "analysis_type": "visual",
        "analyzed_by": "claude_code",
    }

    filename = f"{pair_clean}_{tf}_{ts}.json"
    filepath = os.path.join(ANALYSES_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"  Analyse sauvegardée : {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Sauvegarde une analyse visuelle")
    parser.add_argument("--pair", "-p", required=True)
    parser.add_argument("--tf", "-t", required=True)
    parser.add_argument("--score", "-s", type=int, required=True)
    parser.add_argument("--direction", "-d", required=True, choices=["LONG", "SHORT", "NEUTRAL"])
    parser.add_argument("--pattern", default="")
    parser.add_argument("--entry", type=float, default=0)
    parser.add_argument("--sl", type=float, default=0)
    parser.add_argument("--tp1", type=float, default=0)
    parser.add_argument("--tp2", type=float, default=0)
    parser.add_argument("--rr", type=float, default=0)
    parser.add_argument("--summary", default="")
    parser.add_argument("--gate1", default="")
    parser.add_argument("--gate2", default="")
    parser.add_argument("--template", default="")
    parser.add_argument("--image", default="")
    parser.add_argument("--adx", type=float, default=0)
    parser.add_argument("--rsi", type=float, default=0)

    args = parser.parse_args()

    path = save(
        pair=args.pair, tf=args.tf, score=args.score, direction=args.direction,
        pattern=args.pattern, entry=args.entry, sl=args.sl, tp1=args.tp1,
        tp2=args.tp2, rr=args.rr, summary=args.summary, gate1=args.gate1,
        gate2=args.gate2, template=args.template, image=args.image,
        adx=args.adx, rsi=args.rsi,
    )


if __name__ == "__main__":
    main()
