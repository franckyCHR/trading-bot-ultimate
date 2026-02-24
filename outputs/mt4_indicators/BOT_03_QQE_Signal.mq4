//+------------------------------------------------------------------+
//|  BOT_03_QQE_Signal.mq4                                          |
//|  QQE (Qualitative Quantitative Estimation) avec flèches          |
//|  Sous-fenêtre avec ligne rapide (Fast) et lente (Slow)           |
//|  Flèches au croisement : ↑ haussier, ↓ baissier                 |
//+------------------------------------------------------------------+
#property copyright   "Trading Bot Ultimate"
#property version     "1.00"
#property indicator_separate_window
#property indicator_buffers 4
#property indicator_plots   4

// ── Plot 1 : Ligne rapide (QQE Fast) ────────────────────────────────────────
#property indicator_label1  "QQE Fast"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrDodgerBlue
#property indicator_style1  STYLE_SOLID
#property indicator_width1  2

// ── Plot 2 : Ligne lente (QQE Slow / ATR smoothed) ──────────────────────────
#property indicator_label2  "QQE Slow"
#property indicator_type2   DRAW_LINE
#property indicator_color2  clrOrangeRed
#property indicator_style2  STYLE_SOLID
#property indicator_width2  1

// ── Plot 3 : Flèches haussières ──────────────────────────────────────────────
#property indicator_label3  "Cross Up"
#property indicator_type3   DRAW_ARROW
#property indicator_color3  clrLimeGreen
#property indicator_width3  2

// ── Plot 4 : Flèches baissières ──────────────────────────────────────────────
#property indicator_label4  "Cross Down"
#property indicator_type4   DRAW_ARROW
#property indicator_color4  clrTomato
#property indicator_width4  2

// ── Paramètres ──────────────────────────────────────────────────────────────
input int    RSI_Period   = 14;   // Période RSI de base
input double SF           = 4.238; // Facteur de lissage QQE
input int    ATR_Period   = 10;   // Période ATR pour la bande
input double ATR_Factor   = 4.236; // Multiplicateur ATR

// ── Buffers ─────────────────────────────────────────────────────────────────
double BufFast[];    // Ligne rapide
double BufSlow[];    // Ligne lente (bande ATR)
double BufUp[];      // Flèches haussières
double BufDown[];    // Flèches baissières

// ── Variables internes ───────────────────────────────────────────────────────
double prevRSI[], smRSI[];
double trLevelUp[], trLevelDown[];

//+------------------------------------------------------------------+
int OnInit()
{
   SetIndexBuffer(0, BufFast,  INDICATOR_DATA);
   SetIndexBuffer(1, BufSlow,  INDICATOR_DATA);
   SetIndexBuffer(2, BufUp,    INDICATOR_DATA);
   SetIndexBuffer(3, BufDown,  INDICATOR_DATA);

   // Code WINGDINGS pour les flèches
   PlotIndexSetInteger(2, PLOT_ARROW, 233); // flèche haut
   PlotIndexSetInteger(3, PLOT_ARROW, 234); // flèche bas

   ArraySetAsSeries(BufFast,  true);
   ArraySetAsSeries(BufSlow,  true);
   ArraySetAsSeries(BufUp,    true);
   ArraySetAsSeries(BufDown,  true);

   IndicatorSetString(INDICATOR_SHORTNAME, "QQE Signal");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   if (rates_total < RSI_Period + ATR_Period + 2) return(0);

   ArraySetAsSeries(close, true);
   ArraySetAsSeries(high,  true);
   ArraySetAsSeries(low,   true);

   int limit = rates_total - prev_calculated;
   if (prev_calculated > 0) limit++;

   // ── Calcul RSI lissé ────────────────────────────────────────────
   ArrayResize(prevRSI, rates_total);
   ArrayResize(smRSI,   rates_total);
   ArrayResize(trLevelUp,   rates_total);
   ArrayResize(trLevelDown, rates_total);

   for (int i = rates_total - 2; i >= 0; i--)
   {
      // RSI brut via iRSI
      double rsi = iRSI(NULL, 0, RSI_Period, PRICE_CLOSE, i);

      // EMA du RSI (facteur SF)
      if (i == rates_total - 2)
         smRSI[i] = rsi;
      else
      {
         double k = 2.0 / (SF + 1.0);
         smRSI[i] = smRSI[i+1] + k * (rsi - smRSI[i+1]);
      }

      BufFast[i] = smRSI[i];

      // ── ATR sur le RSI lissé ────────────────────────────────────
      if (i > rates_total - ATR_Period - 2)
      {
         BufSlow[i]  = smRSI[i];
         BufUp[i]    = EMPTY_VALUE;
         BufDown[i]  = EMPTY_VALUE;
         trLevelUp[i]   = smRSI[i];
         trLevelDown[i] = smRSI[i];
         continue;
      }

      // ATR du RSI : amplitude moyenne sur ATR_Period
      double atrRsi = 0;
      for (int k2 = 0; k2 < ATR_Period; k2++)
      {
         if (i + k2 + 1 < rates_total)
            atrRsi += MathAbs(smRSI[i + k2] - smRSI[i + k2 + 1]);
      }
      atrRsi /= ATR_Period;
      double dar = ATR_Factor * atrRsi;

      // Trailing stop du QQE
      double newLong  = smRSI[i] - dar;
      double newShort = smRSI[i] + dar;

      // Ligne lente = trailing stop côté tendance
      double prevSlow = (i + 1 < rates_total) ? BufSlow[i+1] : smRSI[i];
      double prevFast = (i + 1 < rates_total) ? BufFast[i+1] : smRSI[i];

      if (smRSI[i] > prevSlow)
         BufSlow[i] = MathMax(prevSlow, newLong);
      else
         BufSlow[i] = MathMin(prevSlow, newShort);

      BufUp[i]   = EMPTY_VALUE;
      BufDown[i] = EMPTY_VALUE;

      // ── Détection de croisement ──────────────────────────────────
      if (i + 1 < rates_total)
      {
         bool crossUp   = (BufFast[i] > BufSlow[i]) && (BufFast[i+1] <= BufSlow[i+1]);
         bool crossDown = (BufFast[i] < BufSlow[i]) && (BufFast[i+1] >= BufSlow[i+1]);

         if (crossUp)
            BufUp[i]   = BufSlow[i] - 2.0;   // position légèrement sous la ligne
         if (crossDown)
            BufDown[i] = BufSlow[i] + 2.0;   // position légèrement sur la ligne
      }
   }

   return(rates_total);
}
