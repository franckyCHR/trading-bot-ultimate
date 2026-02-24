//+------------------------------------------------------------------+
//|  BOT_03_QQE_Signal.mq4                                          |
//|  QQE (Qualitative Quantitative Estimation) avec flèches          |
//|  Sous-fenêtre : ligne rapide (bleue) / lente (rouge)            |
//|  Flèche ↑ croisement haussier | Flèche ↓ croisement baissier    |
//+------------------------------------------------------------------+
#property copyright   "Trading Bot Ultimate"
#property version     "1.00"
#property indicator_separate_window
#property indicator_buffers 4
#property indicator_color1  DodgerBlue
#property indicator_color2  Red
#property indicator_color3  Lime
#property indicator_color4  Red
#property indicator_width1  2
#property indicator_width2  1
#property indicator_width3  2
#property indicator_width4  2
#property indicator_minimum 0
#property indicator_maximum 100

// ── Paramètres ──────────────────────────────────────────────────────────────
input int    RSI_Period   = 14;    // Période RSI de base
input double SF           = 4.238; // Facteur de lissage QQE
input int    ATR_Period   = 10;    // Période ATR pour la bande
input double ATR_Factor   = 4.236; // Multiplicateur ATR

// ── Buffers ─────────────────────────────────────────────────────────────────
double BufFast[];    // Ligne rapide (bleu)
double BufSlow[];    // Ligne lente  (rouge)
double BufUp[];      // Flèches haussières (vert)
double BufDown[];    // Flèches baissières (rouge)

//+------------------------------------------------------------------+
int OnInit()
{
   SetIndexBuffer(0, BufFast);
   SetIndexBuffer(1, BufSlow);
   SetIndexBuffer(2, BufUp);
   SetIndexBuffer(3, BufDown);

   SetIndexStyle(0, DRAW_LINE,  STYLE_SOLID, 2, DodgerBlue);
   SetIndexStyle(1, DRAW_LINE,  STYLE_SOLID, 1, Red);
   SetIndexStyle(2, DRAW_ARROW, STYLE_SOLID, 2, Lime);
   SetIndexStyle(3, DRAW_ARROW, STYLE_SOLID, 2, Red);

   SetIndexArrow(2, 233);  // flèche haut ↑
   SetIndexArrow(3, 234);  // flèche bas  ↓

   SetIndexEmptyValue(2, EMPTY_VALUE);
   SetIndexEmptyValue(3, EMPTY_VALUE);

   SetIndexLabel(0, "QQE Fast");
   SetIndexLabel(1, "QQE Slow");
   SetIndexLabel(2, "Cross Up");
   SetIndexLabel(3, "Cross Down");

   IndicatorShortName("QQE Signal");

   // Ligne de niveau 50 (milieu)
   IndicatorSetInteger(INDICATOR_LEVELS,        1);
   IndicatorSetDouble (INDICATOR_LEVELVALUE, 0, 50.0);
   IndicatorSetInteger(INDICATOR_LEVELCOLOR, 0, clrDimGray);
   IndicatorSetInteger(INDICATOR_LEVELSTYLE, 0, STYLE_DOT);
   IndicatorSetInteger(INDICATOR_LEVELWIDTH, 0, 1);

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double   &open[],
                const double   &high[],
                const double   &low[],
                const double   &close[],
                const long     &tick_volume[],
                const long     &volume[],
                const int      &spread[])
{
   if (rates_total < RSI_Period + ATR_Period + 5) return(0);

   int limit = rates_total - prev_calculated;
   if (prev_calculated > 0) limit++;
   if (limit > rates_total - RSI_Period - 1)
      limit = rates_total - RSI_Period - 1;

   for (int i = limit; i >= 0; i--)
   {
      // ── RSI lissé (EMA du RSI brut) ─────────────────────────────
      double rsi = iRSI(NULL, 0, RSI_Period, PRICE_CLOSE, i);

      double k = 2.0 / (SF + 1.0);
      if (i == rates_total - RSI_Period - 1)
         BufFast[i] = rsi;
      else
         BufFast[i] = BufFast[i + 1] + k * (rsi - BufFast[i + 1]);

      BufUp[i]   = EMPTY_VALUE;
      BufDown[i] = EMPTY_VALUE;

      // ── ATR du RSI lissé → bande QQE ────────────────────────────
      if (i > rates_total - RSI_Period - ATR_Period - 2)
      {
         BufSlow[i] = BufFast[i];
         continue;
      }

      double atrRsi = 0;
      for (int j = 0; j < ATR_Period; j++)
         if (i + j + 1 < rates_total)
            atrRsi += MathAbs(BufFast[i + j] - BufFast[i + j + 1]);
      atrRsi /= ATR_Period;
      double dar = ATR_Factor * atrRsi;

      // ── Trailing stop côté tendance ──────────────────────────────
      double prevSlow = (i + 1 < rates_total) ? BufSlow[i + 1] : BufFast[i];

      if (BufFast[i] > prevSlow)
         BufSlow[i] = MathMax(prevSlow, BufFast[i] - dar);
      else
         BufSlow[i] = MathMin(prevSlow, BufFast[i] + dar);

      // ── Détection de croisement ──────────────────────────────────
      if (i + 1 < rates_total)
      {
         bool crossUp   = (BufFast[i] > BufSlow[i]) && (BufFast[i+1] <= BufSlow[i+1]);
         bool crossDown = (BufFast[i] < BufSlow[i]) && (BufFast[i+1] >= BufSlow[i+1]);

         if (crossUp)   BufUp[i]   = BufSlow[i] - 2.0;
         if (crossDown) BufDown[i] = BufSlow[i] + 2.0;
      }
   }

   return(rates_total);
}
