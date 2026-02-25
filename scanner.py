"""
scanner.py
──────────
Scanner principal du bot.
3 modes :
  - api-scan  : boucle yfinance toutes les 15 min (existant)
  - manual    : enregistre un screenshot → prêt pour analyse Claude Code
  - semi-auto : capture écran Mac → circuit templates x TF → prêt pour Claude Code
  - batch     : prépare tous les screenshots d'un dossier pour analyse

L'analyse visuelle se fait directement dans Claude Code (pas d'API externe).

Usage :
  python scanner.py                                         Scan API toutes paires
  python scanner.py EURUSD                                  Scan API une paire
  python scanner.py --mode manual --image sc.png --pair GBPUSD --tf H1
  python scanner.py --mode semi-auto --pair GBPUSD
  python scanner.py --mode batch --pair GBPUSD              Analyse toutes les captures
"""

import argparse
import json
import os
import sys
import time
import logging
import schedule
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers= [
        logging.StreamHandler(),
        logging.FileHandler("outputs/bot.log"),
    ]
)
logger = logging.getLogger("Scanner")

# ──────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────

PAIRS = [
    # ── Majeurs Forex ─────────────────────────────────
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "USD/CHF",
    "AUD/USD",
    "USD/CAD",
    "NZD/USD",
    # ── Mineurs (croisés sans USD) ────────────────────
    "EUR/GBP",
    "EUR/JPY",
    "EUR/CHF",
    "EUR/AUD",
    "EUR/CAD",
    "EUR/NZD",
    "GBP/JPY",
    "GBP/CHF",
    "GBP/AUD",
    "GBP/CAD",
    "GBP/NZD",
    "AUD/JPY",
    "AUD/CAD",
    "AUD/NZD",
    "NZD/JPY",
    "CAD/JPY",
    "CHF/JPY",
    # ── Matières premières ────────────────────────────
    "XAU/USD",   # Or (Gold)
    "XAG/USD",   # Argent (Silver)
    # ── Indices ───────────────────────────────────────
    "DJ30",      # Dow Jones 30 (Futures YM=F)
    "DAX",       # DAX Allemand (^GDAXI)
    "NAS100",    # Nasdaq 100
]

TIMEFRAMES = ["15m", "30m", "1h", "4h"]

EXCHANGE = "forex"           # "forex" = yfinance | "binance" = crypto CCXT

MIN_ADX    = 20              # ADX minimum pour valider un signal
BLOCK_HTF  = False           # Bloquer si HTF contre la tendance ?

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID",   "")


# ══════════════════════════════════════════════════════════════════════
# MODE 1 : MANUEL — Enregistre un screenshot
# ══════════════════════════════════════════════════════════════════════

def run_manual(image_path: str, pair: str, timeframe: str, template: str = "Momentum"):
    """
    Enregistre un screenshot et le prépare pour analyse dans Claude Code.
    """
    from bot.analysis.vision_client import VisionAnalyzer

    print("\n" + "=" * 55)
    print("  ANALYSE VISUELLE — Mode Manuel")
    print("=" * 55)

    analyzer = VisionAnalyzer()
    entry = analyzer.register_image(image_path, pair, timeframe, template)

    print(f"  Image    : {entry['filename']}")
    print(f"  Paire    : {pair}")
    print(f"  TF       : {timeframe}")
    print(f"  Template : {template}")
    print(f"  Taille   : {entry['size_kb']} KB")
    print("=" * 55)
    print()
    print("  Screenshot enregistré avec succes !")
    print()
    print("  Pour l'analyser, ouvre Claude Code et dis :")
    print(f"  → Analyse {entry['image_path']}")
    print(f"    C'est {pair} en {timeframe}, template {template}")
    print()


# ══════════════════════════════════════════════════════════════════════
# MODE 2 : SEMI-AUTO — Capture écran circuit complet
# ══════════════════════════════════════════════════════════════════════

def run_semi_auto(pair: str, templates: list[str] = None, timeframes: list[str] = None):
    """
    Capture écran Mac → circuit templates x TF → prêt pour Claude Code.
    """
    from bot.analysis.screenshot_capture import ScreenshotCapture
    from bot.analysis.vision_client import VisionAnalyzer

    templates = templates or ["Momentum", "RSI", "EXTREM_MONEY", "Harmoniques"]
    timeframes = timeframes or ["M30", "H1", "H4", "D1"]

    capture = ScreenshotCapture()
    analyzer = VisionAnalyzer()

    # Circuit de capture interactif
    images = capture.capture_full_circuit(pair, templates, timeframes)

    if not images:
        print("  Aucune image capturée. Abandon.")
        return

    # Enregistrer les images
    registered = []
    for img in images:
        entry = analyzer.register_image(
            img["image_path"], img["pair"], img["timeframe"], img["template"]
        )
        registered.append(entry)

    # Résumé
    analyzer.print_ready_summary(registered)


# ══════════════════════════════════════════════════════════════════════
# MODE 3 : BATCH — Liste les screenshots prêts
# ══════════════════════════════════════════════════════════════════════

def run_batch(pair: str = None):
    """
    Liste tous les screenshots disponibles pour une paire.
    """
    from bot.analysis.vision_client import VisionAnalyzer

    analyzer = VisionAnalyzer()
    screenshots = analyzer.list_screenshots(pair)

    print("\n" + "=" * 55)
    print("  SCREENSHOTS DISPONIBLES")
    print("=" * 55)

    if not screenshots:
        print("  Aucun screenshot trouvé dans outputs/screenshots/")
        print("  → Utilise --mode semi-auto pour capturer")
        print("  → Ou glisse des images dans outputs/screenshots/")
        return

    for s in screenshots:
        print(f"  {s.get('pair', '?'):10s} | {s.get('timeframe', '?'):4s} | "
              f"{s['size_kb']:7.1f} KB | {s['modified']} | {s['filename']}")

    print("=" * 55)
    print(f"  Total : {len(screenshots)} screenshot(s)")
    print()
    print("  Pour analyser dans Claude Code :")
    if pair:
        pair_clean = pair.replace("/", "_")
        print(f"  → Analyse tous les screenshots {pair} dans outputs/screenshots/")
    else:
        print(f"  → Analyse les screenshots dans outputs/screenshots/")
    print()


# ══════════════════════════════════════════════════════════════════════
# MODE 4 : API SCAN (existant — inchangé)
# ══════════════════════════════════════════════════════════════════════

def run_scan(pairs_override=None, tfs_override=None):
    """Lance un scan complet sur toutes les paires et timeframes."""
    pairs = pairs_override if pairs_override else PAIRS
    tfs   = tfs_override   if tfs_override   else TIMEFRAMES
    logger.info("=" * 55)
    logger.info(f"SCAN DÉMARRÉ — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("=" * 55)

    try:
        from bot.data.market_feed        import MarketFeed
        from bot.detection.sr_detector   import SRDetector
        from bot.detection.pattern_detector import PatternDetector
        from bot.detection.candle_detector  import CandleDetector
        from bot.detection.harmonic_detector import HarmonicDetector
        from bot.detection.compression_detector import CompressionDetector
        from bot.detection.indicator_engine    import IndicatorEngine
        from bot.detection.multi_timeframe     import MultiTimeframeAnalyzer
        from bot.validation.gate_checker       import GateChecker
        from bot.validation.adx_validator      import ADXValidator
        from bot.validation.qqe_validator      import QQEValidator
        from bot.entries.entry_calculator      import EntryCalculator
        from bot.drawers                        import registry as drawer_registry
        from bot.output.alert_manager          import AlertManager, Alert
        from bot.output.dashboard_generator    import DashboardGenerator
        from bot.output.backtester             import Backtester
    except ImportError as e:
        logger.error(f"Import manquant : {e}")
        logger.error("Lance d'abord : pip install -r requirements.txt")
        return []

    feed        = MarketFeed(exchange_id=EXCHANGE)
    sr_det      = SRDetector()
    pat_det     = PatternDetector()
    cdl_det     = CandleDetector()
    harm_det    = HarmonicDetector()
    comp_det    = CompressionDetector()
    ind_eng     = IndicatorEngine()
    mtf         = MultiTimeframeAnalyzer(block_counter_trend=BLOCK_HTF)
    gate        = GateChecker()
    adx_val     = ADXValidator(min_adx=MIN_ADX)
    qqe_val     = QQEValidator()
    calc        = EntryCalculator()
    alerts      = AlertManager(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    dashboard   = DashboardGenerator()

    active_signals = []

    for pair in pairs:
        for tf in tfs:
            try:
                logger.info(f"  {pair} | {tf}")

                df = feed.get_ohlcv(pair, tf, limit=300)
                if df is None or len(df) < 50:
                    logger.warning(f"     Données insuffisantes")
                    continue

                indicators = ind_eng.compute(df)
                sr_zones = sr_det.detect(df)

                patterns  = pat_det.detect(df, sr_zones)
                candles   = cdl_det.detect(df, sr_zones)
                harmonics = harm_det.detect(df, sr_zones)
                compressions = comp_det.detect(df)

                all_signals = patterns + candles + harmonics + compressions

                HTF_MAP = {
                    "15m": ("1h",  "4h"),
                    "30m": ("1h",  "4h"),
                    "1h" : ("4h",  "1d"),
                    "4h" : ("1d",  None),
                }
                htf1_tf, htf2_tf = HTF_MAP.get(tf, ("4h", None))

                df_htf1    = feed.get_ohlcv(pair, htf1_tf, limit=100)
                htf1_trend = mtf.get_trend_from_data(df_htf1) if df_htf1 is not None else "NEUTRE"
                htf1_sr    = sr_det.detect(df_htf1) if df_htf1 is not None else []

                df_htf2    = feed.get_ohlcv(pair, htf2_tf, limit=100) if htf2_tf else None
                htf2_trend = mtf.get_trend_from_data(df_htf2) if df_htf2 is not None else "NEUTRE"

                for sig in all_signals:
                    sig.update({
                        "pair"       : pair,
                        "timeframe"  : tf,
                        "adx"        : indicators.get("adx", 0),
                        "adx_rising" : indicators.get("adx_rising", False),
                        "di_plus"    : indicators.get("di_plus", 0),
                        "di_minus"   : indicators.get("di_minus", 0),
                        "qqe_fast"   : indicators.get("qqe_fast", 0),
                        "qqe_slow"   : indicators.get("qqe_slow", 0),
                        "qqe_fast_prev": indicators.get("qqe_fast_prev", 0),
                        "qqe_slow_prev": indicators.get("qqe_slow_prev", 0),
                        "qqe_cross_bars_ago": indicators.get("qqe_cross_bars_ago", 99),
                        "sr_zone"    : bool(sr_zones),
                        "sr_strength": max((z.get("strength", 0) for z in sr_zones), default=0),
                        "timestamp"  : datetime.now().strftime("%H:%M"),
                        "htf1_tf"    : htf1_tf,
                        "htf1_trend" : htf1_trend,
                        "htf2_tf"    : htf2_tf,
                        "htf2_trend" : htf2_trend,
                    })

                    htf_result = mtf.analyze_sniper(
                        signal_tf  = tf,
                        signal_dir = sig.get("direction", "LONG"),
                        htf1_data  = {
                            "trend"     : htf1_trend,
                            "tf"        : htf1_tf,
                            "sr_levels" : [z.get("price", 0) for z in htf1_sr],
                            "price"     : df["close"].iloc[-1],
                        },
                        htf2_data  = {
                            "trend" : htf2_trend,
                            "tf"    : htf2_tf,
                        } if htf2_tf else None,
                    )
                    sig["htf_label"]   = htf_result.label
                    sig["htf_aligned"] = htf_result.aligned
                    sig["htf_blocked"] = htf_result.blocked

                    gate_result = gate.check(sig)
                    if not gate_result.allowed:
                        logger.debug(f"     {gate_result.reason}")
                        continue

                    sig["confluence"] = gate_result.reason
                    entry_result = calc.calculate(sig)
                    sig.update({
                        "entry"    : entry_result.entry,
                        "sl"       : entry_result.stop_loss,
                        "tp1"      : entry_result.tp1,
                        "tp2"      : entry_result.tp2,
                        "rr_ratio" : entry_result.rr_ratio,
                    })

                    drawing = drawer_registry.draw(sig)
                    pine_path = f"outputs/tradingview/{pair.replace('/','_')}_{tf}_{sig.get('pattern','sig')}.pine"
                    mql4_path = f"outputs/mt4/{pair.replace('/','_')}_{tf}_{sig.get('pattern','sig')}.mql4"
                    os.makedirs("outputs/tradingview", exist_ok=True)
                    os.makedirs("outputs/mt4", exist_ok=True)
                    with open(pine_path, "w") as f:
                        f.write(drawing.pine_script)
                    with open(mql4_path, "w") as f:
                        f.write(drawing.mql4_script)
                    sig["pine_file"] = pine_path

                    qqe_status = "croisement" if sig.get("qqe_fast",0) > sig.get("qqe_slow",0) else ""
                    alert = Alert(
                        pair        = pair,
                        timeframe   = tf,
                        pattern     = sig.get("pattern",""),
                        direction   = sig.get("direction",""),
                        entry       = entry_result.entry,
                        sl          = entry_result.stop_loss,
                        tp1         = entry_result.tp1,
                        tp2         = entry_result.tp2,
                        rr_ratio    = entry_result.rr_ratio,
                        confluence  = gate_result.reason,
                        adx         = round(sig.get("adx",0), 1),
                        qqe_status  = qqe_status,
                        compression = sig.get("compression_zone", False),
                        pine_file   = pine_path,
                    )
                    alerts.send(alert)
                    if TELEGRAM_TOKEN:
                        alerts.send_pine_script(pair, tf, pine_path)

                    sig["qqe_status"] = qqe_status
                    active_signals.append(sig)

            except Exception as e:
                logger.error(f"     Erreur {pair} {tf} : {e}", exc_info=True)

    dashboard.generate(active_signals)
    logger.info(f"\nScan terminé — {len(active_signals)} signaux | Dashboard: outputs/dashboard.html\n")
    return active_signals


def _resolve_pair(arg: str) -> str | None:
    """Convertit un argument CLI en paire reconnue (ex: EURUSD -> EUR/USD)."""
    arg = arg.upper().strip()
    if arg in PAIRS:
        return arg
    for pair in PAIRS:
        if arg == pair.replace("/", ""):
            return pair
    return None


# ══════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE — ARGPARSE
# ══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Trading Bot Ultimate — Scanner multi-mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python scanner.py                                         Scan API toutes paires
  python scanner.py EURUSD                                  Scan API une paire
  python scanner.py --mode manual --image sc.png --pair GBPUSD --tf H1
  python scanner.py --mode semi-auto --pair GBPUSD          Capture circuit MT4
  python scanner.py --mode batch --pair GBPUSD              Liste screenshots prêts
        """
    )

    parser.add_argument("legacy_pair", nargs="?", default=None,
                        help="Paire pour scan API (mode legacy, ex: EURUSD)")
    parser.add_argument("--mode", "-m",
                        choices=["manual", "semi-auto", "batch", "api-scan"],
                        default=None,
                        help="Mode d'analyse")
    parser.add_argument("--image", "-i", type=str,
                        help="Chemin vers le screenshot (mode manual)")
    parser.add_argument("--pair", "-p", type=str,
                        help="Paire à analyser (ex: GBPUSD, EUR/USD)")
    parser.add_argument("--tf", "-t", type=str, default="H1",
                        help="Timeframe (ex: M30, H1, H4, D1)")
    parser.add_argument("--template", type=str, default="Momentum",
                        choices=["Momentum", "RSI", "EXTREM_MONEY", "Harmoniques"],
                        help="Template MT4 (mode manual)")

    args = parser.parse_args()

    # Déterminer le mode
    mode = args.mode
    if mode is None:
        if args.image:
            mode = "manual"
        elif args.legacy_pair:
            mode = "api-scan"
        else:
            mode = "api-scan"

    # ── MODE MANUAL ─────────────────────────────────────
    if mode == "manual":
        if not args.image:
            parser.error("--image est requis en mode manual")
        if not args.pair:
            parser.error("--pair est requis en mode manual")

        pair = _resolve_pair(args.pair)
        if pair is None:
            pair = args.pair.upper()
            if "/" not in pair and len(pair) == 6:
                pair = pair[:3] + "/" + pair[3:]

        run_manual(args.image, pair, args.tf.upper(), args.template)
        return

    # ── MODE SEMI-AUTO ──────────────────────────────────
    if mode == "semi-auto":
        if not args.pair:
            parser.error("--pair est requis en mode semi-auto")

        pair = _resolve_pair(args.pair)
        if pair is None:
            pair = args.pair.upper()
            if "/" not in pair and len(pair) == 6:
                pair = pair[:3] + "/" + pair[3:]

        run_semi_auto(pair)
        return

    # ── MODE BATCH ──────────────────────────────────────
    if mode == "batch":
        pair = None
        if args.pair:
            pair = _resolve_pair(args.pair)
            if pair is None:
                pair = args.pair.upper()
                if "/" not in pair and len(pair) == 6:
                    pair = pair[:3] + "/" + pair[3:]
        run_batch(pair)
        return

    # ── MODE API-SCAN (existant) ────────────────────────
    single_pair = None
    pair_arg = args.legacy_pair or args.pair

    if pair_arg:
        single_pair = _resolve_pair(pair_arg)
        if single_pair is None:
            print(f"\nPaire inconnue : '{pair_arg}'")
            print(f"   Paires disponibles : {', '.join(PAIRS)}")
            sys.exit(1)

    pairs_to_scan = [single_pair] if single_pair else PAIRS

    print("\n" + "=" * 55)
    print("  TRADING BOT ULTIMATE — DÉMARRAGE")
    print("=" * 55)
    print(f"  Paires     : {', '.join(pairs_to_scan)}")
    print(f"  Timeframes : {', '.join(TIMEFRAMES)}")
    print(f"  Exchange   : {EXCHANGE}")
    if single_pair:
        print(f"  Mode       : Analyse unique")
    else:
        print(f"  Scan every : 15 minutes")
    print(f"  Telegram   : {'Activé' if TELEGRAM_TOKEN else 'Non configuré'}")
    print("=" * 55 + "\n")

    run_scan(pairs_override=pairs_to_scan)

    if single_pair:
        return

    schedule.every(15).minutes.do(run_scan)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
