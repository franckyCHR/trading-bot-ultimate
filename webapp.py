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
  GET  /pine/<filename>       → sert les fichiers Pine Script
"""

import os
import uuid
import queue
import logging
import threading
from datetime import datetime

from flask import Flask, render_template, request, jsonify, Response, send_file, abort

# ── App Flask ──────────────────────────────────────────────────────────────────
app  = Flask(__name__)
PORT = int(os.environ.get("PORT", 8080))

# ── Config paires/timeframes (copiée depuis scanner.py) ───────────────────────
# Défini ici pour éviter d'importer scanner.py au démarrage (évite erreurs d'import)
PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "USD/CAD",
    "EUR/GBP", "EUR/JPY", "GBP/JPY",
    "XAU/USD",
    "DJ30",
    "DAX",
]
TIMEFRAMES = ["30m", "1h", "4h"]

# ── Stockage des scans en mémoire ─────────────────────────────────────────────
# { scan_id: { "status": str, "signals": list, "log_queue": Queue, "started_at": str } }
SCANS: dict = {}

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
            pass  # Ne jamais bloquer le scanner pour un log


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
    """
    Démarre un scan en arrière-plan.
    Body JSON : { "pairs": ["EUR/USD"], "timeframes": ["1h", "4h"] }
    Retourne  : { "scan_id": "..." }
    """
    data   = request.get_json(silent=True) or {}
    pairs  = data.get("pairs", [])       or None   # None = toutes les paires
    tfs    = data.get("timeframes", [])  or None   # None = tous les TF par défaut

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
    """Thread secondaire : lance le scan et capture les logs."""
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
        log_queue.put(None)   # sentinelle : fin du stream SSE


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
                if msg is None:                  # sentinelle → scan terminé
                    yield "data: __SCAN_DONE__\n\n"
                    break
                safe = msg.replace("\n", " ")    # SSE n'accepte pas les \n dans data
                yield f"data: {safe}\n\n"
            except queue.Empty:
                yield "data: __HEARTBEAT__\n\n"  # keepalive

    return Response(
        generate(),
        mimetype = "text/event-stream",
        headers  = {
            "Cache-Control"    : "no-cache",
            "X-Accel-Buffering": "no",           # désactive le buffering Nginx
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
# FICHIERS PINE SCRIPT
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/pine/<path:filepath>")
def serve_pine(filepath: str):
    # Sécurité : empêcher le path traversal
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

    print(f"\n{'═'*50}")
    print(f"  🌐 Trading Bot Web — http://localhost:{PORT}")
    print(f"  (Si erreur port, essaie : PORT=9000 python webapp.py)")
    print(f"{'═'*50}\n")

    app.run(host="0.0.0.0", port=PORT, threaded=True, debug=False)
