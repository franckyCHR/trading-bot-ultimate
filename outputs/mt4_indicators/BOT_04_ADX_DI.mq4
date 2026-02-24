//+------------------------------------------------------------------+
//|  BOT_04_ADX_DI.mq4                                              |
//|  ADX + +DI / -DI avec alertes au croisement des DI              |
//|  Ligne ADX en blanc — seuil 20 en pointillé                     |
//|  +DI en bleu, -DI en rouge                                       |
//+------------------------------------------------------------------+
#property copyright   "Trading Bot Ultimate"
#property version     "1.00"
#property indicator_separate_window
#property indicator_minimum 0
#property indicator_maximum 60
#property indicator_buffers 5
#property indicator_plots   5

// ── Plot 1 : ADX ────────────────────────────────────────────────────────────
#property indicator_label1  "ADX"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrWhite
#property indicator_style1  STYLE_SOLID
#property indicator_width1  2

// ── Plot 2 : +DI ─────────────────────────────────────────────────────────────
#property indicator_label2  "+DI"
#property indicator_type2   DRAW_LINE
#property indicator_color2  clrDodgerBlue
#property indicator_style2  STYLE_SOLID
#property indicator_width2  1

// ── Plot 3 : -DI ─────────────────────────────────────────────────────────────
#property indicator_label3  "-DI"
#property indicator_type3   DRAW_LINE
#property indicator_color3  clrOrangeRed
#property indicator_style3  STYLE_SOLID
#property indicator_width3  1

// ── Plot 4 : Flèche croisement haussier (+DI > -DI) ──────────────────────────
#property indicator_label4  "DI Cross Bull"
#property indicator_type4   DRAW_ARROW
#property indicator_color4  clrLimeGreen
#property indicator_width4  2

// ── Plot 5 : Flèche croisement baissier (-DI > +DI) ──────────────────────────
#property indicator_label5  "DI Cross Bear"
#property indicator_type5   DRAW_ARROW
#property indicator_color5  clrTomato
#property indicator_width5  2

// ── Paramètres ──────────────────────────────────────────────────────────────
input int    ADX_Period    = 14;   // Période ADX
input double ADX_Threshold = 20;   // Seuil ADX (filtre momentum)
input bool   EnableAlerts  = true; // Alertes au croisement des DI

// ── Buffers ─────────────────────────────────────────────────────────────────
double BufADX[];
double BufDIp[];
double BufDIm[];
double BufCrossUp[];
double BufCrossDown[];

//+------------------------------------------------------------------+
int OnInit()
{
   SetIndexBuffer(0, BufADX,       INDICATOR_DATA);
   SetIndexBuffer(1, BufDIp,       INDICATOR_DATA);
   SetIndexBuffer(2, BufDIm,       INDICATOR_DATA);
   SetIndexBuffer(3, BufCrossUp,   INDICATOR_DATA);
   SetIndexBuffer(4, BufCrossDown, INDICATOR_DATA);

   PlotIndexSetInteger(3, PLOT_ARROW, 233); // flèche haut
   PlotIndexSetInteger(4, PLOT_ARROW, 234); // flèche bas

   ArraySetAsSeries(BufADX,       true);
   ArraySetAsSeries(BufDIp,       true);
   ArraySetAsSeries(BufDIm,       true);
   ArraySetAsSeries(BufCrossUp,   true);
   ArraySetAsSeries(BufCrossDown, true);

   // Ligne de seuil à 20 (niveau horizontal)
   string lineNom = "ADX_Level20";
   if (ObjectFind(0, lineNom) < 0)
      ObjectCreate(0, lineNom, OBJ_HLINE, ChartWindowFind(), ADX_Threshold, 0);
   ObjectSetInteger(0, lineNom, OBJPROP_COLOR,     clrYellow);
   ObjectSetInteger(0, lineNom, OBJPROP_STYLE,     STYLE_DOT);
   ObjectSetInteger(0, lineNom, OBJPROP_WIDTH,     1);
   ObjectSetString(0,  lineNom, OBJPROP_TEXT,      "ADX 20");

   IndicatorSetString(INDICATOR_SHORTNAME, StringFormat("ADX(%d) + DI", ADX_Period));
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   ObjectDelete(0, "ADX_Level20");
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
   if (rates_total < ADX_Period * 2) return(0);

   int limit = rates_total - prev_calculated;
   if (prev_calculated > 0) limit++;

   for (int i = limit - 1; i >= 0; i--)
   {
      // Utilise les fonctions MT4 intégrées pour ADX / DI
      BufADX[i] = iADX(NULL, 0, ADX_Period, PRICE_CLOSE, MODE_MAIN,   i);
      BufDIp[i] = iADX(NULL, 0, ADX_Period, PRICE_CLOSE, MODE_PLUSDI, i);
      BufDIm[i] = iADX(NULL, 0, ADX_Period, PRICE_CLOSE, MODE_MINUSDI, i);

      BufCrossUp[i]   = EMPTY_VALUE;
      BufCrossDown[i] = EMPTY_VALUE;

      if (i < rates_total - 1)
      {
         bool prevDIpDom = BufDIp[i+1] >= BufDIm[i+1];
         bool curDIpDom  = BufDIp[i]   >  BufDIm[i];

         // +DI croise au-dessus de -DI → signal haussier
         if (curDIpDom && !prevDIpDom && BufADX[i] >= ADX_Threshold)
         {
            BufCrossUp[i] = ADX_Threshold - 3;
            if (EnableAlerts && i == 0)
               Alert("BOT_04 — DI+ croise DI- vers le haut | ADX=", DoubleToString(BufADX[i],1),
                     " | ", Symbol(), " ", Period());
         }

         // -DI croise au-dessus de +DI → signal baissier
         if (!curDIpDom && prevDIpDom && BufADX[i] >= ADX_Threshold)
         {
            BufCrossDown[i] = ADX_Threshold + 3;
            if (EnableAlerts && i == 0)
               Alert("BOT_04 — DI- croise DI+ vers le haut | ADX=", DoubleToString(BufADX[i],1),
                     " | ", Symbol(), " ", Period());
         }
      }
   }

   return(rates_total);
}
