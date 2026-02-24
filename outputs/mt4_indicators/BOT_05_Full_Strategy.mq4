//+------------------------------------------------------------------+
//|  BOT_05_Full_Strategy.mq4                                        |
//|  Stratégie complète : S/R + Figure + ADX ≥ 20 + QQE croisé     |
//|  Flèche LONG ↑ verte / SHORT ↓ rouge UNIQUEMENT quand           |
//|  toutes les 4 conditions sont réunies (= 4 GATES du bot Python) |
//+------------------------------------------------------------------+
#property copyright   "Trading Bot Ultimate"
#property version     "1.00"
#property indicator_chart_window
#property indicator_buffers 4
#property indicator_color1  Lime
#property indicator_color2  Red
#property indicator_width1  3
#property indicator_width2  3

// ── Paramètres ──────────────────────────────────────────────────────────────
input int    SR_Lookback    = 20;    // Bougies pour détection pivot S/R
input double SR_Tolerance   = 0.003; // Tolérance S/R (0.3 % du prix)
input int    ADX_Period     = 14;    // Période ADX
input double ADX_Min        = 20.0;  // ADX minimum pour valider
input int    RSI_Period     = 14;    // Période RSI (base QQE)
input double QQE_SF         = 4.238; // Facteur de lissage QQE
input int    QQE_ATR_Period = 10;    // Période ATR QQE
input double QQE_ATR_Factor = 4.236; // Multiplicateur ATR QQE
input int    QQE_MaxBars    = 6;     // Max barres depuis croisement QQE
input bool   EnableAlerts   = true;  // Alertes sonores/popup
input bool   EnableNotif    = false; // Notifications push mobile

// ── Buffers visibles ──────────────────────────────────────────────────────
double BufLong[];    // Flèches LONG  ↑
double BufShort[];   // Flèches SHORT ↓
// ── Buffers de calcul (cachés) ─────────────────────────────────────────────
double BufQQEFast[];
double BufQQESlow[];

//+------------------------------------------------------------------+
int OnInit()
{
   SetIndexBuffer(0, BufLong);
   SetIndexBuffer(1, BufShort);
   SetIndexBuffer(2, BufQQEFast);   // calcul interne, non affiché
   SetIndexBuffer(3, BufQQESlow);   // calcul interne, non affiché

   SetIndexStyle(0, DRAW_ARROW, STYLE_SOLID, 3, Lime);
   SetIndexStyle(1, DRAW_ARROW, STYLE_SOLID, 3, Red);
   SetIndexStyle(2, DRAW_NONE);     // cache le buffer QQE Fast
   SetIndexStyle(3, DRAW_NONE);     // cache le buffer QQE Slow

   SetIndexArrow(0, 233);   // ↑ flèche haut (LONG)
   SetIndexArrow(1, 234);   // ↓ flèche bas  (SHORT)

   SetIndexEmptyValue(0, EMPTY_VALUE);
   SetIndexEmptyValue(1, EMPTY_VALUE);

   SetIndexLabel(0, "BOT LONG");
   SetIndexLabel(1, "BOT SHORT");

   IndicatorShortName("BOT Full Strategy");
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
   int minBars = MathMax(SR_Lookback * 2, ADX_Period * 2 + QQE_ATR_Period + 10);
   if (rates_total < minBars) return(0);

   // ── Précalcul QQE sur toutes les bougies ────────────────────────
   CalculerQQE(rates_total);

   int limit = rates_total - prev_calculated;
   if (prev_calculated > 0) limit++;
   if (limit > rates_total - SR_Lookback) limit = rates_total - SR_Lookback;

   for (int i = limit - 1; i >= 0; i--)
   {
      BufLong[i]  = EMPTY_VALUE;
      BufShort[i] = EMPTY_VALUE;

      // ── GATE 1 : Zone S/R proche du prix actuel ? ───────────────
      bool nearSR  = false;
      double srLvl = 0;
      for (int k = SR_Lookback; k < rates_total - SR_Lookback; k++)
      {
         if (EstPivotHaut(high, k, SR_Lookback, rates_total))
         {
            if (MathAbs(close[i] - high[k]) / close[i] <= SR_Tolerance)
               { nearSR = true; srLvl = high[k]; break; }
         }
         if (EstPivotBas(low, k, SR_Lookback, rates_total))
         {
            if (MathAbs(close[i] - low[k]) / close[i] <= SR_Tolerance)
               { nearSR = true; srLvl = low[k]; break; }
         }
      }
      if (!nearSR) continue;

      // ── GATE 2 : Chandelier reversal (pin bar ou doji) ──────────
      double body  = MathAbs(close[i] - open[i]);
      double range = high[i] - low[i];
      bool reversal = (range > Point * 5) && (range > 0) && (body / range < 0.40);
      if (!reversal) continue;

      // ── GATE 3 : ADX ≥ 20 + DI aligné ──────────────────────────
      double adx = iADX(NULL, 0, ADX_Period, PRICE_CLOSE, MODE_MAIN,    i);
      double dip = iADX(NULL, 0, ADX_Period, PRICE_CLOSE, MODE_PLUSDI,  i);
      double dim = iADX(NULL, 0, ADX_Period, PRICE_CLOSE, MODE_MINUSDI, i);
      if (adx < ADX_Min) continue;

      // ── GATE 4 : QQE croisé récemment (≤ QQE_MaxBars) ──────────
      int crossAgo = QQE_MaxBars + 1;
      for (int m = 0; m <= QQE_MaxBars; m++)
      {
         int idx = i + m, nxt = i + m + 1;
         if (nxt >= rates_total) break;
         bool cUp = (BufQQEFast[idx] > BufQQESlow[idx]) && (BufQQEFast[nxt] <= BufQQESlow[nxt]);
         bool cDn = (BufQQEFast[idx] < BufQQESlow[idx]) && (BufQQEFast[nxt] >= BufQQESlow[nxt]);
         if (cUp || cDn) { crossAgo = m; break; }
      }
      if (crossAgo > QQE_MaxBars) continue;

      // ── Direction : LONG ou SHORT ────────────────────────────────
      bool isLong  = (dip > dim) && (BufQQEFast[i] > BufQQESlow[i]) && (close[i] > srLvl);
      bool isShort = (dim > dip) && (BufQQEFast[i] < BufQQESlow[i]) && (close[i] < srLvl);

      if (isLong)
      {
         BufLong[i] = low[i] - 5 * Point;
         if (EnableAlerts && i == 0)
         {
            Alert("BOT LONG | ADX=", DoubleToStr(adx, 1), " QQE il y a ", crossAgo,
                  " barres | ", Symbol(), " ", GetTFName());
            if (EnableNotif)
               SendNotification(StringFormat("BOT LONG %s %s ADX=%.1f", Symbol(), GetTFName(), adx));
         }
      }
      else if (isShort)
      {
         BufShort[i] = high[i] + 5 * Point;
         if (EnableAlerts && i == 0)
         {
            Alert("BOT SHORT | ADX=", DoubleToStr(adx, 1), " QQE il y a ", crossAgo,
                  " barres | ", Symbol(), " ", GetTFName());
            if (EnableNotif)
               SendNotification(StringFormat("BOT SHORT %s %s ADX=%.1f", Symbol(), GetTFName(), adx));
         }
      }
   }
   return(rates_total);
}

//+------------------------------------------------------------------+
void CalculerQQE(int total)
{
   double k = 2.0 / (QQE_SF + 1.0);

   for (int i = total - 2; i >= 0; i--)
   {
      double rsi = iRSI(NULL, 0, RSI_Period, PRICE_CLOSE, i);

      if (i == total - 2)
         BufQQEFast[i] = rsi;
      else
         BufQQEFast[i] = BufQQEFast[i+1] + k * (rsi - BufQQEFast[i+1]);

      if (i > total - RSI_Period - QQE_ATR_Period - 2)
      {
         BufQQESlow[i] = BufQQEFast[i];
         continue;
      }

      double atr = 0;
      for (int j = 0; j < QQE_ATR_Period; j++)
         if (i+j+1 < total) atr += MathAbs(BufQQEFast[i+j] - BufQQEFast[i+j+1]);
      atr /= QQE_ATR_Period;
      double dar = QQE_ATR_Factor * atr;

      double prev = (i+1 < total) ? BufQQESlow[i+1] : BufQQEFast[i];
      BufQQESlow[i] = (BufQQEFast[i] > prev)
                      ? MathMax(prev, BufQQEFast[i] - dar)
                      : MathMin(prev, BufQQEFast[i] + dar);
   }
}

//+------------------------------------------------------------------+
bool EstPivotHaut(const double &h[], int i, int lb, int total)
{
   for (int j = 1; j <= lb; j++)
   {
      if (i-j < 0 || i+j >= total) return false;
      if (h[i-j] >= h[i] || h[i+j] >= h[i]) return false;
   }
   return true;
}

bool EstPivotBas(const double &l[], int i, int lb, int total)
{
   for (int j = 1; j <= lb; j++)
   {
      if (i-j < 0 || i+j >= total) return false;
      if (l[i-j] <= l[i] || l[i+j] <= l[i]) return false;
   }
   return true;
}

string GetTFName()
{
   switch(Period())
   {
      case 1:     return "M1";   case 5:     return "M5";
      case 15:    return "M15";  case 30:    return "M30";
      case 60:    return "H1";   case 240:   return "H4";
      case 1440:  return "D1";   case 10080: return "W1";
      case 43200: return "MN";
      default:    return IntegerToString(Period());
   }
}
