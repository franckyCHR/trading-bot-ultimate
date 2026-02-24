"""
special_drawers.py
──────────────────
Drawers pour :
- Chandeliers de reversal (Pin Bar, Engulfing, Morning/Evening Star, etc.)
- Zones de compression
"""

from .base_drawer import BaseDrawer, DrawingOutput


class ReversalCandleDrawer(BaseDrawer):
    """
    Drawer universel pour tous les chandeliers de reversal.
    Dessine un CERCLE autour du chandelier signal + flèche directionnelle.
    Fonctionne pour : Pin Bar, Marteau, Engulfing, Morning Star, Evening Star,
                      Harami, Étoile Filante, Doji.
    """

    PATTERN_EMOJIS = {
        "PIN_BAR_BULLISH"    : "📍⬆️ PIN BAR",
        "PIN_BAR_BEARISH"    : "📍⬇️ PIN BAR",
        "MARTEAU"            : "🔨⬆️ MARTEAU",
        "ETOILE_FILANTE"     : "⭐⬇️ ÉT.FILANTE",
        "BULLISH_ENGULFING"  : "🟢⬆️ ENGULFING",
        "BEARISH_ENGULFING"  : "🔴⬇️ ENGULFING",
        "MORNING_STAR"       : "🌅⬆️ MORNING STAR",
        "EVENING_STAR"       : "🌇⬇️ EVENING STAR",
        "HARAMI_BULLISH"     : "🟢⬆️ HARAMI",
        "HARAMI_BEARISH"     : "🔴⬇️ HARAMI",
        "DOJI"               : "➕ DOJI",
    }

    def draw(self, signal: dict) -> DrawingOutput:
        s         = signal
        pattern   = s.get("pattern", "REVERSAL_CANDLE")
        direction = s.get("direction", "LONG")
        entry     = s["close"]
        candle_high = s["high"]
        candle_low  = s["low"]
        atr       = s.get("atr", abs(candle_high - candle_low))

        if direction == "LONG":
            sl  = candle_low  - atr * 0.3
            tp1 = entry + (entry - sl)
            tp2 = entry + (entry - sl) * 2
            circle_pos   = "label.style_label_up"
            circle_offset = candle_low - atr * 0.5
            clr           = "color.green"
            mql_clr       = "clrGreen"
        else:
            sl  = candle_high + atr * 0.3
            tp1 = entry - (sl - entry)
            tp2 = entry - (sl - entry) * 2
            circle_pos    = "label.style_label_down"
            circle_offset = candle_high + atr * 0.5
            clr           = "color.red"
            mql_clr       = "clrRed"

        emoji = self.PATTERN_EMOJIS.get(pattern, f"🕯️ {pattern}")

        pine = f"""
//@version=5
indicator("{pattern}", overlay=true)

// ── Cercle autour du chandelier signal ────────────────
label.new(bar_index, {circle_offset},
    text      = "⬤",
    style     = {circle_pos},
    color     = color.new({clr}, 40),
    textcolor = {clr},
    size      = size.huge)

// ── Nom du pattern ────────────────────────────────────
label.new(bar_index, {circle_offset},
    text      = "{emoji}\\n{round(entry, 2)}",
    style     = {circle_pos},
    color     = {clr},
    textcolor = color.white,
    size      = size.normal)

// ── Rectangle sur les bougies du pattern ──────────────
box.new(bar_index - {s.get('pattern_bars', 1)}, {candle_high * 1.001},
        bar_index, {candle_low * 0.999},
        bgcolor      = color.new({clr}, 82),
        border_color = {clr},
        border_width = 2)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, direction)

        mql4 = f"""
// Reversal Candle — MT4
ObjectCreate("{pattern[:6]}_Circle", OBJ_ELLIPSE, 0,
    Time[1], {candle_high * 1.002}, Time[0], {candle_low * 0.998});
ObjectSet("{pattern[:6]}_Circle", OBJPROP_COLOR, {mql_clr});
ObjectSet("{pattern[:6]}_Circle", OBJPROP_WIDTH, 2);
ObjectCreate("{pattern[:6]}_Lbl", OBJ_TEXT, 0, Time[0], {circle_offset});
ObjectSetText("{pattern[:6]}_Lbl", "{emoji}", 14, "Arial Bold", {mql_clr});
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, direction, pattern[:6])

        return DrawingOutput(
            pattern_name=pattern,
            direction=direction,
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description=f"{emoji} sur S/R | Entrée={round(entry,2)} SL={round(sl,2)} RR=1:{round(abs(tp2-entry)/max(abs(sl-entry),0.001),1)}",
            elements_drawn=["cercle_chandelier","rectangle_bougie","nom_pattern","entree","sl","tp1","tp2"]
        )


class CompressionDrawer(BaseDrawer):
    """
    Zone de compression — rectangle jaune + flèche à la cassure.
    Amplifie n'importe quel signal avec lequel il coïncide.
    """

    def draw(self, signal: dict) -> DrawingOutput:
        s          = signal
        start_bar  = s["compression_start_bar"]
        high_zone  = s["compression_high"]
        low_zone   = s["compression_low"]
        amplitude  = high_zone - low_zone
        nb_bougies = s.get("nb_bougies", 0)
        atr        = s.get("atr", amplitude * 0.2)
        direction  = s.get("direction", "NEUTRE")   # déterminé par la cassure

        if direction == "LONG":
            entry = high_zone
            sl    = low_zone - atr * 0.3
            tp1   = entry + amplitude
            tp2   = entry + amplitude * 2
            clr   = "color.green"; mql_clr = "clrGreen"
            emoji = "⚡⬆️ COMPRESSION → EXPLOSION HAUSSIÈRE"
        elif direction == "SHORT":
            entry = low_zone
            sl    = high_zone + atr * 0.3
            tp1   = entry - amplitude
            tp2   = entry - amplitude * 2
            clr   = "color.red"; mql_clr = "clrRed"
            emoji = "⚡⬇️ COMPRESSION → EXPLOSION BAISSIÈRE"
        else:
            entry = (high_zone + low_zone) / 2
            sl    = 0; tp1 = 0; tp2 = 0
            clr   = "color.yellow"; mql_clr = "clrYellow"
            emoji = "⚡ COMPRESSION — ATTENDRE CASSURE"

        pine = f"""
//@version=5
indicator("Zone de Compression", overlay=true)

// ── Rectangle de compression (jaune) ─────────────────
box.new({start_bar}, {high_zone}, bar_index, {low_zone},
    bgcolor      = color.new(color.yellow, 70),
    border_color = color.yellow,
    border_width = 3)

// ── Label ─────────────────────────────────────────────
label.new({start_bar + (bar_index - start_bar) // 2}, {high_zone},
    text      = "{emoji}\\n{nb_bougies} bougies | ATR réduit",
    style     = label.style_label_down,
    color     = color.yellow,
    textcolor = color.black,
    size      = size.large)

// ── Bornes haute et basse de la zone ──────────────────
line.new({start_bar}, {high_zone}, bar_index + 10, {high_zone},
    color=color.orange, width=2, style=line.style_dashed)
label.new(bar_index + 10, {high_zone}, "Haut: {round(high_zone, 2)}",
    style=label.style_label_left, color=color.orange, textcolor=color.white, size=size.small)

line.new({start_bar}, {low_zone}, bar_index + 10, {low_zone},
    color=color.orange, width=2, style=line.style_dashed)
label.new(bar_index + 10, {low_zone}, "Bas: {round(low_zone, 2)}",
    style=label.style_label_left, color=color.orange, textcolor=color.white, size=size.small)
""" + (self._pine_entry_lines(entry, sl, tp1, tp2, direction) if direction != "NEUTRE" else "")

        mql4 = f"""
ObjectCreate("COMP_Zone", OBJ_RECTANGLE, 0,
    Time[bar_index - {start_bar}], {high_zone}, Time[0], {low_zone});
ObjectSet("COMP_Zone", OBJPROP_COLOR, clrYellow);
ObjectSet("COMP_Zone", OBJPROP_BACK, true);
ObjectSet("COMP_Zone", OBJPROP_WIDTH, 2);
ObjectCreate("COMP_Top", OBJ_HLINE, 0, 0, {high_zone});
ObjectSet("COMP_Top", OBJPROP_COLOR, clrOrange); ObjectSet("COMP_Top", OBJPROP_STYLE, STYLE_DASH);
ObjectCreate("COMP_Bot", OBJ_HLINE, 0, 0, {low_zone});
ObjectSet("COMP_Bot", OBJPROP_COLOR, clrOrange); ObjectSet("COMP_Bot", OBJPROP_STYLE, STYLE_DASH);
ObjectCreate("COMP_Lbl", OBJ_TEXT, 0, Time[0], {high_zone});
ObjectSetText("COMP_Lbl", "{emoji}", 11, "Arial Bold", clrYellow);
""" + (self._mql4_entry_lines(entry, sl, tp1, tp2, direction, "COMP") if direction != "NEUTRE" else "")

        return DrawingOutput(
            pattern_name="COMPRESSION",
            direction=direction,
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description=f"⚡ Compression {nb_bougies} bougies | Range={round(amplitude,2)} | {direction}",
            elements_drawn=["rectangle_jaune","bornes_haute_basse","label","entree","sl","tp1","tp2"]
        )
