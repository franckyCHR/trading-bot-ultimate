"""
harmonic_drawers.py
───────────────────
Drawers pour les figures harmoniques.
Dessine chaque segment XABCD avec couleur distincte + ratio Fibonacci affiché.
"""

from .base_drawer import BaseDrawer, DrawingOutput


class ButterflyDrawer(BaseDrawer):
    """
    Butterfly Harmonique (Bullish ou Bearish)
    Dessine : X→A (bleu) | A→B (orange) | B→C (vert) | C→D (violet)
    + ratios Fibonacci sur chaque segment + PRZ colorée autour de D
    """

    def draw(self, signal: dict) -> DrawingOutput:
        s = signal
        # Points XABCD : bar index + prix
        x_bar = s["X_bar"];  x_p = s["X_price"]
        a_bar = s["A_bar"];  a_p = s["A_price"]
        b_bar = s["B_bar"];  b_p = s["B_price"]
        c_bar = s["C_bar"];  c_p = s["C_price"]
        d_bar = s["D_bar"];  d_p = s["D_price"]
        direction = s["direction"]   # "LONG" ou "SHORT"

        # Ratios réels calculés
        r_ab = round(abs(b_p - a_p) / abs(x_p - a_p), 3) if abs(x_p - a_p) > 0 else 0
        r_bc = round(abs(c_p - b_p) / abs(a_p - b_p), 3) if abs(a_p - b_p) > 0 else 0
        r_cd = round(abs(d_p - c_p) / abs(b_p - c_p), 3) if abs(b_p - c_p) > 0 else 0
        r_xd = round(abs(d_p - x_p) / abs(a_p - x_p), 3) if abs(a_p - x_p) > 0 else 0

        # Points d'entrée
        atr     = s.get("atr", abs(x_p - a_p) * 0.05)
        entry   = d_p
        hauteur = abs(x_p - a_p)

        if direction == "LONG":
            sl  = d_p - atr * 2
            tp1 = d_p + abs(d_p - c_p)
            tp2 = d_p + abs(d_p - a_p)
            clr_lbl = "color.green"
            emoji   = "🦋 BUTTERFLY BULLISH ⬆️"
            prz_clr = "color.green"
        else:
            sl  = d_p + atr * 2
            tp1 = d_p - abs(d_p - c_p)
            tp2 = d_p - abs(d_p - a_p)
            clr_lbl = "color.red"
            emoji   = "🦋 BUTTERFLY BEARISH ⬇️"
            prz_clr = "color.red"

        mid_xa = (x_bar + a_bar) // 2;  mid_xa_p = (x_p + a_p) / 2
        mid_ab = (a_bar + b_bar) // 2;  mid_ab_p = (a_p + b_p) / 2
        mid_bc = (b_bar + c_bar) // 2;  mid_bc_p = (b_p + c_p) / 2
        mid_cd = (c_bar + d_bar) // 2;  mid_cd_p = (c_p + d_p) / 2

        pine = f"""
//@version=5
indicator("Butterfly {direction}", overlay=true)

// ── Segments XABCD ────────────────────────────────────
line.new({x_bar}, {x_p}, {a_bar}, {a_p}, color=color.blue,   width=2)  // XA
line.new({a_bar}, {a_p}, {b_bar}, {b_p}, color=color.orange, width=2)  // AB
line.new({b_bar}, {b_p}, {c_bar}, {c_p}, color=color.green,  width=2)  // BC
line.new({c_bar}, {c_p}, {d_bar}, {d_p}, color=color.purple, width=3)  // CD

// ── Points XABCD ──────────────────────────────────────
label.new({x_bar}, {x_p}, "X", style=label.style_label_right, color=color.blue,   textcolor=color.white, size=size.small)
label.new({a_bar}, {a_p}, "A", style=label.style_label_right, color=color.orange, textcolor=color.white, size=size.small)
label.new({b_bar}, {b_p}, "B", style=label.style_label_right, color=color.green,  textcolor=color.white, size=size.small)
label.new({c_bar}, {c_p}, "C", style=label.style_label_right, color=color.purple, textcolor=color.white, size=size.small)
label.new({d_bar}, {d_p}, "D", style=label.style_label_center, color={prz_clr}, textcolor=color.white, size=size.large)

// ── Ratios Fibonacci sur chaque segment ───────────────
label.new({mid_ab}, {mid_ab_p}, "AB/XA\\n{r_ab}", style=label.style_label_right, color=color.orange, textcolor=color.white, size=size.tiny)
label.new({mid_bc}, {mid_bc_p}, "BC/AB\\n{r_bc}", style=label.style_label_right, color=color.green,  textcolor=color.white, size=size.tiny)
label.new({mid_cd}, {mid_cd_p}, "CD/BC\\n{r_cd}", style=label.style_label_right, color=color.purple, textcolor=color.white, size=size.tiny)
label.new({mid_xa}, {mid_xa_p}, "XD/XA\\n{r_xd}", style=label.style_label_right, color=color.blue,  textcolor=color.white, size=size.tiny)

// ── PRZ — Zone d'entrée autour de D ───────────────────
box.new({d_bar} - 3, {d_p * 1.004}, {d_bar} + 3, {d_p * 0.996},
    bgcolor      = color.new({prz_clr}, 60),
    border_color = {prz_clr},
    border_width = 3)
label.new({d_bar}, {d_p}, "{emoji}\\nPRZ {round(d_p,2)}",
    style     = label.style_label_{'up' if direction == 'SHORT' else 'down'},
    color     = {clr_lbl},
    textcolor = color.white,
    size      = size.large)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, direction)

        mql4_dir = "clrGreen" if direction == "LONG" else "clrRed"
        mql4 = f"""
// Butterfly {direction} — MT4
ObjectCreate("BF_XA", OBJ_TREND, 0, Time[bar_index-{a_bar-x_bar}], {x_p}, Time[bar_index-{b_bar-a_bar}], {a_p});
ObjectSet("BF_XA", OBJPROP_COLOR, clrBlue); ObjectSet("BF_XA", OBJPROP_WIDTH, 2);
ObjectCreate("BF_AB", OBJ_TREND, 0, Time[bar_index-{b_bar-a_bar}], {a_p}, Time[bar_index-{c_bar-b_bar}], {b_p});
ObjectSet("BF_AB", OBJPROP_COLOR, clrOrange); ObjectSet("BF_AB", OBJPROP_WIDTH, 2);
ObjectCreate("BF_BC", OBJ_TREND, 0, Time[bar_index-{c_bar-b_bar}], {b_p}, Time[bar_index-{d_bar-c_bar}], {c_p});
ObjectSet("BF_BC", OBJPROP_COLOR, clrGreen); ObjectSet("BF_BC", OBJPROP_WIDTH, 2);
ObjectCreate("BF_CD", OBJ_TREND, 0, Time[bar_index-{d_bar-c_bar}], {c_p}, Time[0], {d_p});
ObjectSet("BF_CD", OBJPROP_COLOR, clrViolet); ObjectSet("BF_CD", OBJPROP_WIDTH, 3);
ObjectCreate("BF_PRZ", OBJ_RECTANGLE, 0, Time[3], {d_p * 1.004}, Time[0], {d_p * 0.996});
ObjectSet("BF_PRZ", OBJPROP_COLOR, {mql4_dir}); ObjectSet("BF_PRZ", OBJPROP_BACK, true);
ObjectCreate("BF_Lbl", OBJ_TEXT, 0, Time[0], {d_p});
ObjectSetText("BF_Lbl", "🦋 BUTTERFLY {direction}\\nAB={r_ab} | BC={r_bc} | CD={r_cd}", 10, "Arial Bold", {mql4_dir});
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, direction, "BFLY")

        return DrawingOutput(
            pattern_name="BUTTERFLY",
            direction=direction,
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description=f"🦋 Butterfly {direction} | AB={r_ab} BC={r_bc} CD={r_cd} XD={r_xd} | PRZ={round(d_p,2)}",
            elements_drawn=["segments_xabcd_couleurs","points_labels","ratios_fibonacci","prz_zone","label","entree","sl","tp1","tp2"]
        )


class SharkDrawer(BaseDrawer):
    """
    Shark Harmonique (Bullish ou Bearish)
    Structure : O→X→A→B→C (entrée au point C)
    """

    def draw(self, signal: dict) -> DrawingOutput:
        s = signal
        o_bar = s.get("O_bar", 0);  o_p = s.get("O_price", s.get("X_price", 0))
        x_bar = s["X_bar"];         x_p = s["X_price"]
        a_bar = s["A_bar"];         a_p = s["A_price"]
        b_bar = s["B_bar"];         b_p = s["B_price"]
        c_bar = s["C_bar"];         c_p = s["C_price"]
        direction = s["direction"]

        r_ab = round(abs(b_p - a_p) / abs(x_p - a_p), 3) if abs(x_p - a_p) > 0 else 0
        r_bc = round(abs(c_p - b_p) / abs(a_p - b_p), 3) if abs(a_p - b_p) > 0 else 0

        atr   = s.get("atr", abs(x_p - a_p) * 0.05)
        entry = c_p

        if direction == "LONG":
            sl  = c_p - atr * 2
            tp1 = c_p + abs(c_p - b_p)
            tp2 = c_p + abs(c_p - a_p)
            prz_clr = "color.green"; emoji = "🦈 SHARK BULLISH ⬆️"
        else:
            sl  = c_p + atr * 2
            tp1 = c_p - abs(c_p - b_p)
            tp2 = c_p - abs(c_p - a_p)
            prz_clr = "color.red"; emoji = "🦈 SHARK BEARISH ⬇️"

        pine = f"""
//@version=5
indicator("Shark {direction}", overlay=true)

// ── Segments ───────────────────────────────────────────
line.new({x_bar}, {x_p}, {a_bar}, {a_p}, color=color.blue,   width=2)  // XA
line.new({a_bar}, {a_p}, {b_bar}, {b_p}, color=color.orange, width=2)  // AB
line.new({b_bar}, {b_p}, {c_bar}, {c_p}, color=color.purple, width=3)  // BC→C

// ── Points ────────────────────────────────────────────
label.new({x_bar}, {x_p}, "X", style=label.style_label_right, color=color.blue,   textcolor=color.white, size=size.small)
label.new({a_bar}, {a_p}, "A", style=label.style_label_right, color=color.orange, textcolor=color.white, size=size.small)
label.new({b_bar}, {b_p}, "B", style=label.style_label_right, color=color.green,  textcolor=color.white, size=size.small)
label.new({c_bar}, {c_p}, "C\\n{emoji}", style=label.style_label_{'down' if direction == 'LONG' else 'up'},
    color={prz_clr}, textcolor=color.white, size=size.large)

// ── Ratios ────────────────────────────────────────────
label.new({(a_bar+b_bar)//2}, {(a_p+b_p)/2}, "AB/XA {r_ab}",
    style=label.style_label_right, color=color.orange, textcolor=color.white, size=size.tiny)
label.new({(b_bar+c_bar)//2}, {(b_p+c_p)/2}, "BC/AB {r_bc}",
    style=label.style_label_right, color=color.purple, textcolor=color.white, size=size.tiny)

// ── Zone C ────────────────────────────────────────────
box.new({c_bar} - 2, {c_p * 1.003}, {c_bar} + 2, {c_p * 0.997},
    bgcolor={prz_clr}, border_color={prz_clr}, border_width=3)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, direction)

        mql4_dir = "clrGreen" if direction == "LONG" else "clrRed"
        mql4 = f"""
ObjectCreate("SK_XA", OBJ_TREND, 0, Time[{b_bar}], {x_p}, Time[{a_bar}], {a_p});
ObjectSet("SK_XA", OBJPROP_COLOR, clrBlue); ObjectSet("SK_XA", OBJPROP_WIDTH, 2);
ObjectCreate("SK_AB", OBJ_TREND, 0, Time[{b_bar}], {a_p}, Time[{b_bar-a_bar}], {b_p});
ObjectSet("SK_AB", OBJPROP_COLOR, clrOrange); ObjectSet("SK_AB", OBJPROP_WIDTH, 2);
ObjectCreate("SK_BC", OBJ_TREND, 0, Time[{c_bar-b_bar}], {b_p}, Time[0], {c_p});
ObjectSet("SK_BC", OBJPROP_COLOR, clrViolet); ObjectSet("SK_BC", OBJPROP_WIDTH, 3);
ObjectCreate("SK_Lbl", OBJ_TEXT, 0, Time[0], {c_p});
ObjectSetText("SK_Lbl", "🦈 SHARK {direction} | AB={r_ab} BC={r_bc}", 10, "Arial Bold", {mql4_dir});
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, direction, "SHRK")

        return DrawingOutput(
            pattern_name="SHARK",
            direction=direction,
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description=f"🦈 Shark {direction} | AB={r_ab} BC={r_bc} | Entrée C={round(c_p,2)}",
            elements_drawn=["segments_xabc_couleurs","points_labels","ratios","zone_c","label","entree","sl","tp1","tp2"]
        )
