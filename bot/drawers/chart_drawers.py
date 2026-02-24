"""
chart_drawers.py
────────────────
Drawers pour toutes les figures chartistes classiques.
Chaque classe produit du Pine Script + MQL4 prêt à coller.
"""

from .base_drawer import BaseDrawer, DrawingOutput


class HeadShouldersDrawer(BaseDrawer):
    """Épaule-Tête-Épaule — Bearish"""

    def draw(self, signal: dict) -> DrawingOutput:
        s         = signal
        eg_bar    = s["left_shoulder_bar"]
        eg_price  = s["left_shoulder_price"]
        tete_bar  = s["head_bar"]
        tete_price= s["head_price"]
        ed_bar    = s["right_shoulder_bar"]
        ed_price  = s["right_shoulder_price"]
        neck      = s["neckline"]
        entry     = neck
        hauteur   = tete_price - neck
        sl        = ed_price + s.get("atr", hauteur * 0.1)
        tp1       = neck - hauteur * 0.5
        tp2       = neck - hauteur

        pine = f"""
//@version=5
indicator("ETE Bearish", overlay=true)

// ── Points de la figure ────────────────────────────────
label.new({eg_bar},  {eg_price},  "👈 Ép.G\\n{round(eg_price,2)}",
    style=label.style_label_down, color=color.blue, textcolor=color.white, size=size.small)
label.new({tete_bar}, {tete_price}, "👑 TÊTE\\n{round(tete_price,2)}",
    style=label.style_label_down, color=color.red, textcolor=color.white, size=size.large)
label.new({ed_bar},  {ed_price},  "Ép.D 👉\\n{round(ed_price,2)}",
    style=label.style_label_down, color=color.blue, textcolor=color.white, size=size.small)

// ── Lignes reliant les sommets ─────────────────────────
line.new({eg_bar}, {eg_price}, {tete_bar}, {tete_price}, color=color.red, width=2)
line.new({tete_bar}, {tete_price}, {ed_bar}, {ed_price}, color=color.red, width=2)

// ── Neckline ───────────────────────────────────────────
line.new({eg_bar}, {neck}, bar_index + 15, {neck},
    color=color.red, width=2, style=line.style_dashed)
label.new(bar_index + 15, {neck}, "Neckline {round(neck,2)}",
    style=label.style_label_left, color=color.red, textcolor=color.white, size=size.small)

// ── Zone colorée ───────────────────────────────────────
box.new({eg_bar}, {max(eg_price, tete_price, ed_price) * 1.001},
        {ed_bar}, {neck},
        bgcolor=color.new(color.red, 85), border_color=color.red, border_width=1)

// ── Label principal ────────────────────────────────────
label.new({tete_bar}, {tete_price * 1.003},
    text  = "🔴 ETE BEARISH\\n⬇️ Entrée: {round(entry,2)}",
    style = label.style_label_down,
    color = color.red, textcolor = color.white, size = size.large)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, "SHORT")

        mql4 = f"""
// ETE Bearish — MT4
ObjectCreate("ETE_EG",   OBJ_TEXT, 0, Time[bar_index-{tete_bar-eg_bar}],  {eg_price});
ObjectSetText("ETE_EG",   "👈 ÉP.G",  10, "Arial Bold", clrBlue);
ObjectCreate("ETE_HEAD", OBJ_TEXT, 0, Time[0], {tete_price});
ObjectSetText("ETE_HEAD", "👑 TÊTE",  12, "Arial Bold", clrRed);
ObjectCreate("ETE_ED",   OBJ_TEXT, 0, Time[bar_index-{ed_bar-tete_bar}],  {ed_price});
ObjectSetText("ETE_ED",   "ÉP.D 👉",  10, "Arial Bold", clrBlue);

ObjectCreate("ETE_L1", OBJ_TREND, 0,
    Time[bar_index-{tete_bar-eg_bar}], {eg_price},
    Time[bar_index-{ed_bar-tete_bar}], {tete_price});
ObjectSet("ETE_L1", OBJPROP_COLOR, clrRed); ObjectSet("ETE_L1", OBJPROP_WIDTH, 2);

ObjectCreate("ETE_Neck", OBJ_HLINE, 0, 0, {neck});
ObjectSet("ETE_Neck", OBJPROP_COLOR, clrRed);
ObjectSet("ETE_Neck", OBJPROP_STYLE, STYLE_DASH);
ObjectSet("ETE_Neck", OBJPROP_WIDTH, 2);

ObjectCreate("ETE_Zone", OBJ_RECTANGLE, 0,
    Time[bar_index-{tete_bar-eg_bar}], {max(eg_price, tete_price, ed_price)},
    Time[0], {neck});
ObjectSet("ETE_Zone", OBJPROP_COLOR, clrRed);
ObjectSet("ETE_Zone", OBJPROP_BACK, true);
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, "SHORT", "ETE")

        return DrawingOutput(
            pattern_name="ETE", direction="SHORT",
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description=f"ETE Bearish | Neckline={round(neck,2)} | Tête={round(tete_price,2)}",
            elements_drawn=["3_sommets","lignes_ete","neckline","zone_rouge","label","entree","sl","tp1","tp2"]
        )


class InverseHSDrawer(BaseDrawer):
    """ETE Inversé — Bullish"""

    def draw(self, signal: dict) -> DrawingOutput:
        s         = signal
        eg_bar    = s["left_shoulder_bar"]
        eg_price  = s["left_shoulder_price"]
        tete_bar  = s["head_bar"]
        tete_price= s["head_price"]
        ed_bar    = s["right_shoulder_bar"]
        ed_price  = s["right_shoulder_price"]
        neck      = s["neckline"]
        entry     = neck
        hauteur   = neck - tete_price
        sl        = ed_price - s.get("atr", hauteur * 0.1)
        tp1       = neck + hauteur * 0.5
        tp2       = neck + hauteur

        pine = f"""
//@version=5
indicator("ETE Inversé Bullish", overlay=true)
label.new({eg_bar},  {eg_price},  "👈 Ép.G", style=label.style_label_up,   color=color.blue,  textcolor=color.white)
label.new({tete_bar},{tete_price},"👑 TÊTE",  style=label.style_label_up,   color=color.green, textcolor=color.white, size=size.large)
label.new({ed_bar},  {ed_price},  "Ép.D 👉", style=label.style_label_up,   color=color.blue,  textcolor=color.white)
line.new({eg_bar}, {eg_price}, {tete_bar}, {tete_price}, color=color.green, width=2)
line.new({tete_bar},{tete_price},{ed_bar},  {ed_price},  color=color.green, width=2)
line.new({eg_bar}, {neck}, bar_index + 15, {neck},
    color=color.green, width=2, style=line.style_dashed)
box.new({eg_bar}, {neck}, {ed_bar}, {min(eg_price,tete_price,ed_price)*0.999},
    bgcolor=color.new(color.green, 85), border_color=color.green)
label.new({tete_bar},{tete_price*0.997}, "🟢 ETE INV BULLISH\\n⬆️ Entrée: {round(entry,2)}",
    style=label.style_label_up, color=color.green, textcolor=color.white, size=size.large)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, "LONG")

        mql4 = f"""
ObjectCreate("ETEI_Neck", OBJ_HLINE, 0, 0, {neck});
ObjectSet("ETEI_Neck", OBJPROP_COLOR, clrGreen);
ObjectSet("ETEI_Neck", OBJPROP_STYLE, STYLE_DASH); ObjectSet("ETEI_Neck", OBJPROP_WIDTH, 2);
ObjectCreate("ETEI_Zone", OBJ_RECTANGLE, 0,
    Time[bar_index-{tete_bar-eg_bar}], {neck},
    Time[0], {min(eg_price,tete_price,ed_price)});
ObjectSet("ETEI_Zone", OBJPROP_COLOR, clrGreen); ObjectSet("ETEI_Zone", OBJPROP_BACK, true);
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, "LONG", "ETEI")

        return DrawingOutput(
            pattern_name="ETE_INVERSE", direction="LONG",
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description=f"ETE Inversé Bullish | Neckline={round(neck,2)}",
            elements_drawn=["3_creux","neckline","zone_verte","label","entree","sl","tp1","tp2"]
        )


class DoubleTopDrawer(BaseDrawer):
    """Double Top (M) — Bearish"""

    def draw(self, signal: dict) -> DrawingOutput:
        s       = signal
        t1_bar  = s["top1_bar"];    t1 = s["top1_price"]
        t2_bar  = s["top2_bar"];    t2 = s["top2_price"]
        valley  = s["valley"];      atr = s.get("atr", abs(t1 - valley) * 0.1)
        entry   = valley
        hauteur = max(t1, t2) - valley
        sl      = max(t1, t2) + atr
        tp1     = valley - hauteur * 0.5
        tp2     = valley - hauteur

        pine = f"""
//@version=5
indicator("Double Top M", overlay=true)
line.new({t1_bar}, {t1}, {t2_bar}, {t2}, color=color.red, width=2)
line.new({t1_bar}, {valley}, bar_index + 10, {valley},
    color=color.orange, width=2, style=line.style_dashed)
box.new({t1_bar}, {max(t1,t2)*1.001}, {t2_bar}, {valley},
    bgcolor=color.new(color.red, 85), border_color=color.red)
label.new({t1_bar}, {t1}, "🔴 Top 1\\n{round(t1,2)}", style=label.style_label_down, color=color.red, textcolor=color.white)
label.new({t2_bar}, {t2}, "🔴 Top 2\\n{round(t2,2)}", style=label.style_label_down, color=color.red, textcolor=color.white)
label.new({t1_bar + (t2_bar-t1_bar)//2}, {max(t1,t2)*1.003}, "M ⬇️ DOUBLE TOP",
    style=label.style_label_down, color=color.red, textcolor=color.white, size=size.large)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, "SHORT")

        mql4 = f"""
ObjectCreate("DT_Line", OBJ_TREND, 0, Time[bar_index-{t2_bar-t1_bar}], {t1}, Time[0], {t2});
ObjectSet("DT_Line", OBJPROP_COLOR, clrRed); ObjectSet("DT_Line", OBJPROP_WIDTH, 2);
ObjectCreate("DT_Valley", OBJ_HLINE, 0, 0, {valley});
ObjectSet("DT_Valley", OBJPROP_COLOR, clrOrange); ObjectSet("DT_Valley", OBJPROP_STYLE, STYLE_DASH);
ObjectCreate("DT_Zone", OBJ_RECTANGLE, 0,
    Time[bar_index-{t2_bar-t1_bar}], {max(t1,t2)}, Time[0], {valley});
ObjectSet("DT_Zone", OBJPROP_COLOR, clrRed); ObjectSet("DT_Zone", OBJPROP_BACK, true);
ObjectCreate("DT_Lbl", OBJ_TEXT, 0, Time[0], {max(t1,t2)});
ObjectSetText("DT_Lbl", "M ⬇️ DOUBLE TOP", 11, "Arial Bold", clrRed);
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, "SHORT", "DT")

        return DrawingOutput(
            pattern_name="DOUBLE_TOP", direction="SHORT",
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description=f"Double Top M | Top1={round(t1,2)} Top2={round(t2,2)} Valley={round(valley,2)}",
            elements_drawn=["ligne_m","valley_line","zone_rouge","labels","entree","sl","tp1","tp2"]
        )


class DoubleBottomDrawer(BaseDrawer):
    """Double Bottom (W) — Bullish"""

    def draw(self, signal: dict) -> DrawingOutput:
        s      = signal
        b1_bar = s["bot1_bar"];  b1 = s["bot1_price"]
        b2_bar = s["bot2_bar"];  b2 = s["bot2_price"]
        peak   = s["peak"];      atr = s.get("atr", abs(peak - b1) * 0.1)
        entry  = peak
        hauteur = peak - min(b1, b2)
        sl     = min(b1, b2) - atr
        tp1    = peak + hauteur * 0.5
        tp2    = peak + hauteur

        pine = f"""
//@version=5
indicator("Double Bottom W", overlay=true)
line.new({b1_bar}, {b1}, {b2_bar}, {b2}, color=color.green, width=2)
line.new({b1_bar}, {peak}, bar_index + 10, {peak},
    color=color.orange, width=2, style=line.style_dashed)
box.new({b1_bar}, {peak}, {b2_bar}, {min(b1,b2)*0.999},
    bgcolor=color.new(color.green, 85), border_color=color.green)
label.new({b1_bar}, {b1}, "🟢 Bot 1\\n{round(b1,2)}", style=label.style_label_up, color=color.green, textcolor=color.white)
label.new({b2_bar}, {b2}, "🟢 Bot 2\\n{round(b2,2)}", style=label.style_label_up, color=color.green, textcolor=color.white)
label.new({b1_bar + (b2_bar-b1_bar)//2}, {min(b1,b2)*0.997}, "W ⬆️ DOUBLE BOTTOM",
    style=label.style_label_up, color=color.green, textcolor=color.white, size=size.large)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, "LONG")

        mql4 = f"""
ObjectCreate("DB_Zone", OBJ_RECTANGLE, 0,
    Time[bar_index-{b2_bar-b1_bar}], {peak}, Time[0], {min(b1,b2)});
ObjectSet("DB_Zone", OBJPROP_COLOR, clrGreen); ObjectSet("DB_Zone", OBJPROP_BACK, true);
ObjectCreate("DB_Lbl", OBJ_TEXT, 0, Time[0], {min(b1,b2)});
ObjectSetText("DB_Lbl", "W ⬆️ DOUBLE BOTTOM", 11, "Arial Bold", clrGreen);
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, "LONG", "DB")

        return DrawingOutput(
            pattern_name="DOUBLE_BOTTOM", direction="LONG",
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description=f"Double Bottom W | Bot1={round(b1,2)} Bot2={round(b2,2)} Peak={round(peak,2)}",
            elements_drawn=["ligne_w","peak_line","zone_verte","labels","entree","sl","tp1","tp2"]
        )


class BullFlagDrawer(BaseDrawer):
    """Drapeau Haussier — Bullish"""

    def draw(self, signal: dict) -> DrawingOutput:
        s          = signal
        mat_start  = s.get("mat_start_bar", 0);   mat_low  = s["mat_low"]
        mat_end    = s.get("mat_end_bar", 0);     mat_high = s["mat_high"]
        flag_high  = s["flag_canal_high"]
        flag_low   = s["flag_canal_low"]
        entry      = flag_high
        hauteur    = mat_high - mat_low
        sl         = flag_low - s.get("atr", hauteur * 0.05)
        tp1        = entry + hauteur * 0.5
        tp2        = entry + hauteur

        pine = f"""
//@version=5
indicator("Bull Flag", overlay=true)
// Mât
box.new({mat_start}, {mat_high}, {mat_end}, {mat_low},
    bgcolor=color.new(color.blue, 75), border_color=color.blue, border_width=2)
label.new({mat_start + (mat_end-mat_start)//2}, {mat_high}, "🏁 MÂT",
    style=label.style_label_down, color=color.blue, textcolor=color.white)
// Canal du drapeau
line.new({mat_end}, {flag_high}, bar_index, {flag_high * 0.998},
    color=color.orange, width=2)
line.new({mat_end}, {flag_low},  bar_index, {flag_low  * 1.002},
    color=color.orange, width=2)
box.new({mat_end}, {flag_high}, bar_index, {flag_low},
    bgcolor=color.new(color.orange, 85), border_color=color.orange)
label.new(bar_index, {flag_high}, "🚩 BULL FLAG ⬆️",
    style=label.style_label_down, color=color.green, textcolor=color.white, size=size.large)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, "LONG")

        mql4 = f"""
ObjectCreate("BF_Mat", OBJ_RECTANGLE, 0,
    Time[bar_index-{mat_end-mat_start}], {mat_high}, Time[bar_index-{mat_end-mat_start}+{mat_end-mat_start}], {mat_low});
ObjectSet("BF_Mat", OBJPROP_COLOR, clrBlue); ObjectSet("BF_Mat", OBJPROP_BACK, true);
ObjectCreate("BF_Flag", OBJ_RECTANGLE, 0,
    Time[bar_index-{mat_end}], {flag_high}, Time[0], {flag_low});
ObjectSet("BF_Flag", OBJPROP_COLOR, clrOrange); ObjectSet("BF_Flag", OBJPROP_BACK, true);
ObjectCreate("BF_Lbl", OBJ_TEXT, 0, Time[0], {flag_high});
ObjectSetText("BF_Lbl", "🚩 BULL FLAG ⬆️", 11, "Arial Bold", clrGreen);
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, "LONG", "BF")

        return DrawingOutput(
            pattern_name="BULL_FLAG", direction="LONG",
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description=f"Bull Flag | Mât={round(hauteur,2)} | Canal {round(flag_low,2)}→{round(flag_high,2)}",
            elements_drawn=["mat_bleu","canal_orange","label","entree","sl","tp1","tp2"]
        )


class BearFlagDrawer(BaseDrawer):
    """Drapeau Baissier — Bearish"""

    def draw(self, signal: dict) -> DrawingOutput:
        s         = signal
        mat_high  = s["mat_high"];   mat_low  = s["mat_low"]
        flag_high = s["flag_canal_high"]
        flag_low  = s["flag_canal_low"]
        mat_start = s.get("mat_start_bar", 0)
        mat_end   = s.get("mat_end_bar", 0)
        entry     = flag_low
        hauteur   = mat_high - mat_low
        sl        = flag_high + s.get("atr", hauteur * 0.05)
        tp1       = entry - hauteur * 0.5
        tp2       = entry - hauteur

        pine = f"""
//@version=5
indicator("Bear Flag", overlay=true)
box.new({mat_start}, {mat_high}, {mat_end}, {mat_low},
    bgcolor=color.new(color.red, 75), border_color=color.red, border_width=2)
line.new({mat_end}, {flag_high}, bar_index, {flag_high * 1.001}, color=color.orange, width=2)
line.new({mat_end}, {flag_low},  bar_index, {flag_low  * 0.999}, color=color.orange, width=2)
box.new({mat_end}, {flag_high}, bar_index, {flag_low},
    bgcolor=color.new(color.orange, 85), border_color=color.orange)
label.new(bar_index, {flag_low}, "🚩 BEAR FLAG ⬇️",
    style=label.style_label_up, color=color.red, textcolor=color.white, size=size.large)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, "SHORT")

        mql4 = f"""
ObjectCreate("BeF_Mat", OBJ_RECTANGLE, 0, Time[{mat_end}], {mat_high}, Time[{mat_start}], {mat_low});
ObjectSet("BeF_Mat", OBJPROP_COLOR, clrRed); ObjectSet("BeF_Mat", OBJPROP_BACK, true);
ObjectCreate("BeF_Lbl", OBJ_TEXT, 0, Time[0], {flag_low});
ObjectSetText("BeF_Lbl", "🚩 BEAR FLAG ⬇️", 11, "Arial Bold", clrRed);
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, "SHORT", "BeF")

        return DrawingOutput(
            pattern_name="BEAR_FLAG", direction="SHORT",
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description=f"Bear Flag | Mât={round(hauteur,2)}",
            elements_drawn=["mat_rouge","canal_orange","label","entree","sl","tp1","tp2"]
        )


class RisingWedgeDrawer(BaseDrawer):
    """Biseau Ascendant — Bearish"""

    def draw(self, signal: dict) -> DrawingOutput:
        s     = signal
        start = s.get("wedge_start_bar", 0)
        res_s = s["resistance_start"];  res_e = s["resistance_end"]
        sup_s = s["support_start"];     sup_e = s["support_end"]
        entry = sup_e
        largeur = res_s - sup_s
        sl    = res_e + s.get("atr", largeur * 0.05)
        tp1   = entry - largeur * 0.5
        tp2   = entry - largeur

        pine = f"""
//@version=5
indicator("Biseau Ascendant", overlay=true)
var r_line = line.new({start}, {res_s}, bar_index, {res_e}, color=color.red,   width=2)
var s_line = line.new({start}, {sup_s}, bar_index, {sup_e}, color=color.orange, width=2)
linefill.new(r_line, s_line, color=color.new(color.red, 85))
label.new(bar_index, {res_e}, "📐 BISEAU ASCENDANT ⬇️",
    style=label.style_label_down, color=color.red, textcolor=color.white, size=size.large)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, "SHORT")

        mql4 = f"""
ObjectCreate("RW_Res", OBJ_TREND, 0, Time[{start}], {res_s}, Time[0], {res_e});
ObjectSet("RW_Res", OBJPROP_COLOR, clrRed); ObjectSet("RW_Res", OBJPROP_WIDTH, 2);
ObjectCreate("RW_Sup", OBJ_TREND, 0, Time[{start}], {sup_s}, Time[0], {sup_e});
ObjectSet("RW_Sup", OBJPROP_COLOR, clrOrange); ObjectSet("RW_Sup", OBJPROP_WIDTH, 2);
ObjectCreate("RW_Lbl", OBJ_TEXT, 0, Time[0], {res_e});
ObjectSetText("RW_Lbl", "📐 BISEAU ASC ⬇️", 11, "Arial Bold", clrRed);
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, "SHORT", "RW")

        return DrawingOutput(
            pattern_name="BISEAU_ASCENDANT", direction="SHORT",
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description="Biseau Ascendant Bearish — convergence haussière = piège",
            elements_drawn=["trendlines_convergentes","zone_rouge","label","entree","sl","tp1","tp2"]
        )


class FallingWedgeDrawer(BaseDrawer):
    """Biseau Descendant — Bullish"""

    def draw(self, signal: dict) -> DrawingOutput:
        s     = signal
        start = s.get("wedge_start_bar", 0)
        res_s = s["resistance_start"];  res_e = s["resistance_end"]
        sup_s = s["support_start"];     sup_e = s["support_end"]
        entry = res_e
        largeur = res_s - sup_s
        sl    = sup_e - s.get("atr", largeur * 0.05)
        tp1   = entry + largeur * 0.5
        tp2   = entry + largeur

        pine = f"""
//@version=5
indicator("Biseau Descendant", overlay=true)
var r_line = line.new({start}, {res_s}, bar_index, {res_e}, color=color.red,   width=2)
var s_line = line.new({start}, {sup_s}, bar_index, {sup_e}, color=color.green, width=2)
linefill.new(r_line, s_line, color=color.new(color.green, 85))
label.new(bar_index, {res_e}, "📐 BISEAU DESCENDANT ⬆️",
    style=label.style_label_up, color=color.green, textcolor=color.white, size=size.large)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, "LONG")

        mql4 = f"""
ObjectCreate("FW_Res", OBJ_TREND, 0, Time[{start}], {res_s}, Time[0], {res_e});
ObjectSet("FW_Res", OBJPROP_COLOR, clrRed); ObjectSet("FW_Res", OBJPROP_WIDTH, 2);
ObjectCreate("FW_Sup", OBJ_TREND, 0, Time[{start}], {sup_s}, Time[0], {sup_e});
ObjectSet("FW_Sup", OBJPROP_COLOR, clrGreen); ObjectSet("FW_Sup", OBJPROP_WIDTH, 2);
ObjectCreate("FW_Lbl", OBJ_TEXT, 0, Time[0], {sup_e});
ObjectSetText("FW_Lbl", "📐 BISEAU DESC ⬆️", 11, "Arial Bold", clrGreen);
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, "LONG", "FW")

        return DrawingOutput(
            pattern_name="BISEAU_DESCENDANT", direction="LONG",
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description="Biseau Descendant Bullish — convergence baissière = rebond",
            elements_drawn=["trendlines_convergentes","zone_verte","label","entree","sl","tp1","tp2"]
        )


class AscendingTriangleDrawer(BaseDrawer):
    """Triangle Ascendant — Bullish"""

    def draw(self, signal: dict) -> DrawingOutput:
        s        = signal
        start    = s.get("triangle_start_bar", 0)
        res      = s["resistance_level"]
        sup_s    = s["support_start"];   sup_e = s["support_end"]
        entry    = res
        hauteur  = res - sup_s
        sl       = sup_e - s.get("atr", hauteur * 0.05)
        tp1      = entry + hauteur * 0.5
        tp2      = entry + hauteur

        pine = f"""
//@version=5
indicator("Triangle Ascendant", overlay=true)
line.new({start}, {res}, bar_index + 10, {res}, color=color.green, width=3)
var s_line = line.new({start}, {sup_s}, bar_index, {sup_e}, color=color.green, width=2)
var r_line = line.new({start}, {res},   bar_index, {res},   color=color.green, width=3)
linefill.new(r_line, s_line, color=color.new(color.green, 88))
label.new(bar_index, {res * 1.002}, "📐 TRIANGLE ASC ⬆️",
    style=label.style_label_down, color=color.green, textcolor=color.white, size=size.large)
label.new({start}, {res}, "Résistance {round(res,2)}",
    style=label.style_label_right, color=color.green, textcolor=color.white, size=size.small)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, "LONG")

        mql4 = f"""
ObjectCreate("AT_Res", OBJ_HLINE, 0, 0, {res});
ObjectSet("AT_Res", OBJPROP_COLOR, clrGreen); ObjectSet("AT_Res", OBJPROP_WIDTH, 3);
ObjectCreate("AT_Sup", OBJ_TREND, 0, Time[{start}], {sup_s}, Time[0], {sup_e});
ObjectSet("AT_Sup", OBJPROP_COLOR, clrGreen); ObjectSet("AT_Sup", OBJPROP_WIDTH, 2);
ObjectCreate("AT_Lbl", OBJ_TEXT, 0, Time[0], {res});
ObjectSetText("AT_Lbl", "📐 TRIANGLE ASC ⬆️", 11, "Arial Bold", clrGreen);
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, "LONG", "AT")

        return DrawingOutput(
            pattern_name="TRIANGLE_ASCENDANT", direction="LONG",
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description=f"Triangle Ascendant | Résistance plate={round(res,2)}",
            elements_drawn=["resistance_horizontale","support_diagonal","zone_verte","label","entree","sl","tp1","tp2"]
        )


class DescendingTriangleDrawer(BaseDrawer):
    """Triangle Descendant — Bearish"""

    def draw(self, signal: dict) -> DrawingOutput:
        s       = signal
        start   = s.get("triangle_start_bar", 0)
        sup     = s["support_level"]
        res_s   = s["resistance_start"];  res_e = s["resistance_end"]
        entry   = sup
        hauteur = res_s - sup
        sl      = res_e + s.get("atr", hauteur * 0.05)
        tp1     = entry - hauteur * 0.5
        tp2     = entry - hauteur

        pine = f"""
//@version=5
indicator("Triangle Descendant", overlay=true)
line.new({start}, {sup}, bar_index + 10, {sup}, color=color.red, width=3)
var s_line = line.new({start}, {sup},   bar_index, {sup},   color=color.red, width=3)
var r_line = line.new({start}, {res_s}, bar_index, {res_e}, color=color.red, width=2)
linefill.new(r_line, s_line, color=color.new(color.red, 88))
label.new(bar_index, {sup * 0.998}, "📐 TRIANGLE DESC ⬇️",
    style=label.style_label_up, color=color.red, textcolor=color.white, size=size.large)
""" + self._pine_entry_lines(entry, sl, tp1, tp2, "SHORT")

        mql4 = f"""
ObjectCreate("DT_Sup", OBJ_HLINE, 0, 0, {sup});
ObjectSet("DT_Sup", OBJPROP_COLOR, clrRed); ObjectSet("DT_Sup", OBJPROP_WIDTH, 3);
ObjectCreate("DT_Res", OBJ_TREND, 0, Time[{start}], {res_s}, Time[0], {res_e});
ObjectSet("DT_Res", OBJPROP_COLOR, clrRed); ObjectSet("DT_Res", OBJPROP_WIDTH, 2);
ObjectCreate("DT2_Lbl", OBJ_TEXT, 0, Time[0], {sup});
ObjectSetText("DT2_Lbl", "📐 TRIANGLE DESC ⬇️", 11, "Arial Bold", clrRed);
""" + self._mql4_entry_lines(entry, sl, tp1, tp2, "SHORT", "DTr")

        return DrawingOutput(
            pattern_name="TRIANGLE_DESCENDANT", direction="SHORT",
            entry_price=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            pine_script=pine, mql4_script=mql4,
            description=f"Triangle Descendant | Support plat={round(sup,2)}",
            elements_drawn=["support_horizontal","resistance_diagonal","zone_rouge","label","entree","sl","tp1","tp2"]
        )


class SymmetricTriangleDrawer(BaseDrawer):
    """Triangle Symétrique — Neutre, attendre cassure"""

    def draw(self, signal: dict) -> DrawingOutput:
        s       = signal
        start   = s.get("triangle_start_bar", 0)
        res_s   = s["resistance_start"];  res_e = s["resistance_end"]
        sup_s   = s["support_start"];     sup_e = s["support_end"]
        mid     = (res_e + sup_e) / 2
        hauteur = res_s - sup_s
        entry_long  = res_e
        entry_short = sup_e
        sl_long  = sup_e - s.get("atr", hauteur * 0.05)
        sl_short = res_e + s.get("atr", hauteur * 0.05)

        pine = f"""
//@version=5
indicator("Triangle Symétrique", overlay=true)
var r_line = line.new({start}, {res_s}, bar_index, {res_e}, color=color.red,    width=2)
var s_line = line.new({start}, {sup_s}, bar_index, {sup_e}, color=color.orange, width=2)
linefill.new(r_line, s_line, color=color.new(color.yellow, 80))
label.new(bar_index, {mid}, "📐 TRIANGLE SYM\\n⚡ ATTENDRE CASSURE",
    style=label.style_label_center, color=color.yellow, textcolor=color.black, size=size.large)
label.new(bar_index + 5, {res_e}, "Si ⬆️ cassure → Long {round(entry_long,2)}",
    style=label.style_label_left, color=color.green, textcolor=color.white, size=size.small)
label.new(bar_index + 5, {sup_e}, "Si ⬇️ cassure → Short {round(entry_short,2)}",
    style=label.style_label_left, color=color.red,   textcolor=color.white, size=size.small)
"""

        mql4 = f"""
ObjectCreate("ST_Res", OBJ_TREND, 0, Time[{start}], {res_s}, Time[0], {res_e});
ObjectSet("ST_Res", OBJPROP_COLOR, clrRed); ObjectSet("ST_Res", OBJPROP_WIDTH, 2);
ObjectCreate("ST_Sup", OBJ_TREND, 0, Time[{start}], {sup_s}, Time[0], {sup_e});
ObjectSet("ST_Sup", OBJPROP_COLOR, clrOrange); ObjectSet("ST_Sup", OBJPROP_WIDTH, 2);
ObjectCreate("ST_Lbl", OBJ_TEXT, 0, Time[0], {mid});
ObjectSetText("ST_Lbl", "📐 TRIANGLE SYM ⚡ ATTENDRE", 11, "Arial Bold", clrYellow);
"""

        return DrawingOutput(
            pattern_name="TRIANGLE_SYMETRIQUE", direction="NEUTRE",
            entry_price=mid, stop_loss=0, tp1=0, tp2=0,
            pine_script=pine, mql4_script=mql4,
            description="Triangle Symétrique — attendre cassure d'un côté",
            elements_drawn=["trendlines_convergentes","zone_jaune","label_double_option"]
        )
