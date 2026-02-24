//+------------------------------------------------------------------+
//|  BOT_04_ADX_DI.mq4                                              |
//|  ADX + +DI / -DI avec alertes au croisement                     |
//|  Sous-fenêtre : ADX blanc | +DI bleu | -DI rouge                |
//|  Seuil ADX 20 en pointillé jaune                                |
//+------------------------------------------------------------------+
#property copyright   "Trading Bot Ultimate"
#property version     "1.00"
#property indicator_separate_window
#property indicator_minimum 0
#property indicator_maximum 60
#property indicator_buffers 5
#property indicator_color1  White
#property indicator_color2  DodgerBlue
#property indicator_color3  Red
#property indicator_color4  Lime
#property indicator_color5  Red
#property indicator_width1  2
#property indicator_width2  1
#property indicator_width3  1
#property indicator_width4  2
#property indicator_width5  2

// ── Paramètres ──────────────────────────────────────────────────────────────
input int    ADX_Period     = 14;    // Période ADX
input double ADX_Threshold  = 20.0;  // Seuil ADX minimum
input bool   EnableAlerts   = true;  // Alertes au croisement des DI

// ── Buffers ─────────────────────────────────────────────────────────────────
double BufADX[];
double BufDIp[];
double BufDIm[];
double BufCrossUp[];
double BufCrossDown[];

//+------------------------------------------------------------------+
int OnInit()
{
   SetIndexBuffer(0, BufADX);
   SetIndexBuffer(1, BufDIp);
   SetIndexBuffer(2, BufDIm);
   SetIndexBuffer(3, BufCrossUp);
   SetIndexBuffer(4, BufCrossDown);

   SetIndexStyle(0, DRAW_LINE,  STYLE_SOLID, 2, White);
   SetIndexStyle(1, DRAW_LINE,  STYLE_SOLID, 1, DodgerBlue);
   SetIndexStyle(2, DRAW_LINE,  STYLE_SOLID, 1, Red);
   SetIndexStyle(3, DRAW_ARROW, STYLE_SOLID, 2, Lime);
   SetIndexStyle(4, DRAW_ARROW, STYLE_SOLID, 2, Red);

   SetIndexArrow(3, 233);  // flèche haut ↑
   SetIndexArrow(4, 234);  // flèche bas  ↓

   SetIndexEmptyValue(3, EMPTY_VALUE);
   SetIndexEmptyValue(4, EMPTY_VALUE);

   SetIndexLabel(0, "ADX");
   SetIndexLabel(1, "+DI");
   SetIndexLabel(2, "-DI");
   SetIndexLabel(3, "DI+ Cross");
   SetIndexLabel(4, "DI- Cross");

   IndicatorShortName(StringFormat("ADX(%d) + DI", ADX_Period));

   // ── Seuil ADX 20 en pointillé (dans la sous-fenêtre) ────────────
   IndicatorSetInteger(INDICATOR_LEVELS,        1);
   IndicatorSetDouble (INDICATOR_LEVELVALUE, 0, ADX_Threshold);
   IndicatorSetInteger(INDICATOR_LEVELCOLOR, 0, clrYellow);
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
   if (rates_total < ADX_Period * 2) return(0);

   int limit = rates_total - prev_calculated;
   if (prev_calculated > 0) limit++;

   for (int i = limit - 1; i >= 0; i--)
   {
      BufADX[i] = iADX(NULL, 0, ADX_Period, PRICE_CLOSE, MODE_MAIN,    i);
      BufDIp[i] = iADX(NULL, 0, ADX_Period, PRICE_CLOSE, MODE_PLUSDI,  i);
      BufDIm[i] = iADX(NULL, 0, ADX_Period, PRICE_CLOSE, MODE_MINUSDI, i);

      BufCrossUp[i]   = EMPTY_VALUE;
      BufCrossDown[i] = EMPTY_VALUE;

      if (i + 1 < rates_total)
      {
         bool prevBull = (BufDIp[i+1] >= BufDIm[i+1]);
         bool curBull  = (BufDIp[i]   >  BufDIm[i]);

         // +DI passe au-dessus de -DI → haussier
         if (curBull && !prevBull && BufADX[i] >= ADX_Threshold)
         {
            BufCrossUp[i] = ADX_Threshold - 3;
            if (EnableAlerts && i == 0)
               Alert("BOT_04 — DI+ > DI-  | ADX=", DoubleToStr(BufADX[i], 1),
                     " | ", Symbol(), " ", GetTFName());
         }

         // -DI passe au-dessus de +DI → baissier
         if (!curBull && prevBull && BufADX[i] >= ADX_Threshold)
         {
            BufCrossDown[i] = ADX_Threshold + 3;
            if (EnableAlerts && i == 0)
               Alert("BOT_04 — DI- > DI+  | ADX=", DoubleToStr(BufADX[i], 1),
                     " | ", Symbol(), " ", GetTFName());
         }
      }
   }

   return(rates_total);
}

//+------------------------------------------------------------------+
string GetTFName()
{
   switch(Period())
   {
      case 1:     return "M1";
      case 5:     return "M5";
      case 15:    return "M15";
      case 30:    return "M30";
      case 60:    return "H1";
      case 240:   return "H4";
      case 1440:  return "D1";
      case 10080: return "W1";
      case 43200: return "MN";
      default:    return IntegerToString(Period());
   }
}
