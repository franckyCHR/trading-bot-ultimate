//+------------------------------------------------------------------+
//|  BOT_02_Pattern_Detector.mq4                                     |
//|  Détecte Double Top/Bottom, ETE, Triangles                       |
//|  Dessine un rectangle coloré + label pour chaque figure          |
//+------------------------------------------------------------------+
#property copyright   "Trading Bot Ultimate"
#property version     "1.00"
#property indicator_chart_window
#property indicator_buffers 0

// ── Paramètres ──────────────────────────────────────────────────────────────
input int    PivotLookback  = 10;    // Bougies pour identifier un pivot
input double TolerancePct   = 0.003; // Tolérance pour double top/bottom (0.3 %)
input color  BullishColor   = clrLimeGreen;   // Couleur figures haussières
input color  BearishColor   = clrTomato;      // Couleur figures baissières
input color  NeutralColor   = clrGold;        // Couleur figures neutres (triangles)
input bool   ShowLabels     = true;
input int    MaxPivots      = 50;    // Max pivots à analyser

string prefix = "PAT_";

//+------------------------------------------------------------------+
int OnInit()
{
   DeleteAllObjects();
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason) { DeleteAllObjects(); }

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
   if (prev_calculated == rates_total) return(rates_total);
   DeleteAllObjects();

   // ── Collecte des pivots hauts et bas ────────────────────────────
   double pivHigh[];  int    pivHighIdx[];
   double pivLow[];   int    pivLowIdx[];
   ArrayResize(pivHigh, 0);  ArrayResize(pivHighIdx, 0);
   ArrayResize(pivLow,  0);  ArrayResize(pivLowIdx,  0);

   for (int i = PivotLookback; i < rates_total - PivotLookback; i++)
   {
      if (EstPivotHaut(high, i, PivotLookback, rates_total))
      {
         int sz = ArraySize(pivHigh);
         if (sz >= MaxPivots) break;
         ArrayResize(pivHigh,    sz + 1);
         ArrayResize(pivHighIdx, sz + 1);
         pivHigh[sz]    = high[i];
         pivHighIdx[sz] = i;
      }
      if (EstPivotBas(low, i, PivotLookback, rates_total))
      {
         int sz = ArraySize(pivLow);
         if (sz >= MaxPivots) break;
         ArrayResize(pivLow,    sz + 1);
         ArrayResize(pivLowIdx, sz + 1);
         pivLow[sz]    = low[i];
         pivLowIdx[sz] = i;
      }
   }

   int nhigh = ArraySize(pivHigh);
   int nlow  = ArraySize(pivLow);

   // ── Double Top (Bearish M) ───────────────────────────────────────
   for (int a = 0; a < nhigh - 1; a++)
   {
      for (int b = a + 1; b < nhigh; b++)
      {
         double diff = MathAbs(pivHigh[a] - pivHigh[b]) / pivHigh[a];
         if (diff <= TolerancePct)
         {
            int iA = pivHighIdx[a], iB = pivHighIdx[b];
            string nom = prefix + "DT_" + IntegerToString(iA);
            DrawRectangle(nom, time[iA], time[iB],
                          pivHigh[a] * (1 + TolerancePct),
                          pivHigh[a] * (1 - TolerancePct * 3),
                          BearishColor, "Double Top ▼");
            break;
         }
      }
   }

   // ── Double Bottom (Bullish W) ────────────────────────────────────
   for (int a = 0; a < nlow - 1; a++)
   {
      for (int b = a + 1; b < nlow; b++)
      {
         double diff = MathAbs(pivLow[a] - pivLow[b]) / pivLow[a];
         if (diff <= TolerancePct)
         {
            int iA = pivLowIdx[a], iB = pivLowIdx[b];
            string nom = prefix + "DB_" + IntegerToString(iA);
            DrawRectangle(nom, time[iA], time[iB],
                          pivLow[a] * (1 + TolerancePct * 3),
                          pivLow[a] * (1 - TolerancePct),
                          BullishColor, "Double Bottom ▲");
            break;
         }
      }
   }

   // ── Épaule-Tête-Épaule Baissier (3 pivots hauts) ────────────────
   if (nhigh >= 3)
   {
      for (int a = 0; a < nhigh - 2; a++)
      {
         int iL = pivHighIdx[a];
         int iM = pivHighIdx[a + 1];
         int iR = pivHighIdx[a + 2];

         // Tête (milieu) doit être plus haute que les épaules
         if (pivHigh[a+1] > pivHigh[a] && pivHigh[a+1] > pivHigh[a+2])
         {
            // Épaules à peu près à la même hauteur (±3 %)
            double diff = MathAbs(pivHigh[a] - pivHigh[a+2]) / pivHigh[a];
            if (diff <= 0.03)
            {
               string nom = prefix + "ETE_" + IntegerToString(iL);
               DrawRectangle(nom, time[iL], time[iR],
                             pivHigh[a+1] * 1.002,
                             MathMin(pivHigh[a], pivHigh[a+2]) * 0.998,
                             BearishColor, "ETE Bearish ▼");
            }
         }
         // ETE Inversé (3 pivots bas)
      }
   }

   // ── ETE Inversé Haussier (3 pivots bas) ─────────────────────────
   if (nlow >= 3)
   {
      for (int a = 0; a < nlow - 2; a++)
      {
         if (pivLow[a+1] < pivLow[a] && pivLow[a+1] < pivLow[a+2])
         {
            double diff = MathAbs(pivLow[a] - pivLow[a+2]) / pivLow[a];
            if (diff <= 0.03)
            {
               int iL = pivLowIdx[a];
               int iR = pivLowIdx[a + 2];
               string nom = prefix + "ETEinv_" + IntegerToString(iL);
               DrawRectangle(nom, time[iL], time[iR],
                             MathMax(pivLow[a], pivLow[a+2]) * 1.002,
                             pivLow[a+1] * 0.998,
                             BullishColor, "ETE Inv. ▲");
            }
         }
      }
   }

   // ── Triangle Symétrique (hauts descendants + bas ascendants) ─────
   if (nhigh >= 2 && nlow >= 2)
   {
      double highSlope = (pivHigh[nhigh-1] - pivHigh[0]) / (nhigh - 1);
      double lowSlope  = (pivLow[nlow-1]   - pivLow[0])  / (nlow  - 1);

      if (highSlope < -Point && lowSlope > Point)
      {
         int iStart = MathMin(pivHighIdx[0], pivLowIdx[0]);
         int iEnd   = MathMax(pivHighIdx[nhigh-1], pivLowIdx[nlow-1]);
         string nom = prefix + "TRI_SYM";
         DrawRectangle(nom, time[iStart], time[iEnd],
                       pivHigh[0], pivLow[0],
                       NeutralColor, "Triangle Sym.");
      }
   }

   return(rates_total);
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

//+------------------------------------------------------------------+
void DrawRectangle(string nom, datetime t1, datetime t2,
                   double p1, double p2, color col, string label)
{
   if (ObjectFind(0, nom) < 0)
      ObjectCreate(0, nom, OBJ_RECTANGLE, 0, t1, p1, t2, p2);

   ObjectSetInteger(0, nom, OBJPROP_COLOR,  col);
   ObjectSetInteger(0, nom, OBJPROP_BACK,   true);
   ObjectSetInteger(0, nom, OBJPROP_FILL,   true);
   ObjectSetInteger(0, nom, OBJPROP_WIDTH,  1);
   ObjectSetDouble(0,  nom, OBJPROP_PRICE1, p1);
   ObjectSetDouble(0,  nom, OBJPROP_PRICE2, p2);
   ObjectSetInteger(0, nom, OBJPROP_TIME1,  t1);
   ObjectSetInteger(0, nom, OBJPROP_TIME2,  t2);

   if (ShowLabels)
   {
      string lblNom = nom + "_lbl";
      if (ObjectFind(0, lblNom) < 0)
         ObjectCreate(0, lblNom, OBJ_TEXT, 0, t1, p1);
      ObjectSetString(0,  lblNom, OBJPROP_TEXT,     label);
      ObjectSetInteger(0, lblNom, OBJPROP_COLOR,    col);
      ObjectSetInteger(0, lblNom, OBJPROP_FONTSIZE, 9);
      ObjectSetInteger(0, lblNom, OBJPROP_BOLD,     true);
   }
}

void DeleteAllObjects()
{
   for (int i = ObjectsTotal(0) - 1; i >= 0; i--)
   {
      string nom = ObjectName(0, i);
      if (StringFind(nom, prefix) == 0)
         ObjectDelete(0, nom);
   }
}
