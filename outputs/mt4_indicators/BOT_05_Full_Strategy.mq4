//+------------------------------------------------------------------+
//|  BOT_05_Full_Strategy.mq4                                        |
//|  Stratégie complète : S/R + QQE croisé + ADX ≥ 20               |
//|  Affiche une flèche UNIQUEMENT quand toutes les conditions        |
//|  sont réunies (≡ les 4 gates du bot Python)                      |
//+------------------------------------------------------------------+
#property copyright   "Trading Bot Ultimate"
#property version     "1.00"
#property indicator_chart_window
#property indicator_buffers 4
#property indicator_plots   2

// ── Plot 1 : Flèche LONG (achat) ─────────────────────────────────────────────
#property indicator_label1  "LONG Signal"
#property indicator_type1   DRAW_ARROW
#property indicator_color1  clrLimeGreen
#property indicator_width1  3

// ── Plot 2 : Flèche SHORT (vente) ────────────────────────────────────────────
#property indicator_label2  "SHORT Signal"
#property indicator_type2   DRAW_ARROW
#property indicator_color2  clrTomato
#property indicator_width2  3

// ── Paramètres ──────────────────────────────────────────────────────────────
input int    SR_Lookback    = 20;    // Bougies pour pivot S/R
input double SR_Tolerance   = 0.003; // Tolérance S/R en % (0.3 %)
input int    ADX_Period     = 14;    // Période ADX
input double ADX_Min        = 20.0;  // ADX minimum pour valider
input int    RSI_Period     = 14;    // Période RSI (base QQE)
input double QQE_SF         = 4.238; // Facteur de lissage QQE
input int    QQE_ATR_Period = 10;    // Période ATR QQE
input double QQE_ATR_Factor = 4.236; // Multiplicateur ATR QQE
input int    QQE_MaxBars    = 6;     // Max barres depuis le croisement QQE
input bool   EnableAlerts   = true;  // Alertes sonores
input bool   EnableNotif    = false; // Notifications push

// ── Buffers ─────────────────────────────────────────────────────────────────
double BufLong[];     // Flèches achat
double BufShort[];    // Flèches vente
double BufQQEFast[];  // Ligne rapide QQE (interne)
double BufQQESlow[];  // Ligne lente  QQE (interne)

//+------------------------------------------------------------------+
int OnInit()
{
   SetIndexBuffer(0, BufLong,    INDICATOR_DATA);
   SetIndexBuffer(1, BufShort,   INDICATOR_DATA);
   SetIndexBuffer(2, BufQQEFast, INDICATOR_CALCULATIONS);
   SetIndexBuffer(3, BufQQESlow, INDICATOR_CALCULATIONS);

   PlotIndexSetInteger(0, PLOT_ARROW, 233); // ↑
   PlotIndexSetInteger(1, PLOT_ARROW, 234); // ↓

   ArraySetAsSeries(BufLong,    true);
   ArraySetAsSeries(BufShort,   true);
   ArraySetAsSeries(BufQQEFast, true);
   ArraySetAsSeries(BufQQESlow, true);

   IndicatorSetString(INDICATOR_SHORTNAME, "BOT Full Strategy");
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
   if (rates_total < MathMax(SR_Lookback * 2, ADX_Period * 2 + QQE_ATR_Period + 5))
      return(0);

   ArraySetAsSeries(close, true);
   ArraySetAsSeries(high,  true);
   ArraySetAsSeries(low,   true);
   ArraySetAsSeries(time,  true);

   int limit = rates_total - prev_calculated;
   if (prev_calculated > 0) limit++;
   if (limit > rates_total - SR_Lookback) limit = rates_total - SR_Lookback;

   // ── Précalcul QQE ────────────────────────────────────────────────
   CalculerQQE(close, rates_total);

   for (int i = limit - 1; i >= 0; i--)
   {
      BufLong[i]  = EMPTY_VALUE;
      BufShort[i] = EMPTY_VALUE;

      // ── GATE 1 : Zone S/R proche ? ──────────────────────────────
      bool nearSR = false;
      double srLevel = 0;
      for (int k = SR_Lookback; k < rates_total - SR_Lookback; k++)
      {
         if (EstPivotHaut(high, k, SR_Lookback, rates_total))
         {
            double diff = MathAbs(close[i] - high[k]) / close[i];
            if (diff <= SR_Tolerance) { nearSR = true; srLevel = high[k]; break; }
         }
         if (EstPivotBas(low, k, SR_Lookback, rates_total))
         {
            double diff = MathAbs(close[i] - low[k]) / close[i];
            if (diff <= SR_Tolerance) { nearSR = true; srLevel = low[k]; break; }
         }
      }
      if (!nearSR) continue;

      // ── GATE 2 : Figure / Reversal candle — simplifié ───────────
      // Détection pin bar : mèche 2× le corps
      double body  = MathAbs(close[i] - open[i]);
      double range = high[i] - low[i];
      bool pinBar  = (range > 0) && (body / range < 0.35); // corps < 35 % du range
      if (!pinBar && range == 0) continue;  // bougie doji acceptable aussi

      // ── GATE 3 : ADX ≥ 20 + DI aligné ──────────────────────────
      double adx   = iADX(NULL, 0, ADX_Period, PRICE_CLOSE, MODE_MAIN,    i);
      double dip   = iADX(NULL, 0, ADX_Period, PRICE_CLOSE, MODE_PLUSDI,  i);
      double dim   = iADX(NULL, 0, ADX_Period, PRICE_CLOSE, MODE_MINUSDI, i);
      if (adx < ADX_Min) continue;

      // ── GATE 4 : QQE croisé récemment (≤ QQE_MaxBars) ──────────
      int crossAgo = QQE_MaxBars + 1;  // par défaut : trop vieux
      for (int m = 0; m <= QQE_MaxBars && (i + m) < rates_total - 1; m++)
      {
         int idx  = i + m;
         int idxN = i + m + 1;
         bool crossU = (BufQQEFast[idx] > BufQQESlow[idx]) &&
                       (BufQQEFast[idxN] <= BufQQESlow[idxN]);
         bool crossD = (BufQQEFast[idx] < BufQQESlow[idx]) &&
                       (BufQQEFast[idxN] >= BufQQESlow[idxN]);
         if (crossU || crossD) { crossAgo = m; break; }
      }
      if (crossAgo > QQE_MaxBars) continue;

      // ── Détermination direction ──────────────────────────────────
      bool isLong  = (dip > dim) && (BufQQEFast[i] > BufQQESlow[i]) &&
                     (close[i] > srLevel);
      bool isShort = (dim > dip) && (BufQQEFast[i] < BufQQESlow[i]) &&
                     (close[i] < srLevel);

      if (isLong)
      {
         BufLong[i] = low[i] - 3 * Point;
         if (EnableAlerts && i == 0)
         {
            Alert("BOT Full — LONG | ADX=", DoubleToString(adx,1),
                  " | QQE il y a ", crossAgo, " barres | ", Symbol(), " ", Period());
            if (EnableNotif) SendNotification(StringFormat("BOT LONG %s %d", Symbol(), Period()));
         }
      }
      else if (isShort)
      {
         BufShort[i] = high[i] + 3 * Point;
         if (EnableAlerts && i == 0)
         {
            Alert("BOT Full — SHORT | ADX=", DoubleToString(adx,1),
                  " | QQE il y a ", crossAgo, " barres | ", Symbol(), " ", Period());
            if (EnableNotif) SendNotification(StringFormat("BOT SHORT %s %d", Symbol(), Period()));
         }
      }
   }

   return(rates_total);
}

//+------------------------------------------------------------------+
//| Précalcule les buffers QQE Fast/Slow                             |
//+------------------------------------------------------------------+
void CalculerQQE(const double &close[], int total)
{
   ArraySetAsSeries(close, true);

   for (int i = total - 2; i >= 0; i--)
   {
      double rsi = iRSI(NULL, 0, RSI_Period, PRICE_CLOSE, i);
      double k   = 2.0 / (QQE_SF + 1.0);

      if (i == total - 2)
         BufQQEFast[i] = rsi;
      else
         BufQQEFast[i] = BufQQEFast[i+1] + k * (rsi - BufQQEFast[i+1]);

      if (i > total - QQE_ATR_Period - 2)
      {
         BufQQESlow[i] = BufQQEFast[i];
         continue;
      }

      double atr = 0;
      for (int j = 0; j < QQE_ATR_Period; j++)
      {
         if (i + j + 1 < total)
            atr += MathAbs(BufQQEFast[i+j] - BufQQEFast[i+j+1]);
      }
      atr /= QQE_ATR_Period;
      double dar = QQE_ATR_Factor * atr;

      double prevSlow = (i + 1 < total) ? BufQQESlow[i+1] : BufQQEFast[i];
      if (BufQQEFast[i] > prevSlow)
         BufQQESlow[i] = MathMax(prevSlow, BufQQEFast[i] - dar);
      else
         BufQQESlow[i] = MathMin(prevSlow, BufQQEFast[i] + dar);
   }
}

//+------------------------------------------------------------------+
bool EstPivotHaut(const double &high[], int i, int lb, int total)
{
   for (int j = 1; j <= lb; j++)
   {
      if (i - j < 0 || i + j >= total) return false;
      if (high[i-j] >= high[i] || high[i+j] >= high[i]) return false;
   }
   return true;
}

bool EstPivotBas(const double &low[], int i, int lb, int total)
{
   for (int j = 1; j <= lb; j++)
   {
      if (i - j < 0 || i + j >= total) return false;
      if (low[i-j] <= low[i] || low[i+j] <= low[i]) return false;
   }
   return true;
}
