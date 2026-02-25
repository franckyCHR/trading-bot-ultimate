"""
webapp.py
─────────
Serveur Flask pour Trading Bot Ultimate.
Accessible depuis n'importe où une fois déployé sur Railway.

Endpoints :
  GET  /                      → page principale
  POST /api/scan              → démarre un scan (background), retourne scan_id
  GET  /api/stream/<scan_id>  → SSE : logs en temps réel
  GET  /api/results/<scan_id> → JSON : signaux détectés
  GET  /api/chart             → données OHLCV pour graphique
  GET  /pine/<filename>       → sert les fichiers Pine Script
  POST /api/analyze-image     → upload screenshot → analyse visuelle
  GET  /api/analysis/<id>     → résultats d'une analyse visuelle
  GET  /api/screenshots       → liste des screenshots
  GET  /screenshots/<file>    → sert les images screenshots
"""

import os
import uuid
import json
import queue
import logging
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, Response, send_file, abort

# ── App Flask ──────────────────────────────────────────────────────────────────
app  = Flask(__name__)
PORT = int(os.environ.get("PORT", 8080))

# ── Config paires/timeframes (copiée depuis scanner.py) ───────────────────────
PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "USD/CAD",
    "EUR/GBP", "EUR/JPY", "GBP/JPY",
    "XAU/USD",
    "DJ30",
    "DAX",
]
TIMEFRAMES = ["30m", "1h", "4h"]

# ── Stockage des scans en mémoire ─────────────────────────────────────────────
SCANS: dict = {}
ANALYSES: dict = {}  # Analyses visuelles

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("WebApp")


# ══════════════════════════════════════════════════════════════════════════════
# QUEUE HANDLER — redirige les logs Python vers la Queue SSE
# ══════════════════════════════════════════════════════════════════════════════

class QueueHandler(logging.Handler):
    """Capture chaque log et le pousse dans une queue (pour SSE)."""

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord):
        try:
            self.log_queue.put_nowait(self.format(record))
        except queue.Full:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES HTML
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html", pairs=PAIRS, timeframes=TIMEFRAMES)


# ══════════════════════════════════════════════════════════════════════════════
# API — DÉMARRER UN SCAN
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/scan", methods=["POST"])
def start_scan():
    data   = request.get_json(silent=True) or {}
    pairs  = data.get("pairs", [])       or None
    tfs    = data.get("timeframes", [])  or None

    scan_id = str(uuid.uuid4())
    SCANS[scan_id] = {
        "status"    : "running",
        "signals"   : [],
        "log_queue" : queue.Queue(maxsize=500),
        "started_at": datetime.now().strftime("%H:%M:%S"),
    }

    threading.Thread(
        target = _run_scan_thread,
        args   = (scan_id, pairs, tfs),
        daemon = True,
    ).start()

    return jsonify({"scan_id": scan_id}), 202


def _run_scan_thread(scan_id: str, pairs_override, tfs_override):
    log_queue = SCANS[scan_id]["log_queue"]

    handler = QueueHandler(log_queue)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    ))
    root = logging.getLogger()
    root.addHandler(handler)

    try:
        from scanner import run_scan
        signals = run_scan(
            pairs_override = pairs_override,
            tfs_override   = tfs_override,
        )
        SCANS[scan_id]["signals"] = signals or []
        SCANS[scan_id]["status"]  = "done"

    except Exception as exc:
        logger.error(f"Erreur scan {scan_id} : {exc}", exc_info=True)
        SCANS[scan_id]["status"] = "error"
        SCANS[scan_id]["error"]  = str(exc)

    finally:
        root.removeHandler(handler)
        log_queue.put(None)


# ══════════════════════════════════════════════════════════════════════════════
# API — STREAM SSE (logs en temps réel)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/stream/<scan_id>")
def stream_logs(scan_id: str):
    if scan_id not in SCANS:
        abort(404)

    def generate():
        log_queue = SCANS[scan_id]["log_queue"]
        while True:
            try:
                msg = log_queue.get(timeout=30)
                if msg is None:
                    yield "data: __SCAN_DONE__\n\n"
                    break
                safe = msg.replace("\n", " ")
                yield f"data: {safe}\n\n"
            except queue.Empty:
                yield "data: __HEARTBEAT__\n\n"

    return Response(
        generate(),
        mimetype = "text/event-stream",
        headers  = {
            "Cache-Control"    : "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ══════════════════════════════════════════════════════════════════════════════
# API — RÉSULTATS JSON
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/results/<scan_id>")
def get_results(scan_id: str):
    if scan_id not in SCANS:
        return jsonify({"error": "scan_id inconnu"}), 404

    scan    = SCANS[scan_id]
    signals = scan.get("signals", [])

    serialized = []
    for s in signals:
        serialized.append({
            "pair"       : s.get("pair", ""),
            "timeframe"  : s.get("timeframe", ""),
            "pattern"    : s.get("pattern", ""),
            "direction"  : s.get("direction", ""),
            "entry"      : round(float(s.get("entry") or 0), 5),
            "sl"         : round(float(s.get("sl") or s.get("stop_loss") or 0), 5),
            "tp1"        : round(float(s.get("tp1") or 0), 5),
            "tp2"        : round(float(s.get("tp2") or 0), 5),
            "rr_ratio"   : s.get("rr_ratio", 0),
            "adx"        : round(float(s.get("adx") or 0), 1),
            "qqe_status" : s.get("qqe_status", ""),
            "compression": bool(s.get("compression_zone", False)),
            "htf_label"  : s.get("htf_label", ""),
            "timestamp"  : s.get("timestamp", ""),
            "pine_file"  : s.get("pine_file", ""),
            "zone_high"  : round(float(s.get("zone_high") or s.get("resistance_level") or s.get("tp2") or 0), 5),
            "zone_low"   : round(float(s.get("zone_low")  or s.get("support_level")   or s.get("sl")  or 0), 5),
            "confluence" : s.get("confluence", ""),
            "analysis_type": s.get("analysis_type", "api"),
            "confluence_score": s.get("confluence_score", 0),
        })

    return jsonify({
        "scan_id"   : scan_id,
        "status"    : scan.get("status", "unknown"),
        "count"     : len(serialized),
        "signals"   : serialized,
        "started_at": scan.get("started_at", ""),
        "error"     : scan.get("error", ""),
    })


# ══════════════════════════════════════════════════════════════════════════════
# API — DONNÉES OHLCV POUR GRAPHIQUE
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/chart")
def get_chart_data():
    pair      = request.args.get("pair", "EUR/USD")
    timeframe = request.args.get("timeframe", "1h")

    from bot.data.market_feed import MarketFeed
    feed = MarketFeed(exchange_id="forex")
    df   = feed.get_ohlcv(pair, timeframe, limit=200)

    if df is None or df.empty:
        return jsonify({"error": "Données indisponibles"}), 404

    candles = []
    for _, row in df.iterrows():
        ts = row["timestamp"]
        if hasattr(ts, "timestamp"):
            t = int(ts.timestamp())
        else:
            import pandas as pd
            t = int(pd.Timestamp(ts).timestamp())
        candles.append({
            "time" : t,
            "open" : round(float(row["open"]),  5),
            "high" : round(float(row["high"]),  5),
            "low"  : round(float(row["low"]),   5),
            "close": round(float(row["close"]), 5),
        })

    return jsonify({"pair": pair, "timeframe": timeframe, "candles": candles})


# ══════════════════════════════════════════════════════════════════════════════
# API — ANALYSE VISUELLE (upload screenshot)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/analyze-image", methods=["POST"])
def analyze_image():
    """
    Upload un screenshot → sauvegarde dans outputs/screenshots/.
    L'analyse se fait ensuite dans Claude Code (pas d'API externe).
    """
    if "file" not in request.files:
        return jsonify({"error": "Pas de fichier uploadé"}), 400

    file = request.files["file"]
    pair = request.form.get("pair", "EUR/USD")
    timeframe = request.form.get("timeframe", "H1")
    template = request.form.get("template", "Momentum")

    if not file.filename:
        return jsonify({"error": "Fichier vide"}), 400

    # Sauvegarder l'image
    os.makedirs("outputs/screenshots", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pair_clean = pair.replace("/", "_")
    ext = Path(file.filename).suffix or ".png"
    filename = f"{pair_clean}_{timeframe}_{template}_{ts}{ext}"
    filepath = os.path.join("outputs/screenshots", filename)
    file.save(filepath)

    # Enregistrer dans la liste des analyses
    analysis_id = str(uuid.uuid4())
    ANALYSES[analysis_id] = {
        "status": "saved",
        "image": filename,
        "filepath": filepath,
        "pair": pair,
        "timeframe": timeframe,
        "template": template,
        "saved_at": datetime.now().strftime("%H:%M:%S"),
    }

    logger.info(f"Screenshot uploadé : {filename}")

    return jsonify({
        "analysis_id": analysis_id,
        "image": filename,
        "message": f"Screenshot sauvegardé. Pour analyser, ouvre Claude Code et dis : Analyse {filepath}",
    }), 201


@app.route("/api/analysis/<analysis_id>")
def get_analysis(analysis_id: str):
    """Retourne les infos d'un screenshot uploadé."""
    if analysis_id not in ANALYSES:
        return jsonify({"error": "analysis_id inconnu"}), 404

    a = ANALYSES[analysis_id]
    return jsonify({
        "analysis_id": analysis_id,
        "status": a.get("status", "saved"),
        "image": a.get("image", ""),
        "filepath": a.get("filepath", ""),
        "pair": a.get("pair", ""),
        "timeframe": a.get("timeframe", ""),
        "template": a.get("template", ""),
        "saved_at": a.get("saved_at", ""),
        "message": "Analyse via Claude Code : ouvre le terminal et demande l'analyse de ce screenshot",
    })


@app.route("/api/analyses")
def list_analyses():
    """Liste toutes les analyses visuelles sauvegardées en JSON."""
    analyses_dir = Path("outputs/analyses")
    if not analyses_dir.exists():
        return jsonify({"analyses": []})

    results = []
    for f in sorted(analyses_dir.glob("*.json"), reverse=True):
        try:
            with open(f) as fh:
                data = json.load(fh)
            data["_filename"] = f.name
            results.append(data)
        except (json.JSONDecodeError, OSError):
            continue

    return jsonify({"analyses": results, "count": len(results)})


@app.route("/api/analyses/clear", methods=["POST"])
def clear_analyses():
    """Supprime toutes les analyses (reset)."""
    analyses_dir = Path("outputs/analyses")
    count = 0
    if analyses_dir.exists():
        for f in analyses_dir.glob("*.json"):
            f.unlink()
            count += 1
    return jsonify({"deleted": count})


@app.route("/api/screenshots")
def list_screenshots():
    """Liste les screenshots disponibles."""
    screenshots_dir = Path("outputs/screenshots")
    if not screenshots_dir.exists():
        return jsonify({"screenshots": []})

    files = []
    for f in sorted(screenshots_dir.glob("*.png"), reverse=True):
        files.append({
            "filename": f.name,
            "size_kb": round(f.stat().st_size / 1024, 1),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    # Also include jpg/jpeg
    for f in sorted(screenshots_dir.glob("*.jp*g"), reverse=True):
        files.append({
            "filename": f.name,
            "size_kb": round(f.stat().st_size / 1024, 1),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        })

    return jsonify({"screenshots": files})


@app.route("/screenshots/<path:filename>")
def serve_screenshot(filename: str):
    """Sert les fichiers screenshots."""
    safe_name = os.path.basename(filename)
    full_path = os.path.join("outputs", "screenshots", safe_name)
    if not os.path.isfile(full_path):
        abort(404)
    return send_file(full_path)


# ══════════════════════════════════════════════════════════════════════════════
# FICHIERS PINE SCRIPT
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/pine/<path:filepath>")
def serve_pine(filepath: str):
    safe_name = os.path.basename(filepath)
    full_path = os.path.join("outputs", "tradingview", safe_name)
    if not os.path.isfile(full_path):
        abort(404)
    return send_file(full_path, mimetype="text/plain", download_name=safe_name)


# ══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    os.makedirs("outputs/tradingview", exist_ok=True)
    os.makedirs("outputs/mt4",        exist_ok=True)
    os.makedirs("outputs/screenshots", exist_ok=True)
    os.makedirs("outputs/analyses",   exist_ok=True)

    print(f"\n{'='*50}")
    print(f"  Trading Bot Web — http://localhost:{PORT}")
    print(f"  (Si erreur port, essaie : PORT=9000 python webapp.py)")
    print(f"{'='*50}\n")

    app.run(host="0.0.0.0", port=PORT, threaded=True, debug=False)
