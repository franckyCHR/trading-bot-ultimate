"""
alert_manager.py
────────────────
Gestion des alertes : console + Telegram.
Chaque signal valide génère une alerte formatée
avec le label complet (figure, prix, SL, TP).
"""

import os
import json
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

logger = logging.getLogger("AlertManager")


@dataclass
class Alert:
    pair        : str
    timeframe   : str
    pattern     : str
    direction   : str
    entry       : float
    sl          : float
    tp1         : float
    tp2         : float
    rr_ratio    : float
    confluence  : str
    adx         : float
    qqe_status  : str
    compression : bool
    timestamp   : str = ""
    pine_file   : str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")


class AlertManager:

    def __init__(self,
                 telegram_token: Optional[str] = None,
                 telegram_chat_id: Optional[str] = None):

        # Telegram — récupère depuis les variables d'environnement si pas fourni
        self.tg_token   = telegram_token   or os.getenv("TELEGRAM_BOT_TOKEN")
        self.tg_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.tg_enabled = bool(self.tg_token and self.tg_chat_id and REQUESTS_OK)

        if self.tg_enabled:
            logger.info("✅ Telegram activé")
        else:
            logger.info("ℹ️ Telegram désactivé — alertes console uniquement")

    # ──────────────────────────────────────────────────────────────
    # ENVOI D'ALERTE
    # ──────────────────────────────────────────────────────────────

    def send(self, alert: Alert):
        """Envoie l'alerte sur tous les canaux configurés."""
        self._console(alert)
        if self.tg_enabled:
            self._telegram(alert)
        self._save_log(alert)

    # ──────────────────────────────────────────────────────────────
    # CONSOLE
    # ──────────────────────────────────────────────────────────────

    def _console(self, a: Alert):
        emoji = "⬆️" if a.direction == "LONG" else "⬇️"
        comp  = " 🔥 COMPRESSION" if a.compression else ""
        print("\n" + "═"*55)
        print(f"  {emoji} {a.pattern} | {a.pair} | {a.timeframe}{comp}")
        print(f"  {a.timestamp}")
        print("─"*55)
        print(f"  📍 ENTRÉE  : {a.entry:,.4f}")
        print(f"  🔴 SL      : {a.sl:,.4f}")
        print(f"  🟠 TP1     : {a.tp1:,.4f}")
        print(f"  🟢 TP2     : {a.tp2:,.4f}   (RR 1:{a.rr_ratio})")
        print("─"*55)
        print(f"  {a.confluence}")
        print(f"  ADX: {a.adx}  |  QQE: {a.qqe_status}")
        if a.pine_file:
            print(f"  📄 Pine Script : {a.pine_file}")
        print("═"*55 + "\n")

    # ──────────────────────────────────────────────────────────────
    # TELEGRAM
    # ──────────────────────────────────────────────────────────────

    def _telegram(self, a: Alert):
        emoji   = "⬆️" if a.direction == "LONG" else "⬇️"
        comp    = "\n🔥 *COMPRESSION EXPLOSIVE*" if a.compression else ""
        message = f"""
🤖 *SIGNAL BOT TRADING*{comp}

{emoji} *{a.pattern}* | `{a.pair}` | `{a.timeframe}`
📅 {a.timestamp}

📍 *ENTRÉE*  : `{a.entry:,.4f}`
🔴 *SL*      : `{a.sl:,.4f}`
🟠 *TP1*     : `{a.tp1:,.4f}`
🟢 *TP2*     : `{a.tp2:,.4f}`  _(RR 1:{a.rr_ratio})_

📊 {a.confluence}
ADX: `{a.adx}` | QQE: `{a.qqe_status}`
        """.strip()

        url     = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        payload = {
            "chat_id"    : self.tg_chat_id,
            "text"       : message,
            "parse_mode" : "Markdown",
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Telegram envoyé : {a.pair} {a.pattern}")
            else:
                logger.warning(f"⚠️ Telegram erreur {response.status_code} : {response.text}")
        except Exception as e:
            logger.error(f"❌ Telegram exception : {e}")

    def send_visual_analysis(self, analysis: dict, image_path: str = ""):
        """
        Envoie une alerte Telegram pour analyse visuelle avec photo jointe.
        Seulement si score >= 6.
        """
        score = analysis.get("confluence_score", 0)
        direction = analysis.get("direction", "NEUTRAL")
        pair = analysis.get("pair", "?")
        tf = analysis.get("timeframe", "?")
        pattern = analysis.get("pattern", "Visual Analysis")
        summary = analysis.get("summary", "")
        entry = analysis.get("entry", 0)
        sl = analysis.get("sl", 0)
        tp1 = analysis.get("tp1", 0)
        tp2 = analysis.get("tp2", 0)
        rr = analysis.get("rr_ratio", 0)
        warnings = analysis.get("warnings", [])

        if score < 6:
            return

        emoji = "\u2b06\ufe0f" if direction == "LONG" else "\u2b07\ufe0f"
        score_emoji = "\U0001f3c6" if score >= 9 else "\u2705\u2705" if score >= 7 else "\u2705"

        message = (
            f"\U0001f4f8 *ANALYSE VISUELLE*\n\n"
            f"{emoji} *{pattern}* | `{pair}` | `{tf}`\n"
            f"{score_emoji} *Score : {score}/10*\n\n"
        )

        if entry:
            message += (
                f"\U0001f4cd *ENTRÉE*  : `{entry:,.4f}`\n"
                f"\U0001f534 *SL*      : `{sl:,.4f}`\n"
                f"\U0001f7e0 *TP1*     : `{tp1:,.4f}`\n"
                f"\U0001f7e2 *TP2*     : `{tp2:,.4f}`  _(RR 1:{rr})_\n\n"
            )

        message += f"\U0001f4dd {summary}"

        if warnings:
            message += f"\n\n\u26a0\ufe0f {', '.join(warnings)}"

        if not self.tg_enabled or not REQUESTS_OK:
            return

        try:
            # Si image disponible, envoyer comme photo
            if image_path and os.path.isfile(image_path):
                url = f"https://api.telegram.org/bot{self.tg_token}/sendPhoto"
                with open(image_path, "rb") as f:
                    requests.post(url, data={
                        "chat_id": self.tg_chat_id,
                        "caption": message,
                        "parse_mode": "Markdown",
                    }, files={"photo": f}, timeout=30)
            else:
                # Pas d'image, envoyer comme texte
                url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
                requests.post(url, json={
                    "chat_id": self.tg_chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                }, timeout=10)

            logger.info(f"Telegram visual analysis envoyé : {pair} {tf} score={score}")
        except Exception as e:
            logger.error(f"Telegram visual analysis erreur : {e}")

    def send_pine_script(self, pair: str, tf: str, pine_path: str):
        """Envoie le fichier Pine Script sur Telegram."""
        if not self.tg_enabled or not REQUESTS_OK:
            return
        try:
            url = f"https://api.telegram.org/bot{self.tg_token}/sendDocument"
            with open(pine_path, "rb") as f:
                requests.post(url, data={
                    "chat_id" : self.tg_chat_id,
                    "caption" : f"📄 Pine Script — {pair} {tf}"
                }, files={"document": f}, timeout=15)
        except Exception as e:
            logger.error(f"❌ Envoi Pine Script : {e}")

    # ──────────────────────────────────────────────────────────────
    # LOG JSON
    # ──────────────────────────────────────────────────────────────

    def _save_log(self, a: Alert):
        log_path = "outputs/signals_log.json"
        os.makedirs("outputs", exist_ok=True)
        try:
            try:
                with open(log_path, "r") as f:
                    logs = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                logs = []

            logs.append({
                "timestamp"  : a.timestamp,
                "pair"       : a.pair,
                "timeframe"  : a.timeframe,
                "pattern"    : a.pattern,
                "direction"  : a.direction,
                "entry"      : a.entry,
                "sl"         : a.sl,
                "tp1"        : a.tp1,
                "tp2"        : a.tp2,
                "rr"         : a.rr_ratio,
                "adx"        : a.adx,
                "compression": a.compression,
            })

            with open(log_path, "w") as f:
                json.dump(logs[-500:], f, indent=2)  # Garde les 500 derniers
        except Exception as e:
            logger.warning(f"⚠️ Sauvegarde log : {e}")
