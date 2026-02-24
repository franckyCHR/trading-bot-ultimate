"""
gate_checker.py
───────────────
Les 2 portes obligatoires du bot.
Si une porte est fermée → STOP TOTAL, aucun signal émis.
Ce fichier ne peut pas être contourné dans le pipeline.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GateResult:
    allowed      : bool
    reason       : str
    gate1_sr     : bool = False   # Zone S/R identifiée
    gate2_figure : bool = False   # Figure ou reversal confirmé
    adx_ok       : bool = False   # ADX momentum valide
    qqe_ok       : bool = False   # QQE croisement aligné
    compression  : bool = False   # Zone de compression présente
    warnings     : list = None    # Avertissements non bloquants

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class GateChecker:
    """
    Vérifie toutes les conditions dans l'ordre séquentiel.
    Les portes 1, 2, 3 et 4 sont BLOQUANTES.
    Les autres génèrent des avertissements.
    """

    def check(self, signal: dict) -> GateResult:

        warnings = []

        # ══════════════════════════════════════════════
        # PORTE 1 — Zone S/R identifiée
        # ══════════════════════════════════════════════
        has_sr = bool(signal.get("sr_zone"))
        sr_strength = signal.get("sr_strength", 0)

        if not has_sr:
            return GateResult(
                allowed      = False,
                reason       = "❌ PORTE 1 FERMÉE — Aucune zone S/R identifiée. Pas de trade.",
                gate1_sr     = False,
                gate2_figure = False,
            )

        if sr_strength < 1:
            warnings.append("⚠️ Zone S/R faible (moins de 2 touches)")

        # ══════════════════════════════════════════════
        # PORTE 2 — Figure chartiste OU reversal candle
        # ══════════════════════════════════════════════
        has_pattern  = bool(signal.get("pattern"))
        has_reversal = bool(signal.get("reversal_candle"))
        pattern_clarity = signal.get("pattern_clarity", 0)

        if not has_pattern and not has_reversal:
            return GateResult(
                allowed      = False,
                reason       = "❌ PORTE 2 FERMÉE — Aucune figure ni reversal candle confirmé. Pas de trade.",
                gate1_sr     = True,
                gate2_figure = False,
            )

        if has_pattern and pattern_clarity < 2:
            return GateResult(
                allowed      = False,
                reason       = f"❌ PORTE 2 FERMÉE — Figure '{signal.get('pattern')}' trop floue (clarté {pattern_clarity}/3). Pas de trade.",
                gate1_sr     = True,
                gate2_figure = False,
            )

        if has_pattern and has_reversal:
            warnings.append("✅ BONUS — Figure chartiste ET reversal candle sur la même zone")

        # ══════════════════════════════════════════════
        # GATE 3 — ADX momentum (BLOQUANT)
        # ══════════════════════════════════════════════
        adx_value = float(signal.get("adx", 0))
        di_plus   = float(signal.get("di_plus", 0))
        di_minus  = float(signal.get("di_minus", 0))
        direction = signal.get("direction", "NEUTRE")

        adx_ok = adx_value >= 20
        di_ok  = (di_plus >= di_minus) if direction == "LONG" else (di_minus >= di_plus)

        if not adx_ok:
            return GateResult(
                allowed      = False,
                reason       = f"❌ GATE 3 FERMÉE — ADX {adx_value:.1f} < 20 — momentum insuffisant",
                gate1_sr     = True,
                gate2_figure = True,
                warnings     = warnings,
            )

        if not di_ok:
            dominant = f"-DI {di_minus:.1f}" if direction == "LONG" else f"+DI {di_plus:.1f}"
            return GateResult(
                allowed      = False,
                reason       = f"❌ GATE 3 FERMÉE — DI inversé ({dominant} dominant) — momentum contre le trade",
                gate1_sr     = True,
                gate2_figure = True,
                warnings     = warnings,
            )

        rising = signal.get("adx_rising", False)
        warnings.append(f"ADX: {round(adx_value,1)}{'↑' if rising else ''} ✅")

        # ══════════════════════════════════════════════
        # GATE 4 — QQE croisement récent (BLOQUANT)
        # ══════════════════════════════════════════════
        qqe_fast      = float(signal.get("qqe_fast", 0))
        qqe_slow      = float(signal.get("qqe_slow", 0))
        qqe_fast_prev = float(signal.get("qqe_fast_prev", 0))
        qqe_slow_prev = float(signal.get("qqe_slow_prev", 0))
        qqe_bars_ago  = int(signal.get("qqe_cross_bars_ago", 99))

        qqe_side_ok = (qqe_fast > qqe_slow) if direction == "LONG" else (qqe_fast < qqe_slow)
        qqe_fresh   = qqe_bars_ago <= 6

        if not qqe_side_ok:
            sens = "baissier" if direction == "LONG" else "haussier"
            return GateResult(
                allowed      = False,
                reason       = f"❌ GATE 4 FERMÉE — QQE {sens} — momentum court terme contre le trade",
                gate1_sr     = True,
                gate2_figure = True,
                adx_ok       = True,
                warnings     = warnings,
            )

        if not qqe_fresh:
            return GateResult(
                allowed      = False,
                reason       = f"❌ GATE 4 FERMÉE — QQE croisement il y a {qqe_bars_ago} barres (max autorisé : 6)",
                gate1_sr     = True,
                gate2_figure = True,
                adx_ok       = True,
                warnings     = warnings,
            )

        cross_bull = (qqe_fast > qqe_slow) and (qqe_fast_prev <= qqe_slow_prev)
        cross_bear = (qqe_fast < qqe_slow) and (qqe_fast_prev >= qqe_slow_prev)
        qqe_ok     = True

        if direction == "LONG":
            if cross_bull:
                warnings.append("QQE: croisement haussier frais ✅✅")
            else:
                warnings.append(f"QQE: haussier il y a {qqe_bars_ago} bougies ✅")
        else:
            if cross_bear:
                warnings.append("QQE: croisement baissier frais ✅✅")
            else:
                warnings.append(f"QQE: baissier il y a {qqe_bars_ago} bougies ✅")

        # ══════════════════════════════════════════════
        # GATE 5 — Contexte HTF (BLOQUANT pour M15/M30)
        # ══════════════════════════════════════════════
        tf           = signal.get("timeframe", "1h")
        htf_blocked  = signal.get("htf_blocked", False)
        htf1_tf      = signal.get("htf1_tf", "1h")
        htf1_trend   = signal.get("htf1_trend", "NEUTRE")
        htf2_tf      = signal.get("htf2_tf", "4h")
        htf2_trend   = signal.get("htf2_trend", "NEUTRE")

        if tf in ("15m", "30m") and htf_blocked:
            return GateResult(
                allowed      = False,
                reason       = (
                    f"❌ GATE 5 FERMÉE — {htf1_tf} est {htf1_trend} "
                    f"CONTRE ta direction {direction} — "
                    f"Tu trades contre la tendance immédiate. ATTENDS."
                ),
                gate1_sr     = True,
                gate2_figure = True,
                adx_ok       = True,
                qqe_ok       = True,
                warnings     = warnings,
            )

        # Ajouter le contexte HTF comme info
        if tf in ("15m", "30m"):
            h1_ok = (direction == "LONG" and htf1_trend == "BULLISH") or \
                    (direction == "SHORT" and htf1_trend == "BEARISH")
            h4_ok = (direction == "LONG" and htf2_trend == "BULLISH") or \
                    (direction == "SHORT" and htf2_trend == "BEARISH")
            if h1_ok and h4_ok:
                warnings.append(f"🎯 SNIPER {htf1_tf}+{htf2_tf} alignés → entrée de qualité")
            elif h1_ok:
                warnings.append(f"✅ {htf1_tf} aligné | {htf2_tf}: {htf2_trend} (surveille)")
            else:
                warnings.append(f"⚠️ {htf1_tf}: {htf1_trend} — contexte neutre")

        # ══════════════════════════════════════════════
        # FILTRE 6 — Zone de compression (bonus)
        # ══════════════════════════════════════════════
        has_compression = bool(signal.get("compression_zone"))
        if has_compression:
            warnings.append("🔥 COMPRESSION EXPLOSIVE — énergie accumulée")

        # ══════════════════════════════════════════════
        # FILTRE 7 — Avertissements psychologiques
        # ══════════════════════════════════════════════
        trades_today = signal.get("trades_today", 0)
        if trades_today >= 3:
            warnings.append("⚠️ PSYCHO — 3 trades déjà pris aujourd'hui")

        loss_today = signal.get("loss_on_pair_today", False)
        if loss_today:
            warnings.append("⚠️ PSYCHO — Perte déjà prise sur cette paire aujourd'hui")

        session_ok = signal.get("active_session", True)
        if not session_ok:
            warnings.append("⚠️ PSYCHO — En dehors des sessions London/NY")

        # ══════════════════════════════════════════════
        # RÉSULTAT FINAL
        # ══════════════════════════════════════════════
        htf_aligned = signal.get("htf_aligned", False)
        htf2_aligned = (
            (direction == "LONG"  and signal.get("htf2_trend") == "BULLISH") or
            (direction == "SHORT" and signal.get("htf2_trend") == "BEARISH")
        )

        confluence_score = sum([
            has_sr,
            has_pattern or has_reversal,
            has_pattern and has_reversal,   # bonus double confirmation
            adx_ok,
            qqe_ok,
            has_compression,
            htf_aligned,                    # H1 dans le sens du trade
            htf2_aligned,                   # H4 dans le sens du trade
        ])

        if confluence_score >= 6:
            status = "🔥 SNIPER PARFAIT"
        elif confluence_score >= 4:
            status = "✅ SIGNAL FORT"
        elif confluence_score >= 2:
            status = "📊 SIGNAL VALIDE"
        else:
            status = "⚠️ SIGNAL FAIBLE — surveiller"

        return GateResult(
            allowed      = True,
            reason       = f"{status} — confluence {confluence_score}/8",
            gate1_sr     = True,
            gate2_figure = True,
            adx_ok       = adx_ok,
            qqe_ok       = qqe_ok,
            compression  = has_compression,
            warnings     = warnings,
        )
