"""
screenshot_capture.py
─────────────────────
Capture d'écran Mac pour le mode semi-automatique.
L'utilisateur change manuellement le template/TF dans MT4
et appuie Entrée pour capturer chaque vue.
"""

import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("ScreenshotCapture")

SCREENSHOTS_DIR = "outputs/screenshots"


class ScreenshotCapture:
    """Capture d'écran via screencapture (macOS)."""

    def __init__(self, output_dir: str = SCREENSHOTS_DIR):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def capture_screen(self, output_path: str, region: tuple = None) -> str:
        """
        Capture l'écran entier (ou une région) via screencapture -x.

        Args:
            output_path: Chemin de sauvegarde du PNG
            region: Optionnel (x, y, w, h) pour capturer une zone

        Returns:
            Chemin du fichier capturé
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        cmd = ["screencapture", "-x"]  # -x = pas de son
        if region:
            x, y, w, h = region
            cmd.extend(["-R", f"{x},{y},{w},{h}"])
        cmd.append(output_path)

        try:
            subprocess.run(cmd, check=True, timeout=10)
        except FileNotFoundError:
            raise RuntimeError(
                "screencapture non disponible. "
                "Ce mode fonctionne uniquement sur macOS."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout lors de la capture d'écran")

        # Validation
        path = Path(output_path)
        if not path.exists():
            raise RuntimeError(f"Capture échouée : {output_path}")

        size = path.stat().st_size
        if size < 10_000:
            logger.warning(f"Image suspecte ({size} bytes) : {output_path}")

        logger.info(f"Screenshot capturé : {output_path} ({size // 1024} KB)")
        return output_path

    def capture_full_circuit(
        self,
        pair: str,
        templates: list[str] = None,
        timeframes: list[str] = None,
    ) -> list[dict]:
        """
        Circuit complet de capture : boucle sur templates x TF.
        L'utilisateur change dans MT4 et appuie Entrée pour capturer.

        Args:
            pair: Paire tradée (ex: "GBP/USD")
            templates: Liste des templates MT4
            timeframes: Liste des timeframes

        Returns:
            Liste de dicts {image_path, pair, timeframe, template}
        """
        templates = templates or ["Momentum", "RSI", "EXTREM_MONEY", "Harmoniques"]
        timeframes = timeframes or ["M30", "H1", "H4", "D1"]

        total = len(templates) * len(timeframes)
        images = []
        count = 0

        pair_clean = pair.replace("/", "_")
        ts = datetime.now().strftime("%Y%m%d_%H%M")

        print("\n" + "-" * 55)
        print("  MODE CAPTURE — Circuit MT4")
        print("-" * 55)
        print(f"  Paire     : {pair}")
        print(f"  Templates : {', '.join(templates)}")
        print(f"  TFs       : {', '.join(timeframes)}")
        print(f"  Total     : {total} captures")
        print("-" * 55)
        print("  Instructions :")
        print("  1. Ouvre MT4 avec le graphique visible")
        print("  2. Change le template et le TF comme indiqué")
        print("  3. Appuie [Entrée] pour capturer")
        print("  4. Tape 'skip' pour passer, 'quit' pour arrêter")
        print("-" * 55 + "\n")

        for template in templates:
            for tf in timeframes:
                count += 1
                prompt = f"  [{count}/{total}] {template} | {tf} — Prêt ? [Entrée/skip/quit] "

                user_input = input(prompt).strip().lower()

                if user_input == "quit":
                    print("  Arrêt du circuit.")
                    return images

                if user_input == "skip":
                    print(f"  Skipped {template} {tf}")
                    continue

                # Capturer
                filename = f"{pair_clean}_{template}_{tf}_{ts}.png"
                output_path = os.path.join(self.output_dir, filename)

                try:
                    self.capture_screen(output_path)
                    images.append({
                        "image_path": output_path,
                        "pair": pair,
                        "timeframe": tf,
                        "template": template,
                    })
                    print(f"  Capturé : {filename}")
                except Exception as e:
                    print(f"  Erreur capture : {e}")

        print(f"\n  Total capturé : {len(images)}/{total} images")
        return images
