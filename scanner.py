"""
scanner.py
──────────
Scanner principal du bot.
Boucle toutes les 15 minutes sur toutes les paires et timeframes.
Pipeline : Data → Détection → Validation → Entrée → Dessin → Alerte → Dashboard
"""

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
# CONFIGURATION — Modifie ici tes préférences
# ──────────────────────────────────────────────────

PAIRS = [
    # ── Majeurs Forex ─────────────────────────────────
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "USD/CHF",
    "AUD/USD",
    "USD/CAD",
    # ── Croisés Forex ─────────────────────────────────
    "EUR/GBP",
    "EUR/JPY",
    "GBP/JPY",
    # ── Matières premières ────────────────────────────
    "XAU/USD",   # Or (Gold)
    # ── Indices ───────────────────────────────────────
    "DJ30",      # Dow Jones 30 (Futures YM=F)
    "DAX",       # DAX Allemand (^GDAXI)
]

TIMEFRAMES = ["15m", "30m", "1h", "4h"]

EXCHANGE = "forex"           # "forex" = yfinance | "binance" = crypto CCXT

MIN_ADX    = 20              # ADX minimum pour valider un signal
BLOCK_HTF  = False           # Bloquer si HTF contre la tendance ?

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID",   "")


def run_scan(pairs_override=None, tfs_override=None):
    """Lance un scan complet sur toutes les paires et timeframes."""
    pairs = pairs_override if pairs_override else PAIRS
    tfs   = tfs_override   if tfs_override   else TIMEFRAMES
    logger.info("═" * 55)
    logger.info(f"🔍 SCAN DÉMARRÉ — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("═" * 55)

    # Imports ici pour éviter les erreurs au démarrage si librairies manquantes
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
        logger.error(f"❌ Import manquant : {e}")
        logger.error("👉 Lance d'abord : pip install -r requirements.txt")
        return []

    # Initialisation des modules
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
                logger.info(f"  📊 {pair} | {tf}")

                # 1. Données OHLCV
                df = feed.get_ohlcv(pair, tf, limit=300)
                if df is None or len(df) < 50:
                    logger.warning(f"     ⚠️ Données insuffisantes")
                    continue

                # 2. Indicateurs
                indicators = ind_eng.compute(df)

                # 3. Détection S/R
                sr_zones = sr_det.detect(df)

                # 4. Détection de patterns
                patterns  = pat_det.detect(df, sr_zones)
                candles   = cdl_det.detect(df, sr_zones)
                harmonics = harm_det.detect(df, sr_zones)
                compressions = comp_det.detect(df)

                all_signals = patterns + candles + harmonics + compressions

                # 5. Analyse HTF — logique sniper M15/M30 = on vérifie H1 ET H4
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

                    # Enrichir le signal avec les indicateurs
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

                    # Multi-timeframe sniper
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

                    # 6. Vérification des portes
                    gate_result = gate.check(sig)
                    if not gate_result.allowed:
                        logger.debug(f"     {gate_result.reason}")
                        continue

                    # 7. Calcul des niveaux d'entrée
                    sig["confluence"] = gate_result.reason
                    entry_result = calc.calculate(sig)
                    sig.update({
                        "entry"    : entry_result.entry,
                        "sl"       : entry_result.stop_loss,
                        "tp1"      : entry_result.tp1,
                        "tp2"      : entry_result.tp2,
                        "rr_ratio" : entry_result.rr_ratio,
                    })

                    # 8. Dessin — Pine Script + MQL4
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

                    # 9. Alerte
                    qqe_status = "✅ croisement" if sig.get("qqe_fast",0) > sig.get("qqe_slow",0) else "⚠️"
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
                logger.error(f"     ❌ Erreur {pair} {tf} : {e}", exc_info=True)

    # 10. Dashboard HTML
    dashboard.generate(active_signals)
    logger.info(f"\n✅ Scan terminé — {len(active_signals)} signaux | Dashboard: outputs/dashboard.html\n")
    return active_signals


def _resolve_pair(arg: str) -> str | None:
    """Convertit un argument CLI en paire reconnue (ex: EURUSD → EUR/USD)."""
    # Normaliser : majuscules, sans espaces
    arg = arg.upper().strip()

    # Correspondance directe (ex: "EUR/USD")
    if arg in PAIRS:
        return arg

    # Essayer d'ajouter le slash (ex: EURUSD → EUR/USD)
    for pair in PAIRS:
        if arg == pair.replace("/", ""):
            return pair

    return None


def main():
    # ── Lecture argument CLI optionnel ────────────────────────────
    single_pair = None
    if len(sys.argv) > 1:
        single_pair = _resolve_pair(sys.argv[1])
        if single_pair is None:
            print(f"\n❌ Paire inconnue : '{sys.argv[1]}'")
            print(f"   Paires disponibles : {', '.join(PAIRS)}")
            print(f"   Exemples : python scanner.py EURUSD  |  python scanner.py XAUUSD\n")
            sys.exit(1)

    pairs_to_scan = [single_pair] if single_pair else PAIRS

    print("\n" + "═"*55)
    print("  🤖 TRADING BOT ULTIMATE — DÉMARRAGE")
    print("═"*55)
    print(f"  Paires     : {', '.join(pairs_to_scan)}")
    print(f"  Timeframes : {', '.join(TIMEFRAMES)}")
    print(f"  Exchange   : {EXCHANGE}")
    if single_pair:
        print(f"  Mode       : Analyse unique (une seule paire)")
    else:
        print(f"  Scan every : 15 minutes")
    print(f"  Telegram   : {'✅' if TELEGRAM_TOKEN else '❌ Non configuré'}")
    print("═"*55 + "\n")

    # Lancer le scan
    run_scan(pairs_override=pairs_to_scan)

    # En mode analyse unique → on s'arrête là
    if single_pair:
        return

    # En mode complet → boucle toutes les 15 minutes
    schedule.every(15).minutes.do(run_scan)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
