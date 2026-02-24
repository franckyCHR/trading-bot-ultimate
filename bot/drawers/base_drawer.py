"""
base_drawer.py
──────────────
Classe de base pour tous les drawers.
Contient un FALLBACK GÉNÉRIQUE qui fonctionne pour n'importe quelle figure.
Aucune erreur possible : si un drawer spécifique n'existe pas,
le fallback prend le relai automatiquement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class DrawingOutput:
    """Résultat standard retourné par chaque drawer"""
    pattern_name   : str
    direction      : str           # LONG / SHORT / NEUTRE
    entry_price    : float
    stop_loss      : float
    tp1            : float
    tp2            : float
    pine_script    : str           # Code Pine Script prêt à coller dans TradingView
    mql4_script    : str           # Code MQL4 prêt à coller dans MT4
    description    : str           # Description textuelle de la figure
    elements_drawn : list          # Liste des éléments dessinés


class BaseDrawer(ABC):
    """Classe abstraite que chaque drawer doit implémenter"""

    @abstractmethod
    def draw(self, signal: dict) -> DrawingOutput:
        """
        Dessine la figure et retourne le code Pine + MQL4.
        signal = dict avec toutes les infos du pattern détecté.
        """
        pass

    # ──────────────────────────────────────────────────────────────
    # UTILITAIRES PARTAGÉS — disponibles dans tous les drawers
    # ──────────────────────────────────────────────────────────────

    def _pine_entry_lines(self, entry: float, sl: float,
                          tp1: float, tp2: float, direction: str) -> str:
        """Génère les lignes d'entrée / SL / TP communes à tous les patterns"""
        arrow = "⬆️ LONG" if direction == "LONG" else "⬇️ SHORT"
        color = "color.green" if direction == "LONG" else "color.red"
        label_style = "label.style_label_up" if direction == "LONG" else "label.style_label_down"

        return f"""
// ── Flèche d'entrée ──────────────────────────────────
label.new(bar_index, {entry},
    text      = "{arrow}\\nEntrée: {entry}",
    style     = {label_style},
    color     = {color},
    textcolor = color.white,
    size      = size.large)

// ── Stop Loss ────────────────────────────────────────
line.new(bar_index - 5, {sl}, bar_index + 20, {sl},
    color = color.red, width = 2, style = line.style_dashed)
label.new(bar_index + 20, {sl},
    text  = "🔴 SL {sl}",
    style = label.style_label_left, color = color.red, textcolor = color.white)

// ── TP1 ──────────────────────────────────────────────
line.new(bar_index - 5, {tp1}, bar_index + 20, {tp1},
    color = color.orange, width = 1, style = line.style_dotted)
label.new(bar_index + 20, {tp1},
    text  = "🟠 TP1 {tp1}",
    style = label.style_label_left, color = color.orange, textcolor = color.white)

// ── TP2 ──────────────────────────────────────────────
line.new(bar_index - 5, {tp2}, bar_index + 20, {tp2},
    color = color.green, width = 2)
label.new(bar_index + 20, {tp2},
    text  = "🟢 TP2 {tp2}",
    style = label.style_label_left, color = color.green, textcolor = color.white)
"""

    def _mql4_entry_lines(self, entry: float, sl: float,
                           tp1: float, tp2: float, direction: str,
                           prefix: str = "SIG") -> str:
        """Génère les lignes d'entrée MT4 communes à tous les patterns"""
        arrow_code = "233" if direction == "LONG" else "234"
        arrow_color = "clrGreen" if direction == "LONG" else "clrRed"

        return f"""
// ── Flèche d'entrée ──────────────────────────────────
ObjectCreate("{prefix}_Entry", OBJ_ARROW, 0, Time[0], {entry});
ObjectSet("{prefix}_Entry", OBJPROP_ARROWCODE, {arrow_code});
ObjectSet("{prefix}_Entry", OBJPROP_COLOR, {arrow_color});
ObjectSet("{prefix}_Entry", OBJPROP_WIDTH, 4);

// ── Stop Loss ────────────────────────────────────────
ObjectCreate("{prefix}_SL", OBJ_HLINE, 0, 0, {sl});
ObjectSet("{prefix}_SL", OBJPROP_COLOR, clrRed);
ObjectSet("{prefix}_SL", OBJPROP_STYLE, STYLE_DASH);
ObjectSet("{prefix}_SL", OBJPROP_WIDTH, 2);
ObjectCreate("{prefix}_SL_Lbl", OBJ_TEXT, 0, Time[0], {sl});
ObjectSetText("{prefix}_SL_Lbl", "SL: {sl}", 9, "Arial Bold", clrRed);

// ── TP1 ──────────────────────────────────────────────
ObjectCreate("{prefix}_TP1", OBJ_HLINE, 0, 0, {tp1});
ObjectSet("{prefix}_TP1", OBJPROP_COLOR, clrOrange);
ObjectSet("{prefix}_TP1", OBJPROP_STYLE, STYLE_DOT);
ObjectCreate("{prefix}_TP1_Lbl", OBJ_TEXT, 0, Time[0], {tp1});
ObjectSetText("{prefix}_TP1_Lbl", "TP1: {tp1}", 9, "Arial Bold", clrOrange);

// ── TP2 ──────────────────────────────────────────────
ObjectCreate("{prefix}_TP2", OBJ_HLINE, 0, 0, {tp2});
ObjectSet("{prefix}_TP2", OBJPROP_COLOR, clrGreen);
ObjectSet("{prefix}_TP2", OBJPROP_WIDTH, 2);
ObjectCreate("{prefix}_TP2_Lbl", OBJ_TEXT, 0, Time[0], {tp2});
ObjectSetText("{prefix}_TP2_Lbl", "TP2: {tp2}", 9, "Arial Bold", clrGreen);
"""


# ══════════════════════════════════════════════════════════════════
# FALLBACK GÉNÉRIQUE — fonctionne pour n'importe quelle figure
# Utilisé automatiquement si aucun drawer spécifique n'est trouvé
# ══════════════════════════════════════════════════════════════════

class GenericFallbackDrawer(BaseDrawer):
    """
    Drawer de secours universel.
    Dessine n'importe quelle figure avec une représentation générique :
    - Zone colorée sur les bougies concernées
    - Label avec le nom de la figure
    - Entrée / SL / TP1 / TP2

    Ne lève JAMAIS d'erreur. Toujours opérationnel.
    """

    def draw(self, signal: dict) -> DrawingOutput:
        name      = signal.get("pattern",   "PATTERN INCONNU")
        direction = signal.get("direction", "NEUTRE")
        entry     = signal.get("entry",     signal.get("close", 0))
        sl        = signal.get("stop_loss", entry * 0.98 if direction == "LONG" else entry * 1.02)
        tp1       = signal.get("tp1",       entry * 1.01 if direction == "LONG" else entry * 0.99)
        tp2       = signal.get("tp2",       entry * 1.02 if direction == "LONG" else entry * 0.98)
        bar_left  = signal.get("bar_start", 10)
        high      = signal.get("zone_high", entry * 1.005)
        low       = signal.get("zone_low",  entry * 0.995)
        color_map = {"LONG": "color.green", "SHORT": "color.red", "NEUTRE": "color.yellow"}
        clr       = color_map.get(direction, "color.gray")
        mql_clr   = {"LONG": "clrGreen", "SHORT": "clrRed", "NEUTRE": "clrYellow"}.get(direction, "clrGray")
        emoji     = "⬆️" if direction == "LONG" else "⬇️" if direction == "SHORT" else "⚡"

        pine = f"""
//@version=5
indicator("{name}", overlay=true)

// ── Zone générique de la figure ───────────────────────
box.new(bar_index - {bar_left}, {high},
        bar_index,               {low},
        bgcolor      = color.new({clr}, 80),
        border_color = {clr},
        border_width = 2)

// ── Label ──────────────────────────────────────────────
label.new(bar_index, {high},
    text      = "{emoji} {name}\\n{direction}",
    style     = label.style_label_down,
    color     = {clr},
    textcolor = color.white,
    size      = size.large)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, direction)

        mql4 = f"""
// ── Zone générique MT4 ────────────────────────────────
ObjectCreate("{name}_Zone", OBJ_RECTANGLE, 0,
    Time[{bar_left}], {high}, Time[0], {low});
ObjectSet("{name}_Zone", OBJPROP_COLOR, {mql_clr});
ObjectSet("{name}_Zone", OBJPROP_BACK, true);
ObjectSet("{name}_Zone", OBJPROP_FILL, true);

// ── Label ──────────────────────────────────────────────
ObjectCreate("{name}_Lbl", OBJ_TEXT, 0, Time[0], {high});
ObjectSetText("{name}_Lbl", "{emoji} {name} | {direction}", 11, "Arial Bold", {mql_clr});
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, direction, prefix=name[:6])

        return DrawingOutput(
            pattern_name   = name,
            direction      = direction,
            entry_price    = entry,
            stop_loss      = sl,
            tp1            = tp1,
            tp2            = tp2,
            pine_script    = pine,
            mql4_script    = mql4,
            description    = f"[FALLBACK] {name} détecté — drawer générique utilisé",
            elements_drawn = ["zone_coloree", "label", "entree", "sl", "tp1", "tp2"]
        )
