//+------------------------------------------------------------------+
//|  BOT_01_SR_Zones.mq4                                             |
//|  Détecte et dessine les zones de Support & Résistance            |
//|  Méthode : pivots locaux sur N bougies + force par nombre touches|
//+------------------------------------------------------------------+
#property copyright   "Trading Bot Ultimate"
#property version     "1.00"
#property indicator_chart_window
#property indicator_buffers 0

// ── Paramètres ──────────────────────────────────────────────────────────────
input int    LookbackBars   = 20;    // Nombre de bougies pour pivot local
input int    ZoneWidthPips  = 10;    // Épaisseur de la zone en pips
input int    MinTouches     = 2;     // Touches minimales pour valider la zone
input color  SupportColor   = clrDodgerBlue;   // Couleur des supports
input color  ResistColor    = clrOrangeRed;    // Couleur des résistances
input int    MaxZones       = 10;    // Nombre max de zones à tracer
input bool   ShowLabels     = true;  // Afficher les labels

// ── Variables globales ───────────────────────────────────────────────────────
string prefix = "SR_";

//+------------------------------------------------------------------+
//| Initialisation                                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   DeleteAllObjects();
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Déinitialisation — nettoie tous les objets                        |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   DeleteAllObjects();
}

//+------------------------------------------------------------------+
//| Calcul principal                                                  |
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
   // Recalcule uniquement si de nouvelles bougies sont disponibles
   if (prev_calculated == rates_total) return(rates_total);

   DeleteAllObjects();

   double pip = Point;
   if (Digits == 5 || Digits == 3) pip = Point * 10;
   double zoneWidth = ZoneWidthPips * pip;

   int zonesFound = 0;

   // ── Recherche des pivots hauts (résistances) ────────────────────
   for (int i = LookbackBars; i < rates_total - LookbackBars && zonesFound < MaxZones; i++)
   {
      if (EstPivotHaut(high, i, LookbackBars, rates_total))
      {
         double niveau = high[i];
         int touches = CompterTouches(niveau, zoneWidth, high, low, rates_total);
         if (touches >= MinTouches)
         {
            string nom = prefix + "R_" + IntegerToString(i);
            double debut = (double)time[MathMax(0, i - LookbackBars)];
            DrawZone(nom, time[i], TimeCurrent(), niveau, niveau + zoneWidth,
                     ResistColor, touches);
            zonesFound++;
         }
      }
   }

   // ── Recherche des pivots bas (supports) ─────────────────────────
   for (int i = LookbackBars; i < rates_total - LookbackBars && zonesFound < MaxZones * 2; i++)
   {
      if (EstPivotBas(low, i, LookbackBars, rates_total))
      {
         double niveau = low[i];
         int touches = CompterTouches(niveau, zoneWidth, high, low, rates_total);
         if (touches >= MinTouches)
         {
            string nom = prefix + "S_" + IntegerToString(i);
            DrawZone(nom, time[i], TimeCurrent(), niveau - zoneWidth, niveau,
                     SupportColor, touches);
            zonesFound++;
         }
      }
   }

   return(rates_total);
}

//+------------------------------------------------------------------+
//| Vérifie si la bougie i est un pivot haut                         |
//+------------------------------------------------------------------+
bool EstPivotHaut(const double &high[], int i, int lookback, int total)
{
   for (int j = 1; j <= lookback; j++)
   {
      if (i - j < 0 || i + j >= total) return false;
      if (high[i - j] >= high[i] || high[i + j] >= high[i]) return false;
   }
   return true;
}

//+------------------------------------------------------------------+
//| Vérifie si la bougie i est un pivot bas                          |
//+------------------------------------------------------------------+
bool EstPivotBas(const double &low[], int i, int lookback, int total)
{
   for (int j = 1; j <= lookback; j++)
   {
      if (i - j < 0 || i + j >= total) return false;
      if (low[i - j] <= low[i] || low[i + j] <= low[i]) return false;
   }
   return true;
}

//+------------------------------------------------------------------+
//| Compte combien de bougies touchent la zone niveau ± width        |
//+------------------------------------------------------------------+
int CompterTouches(double niveau, double width,
                   const double &high[], const double &low[], int total)
{
   int count = 0;
   for (int k = 0; k < total; k++)
   {
      if ((high[k] >= niveau - width && high[k] <= niveau + width) ||
          (low[k]  >= niveau - width && low[k]  <= niveau + width))
         count++;
   }
   return count;
}

//+------------------------------------------------------------------+
//| Dessine un rectangle de zone S/R                                 |
//+------------------------------------------------------------------+
void DrawZone(string nom, datetime t1, datetime t2,
              double price1, double price2, color col, int touches)
{
   if (ObjectFind(0, nom) < 0)
      ObjectCreate(0, nom, OBJ_RECTANGLE, 0, t1, price1, t2, price2);

   ObjectSetInteger(0, nom, OBJPROP_COLOR,   col);
   ObjectSetInteger(0, nom, OBJPROP_BACK,    true);
   ObjectSetInteger(0, nom, OBJPROP_FILL,    true);
   ObjectSetInteger(0, nom, OBJPROP_WIDTH,   1);
   ObjectSetDouble(0,  nom, OBJPROP_PRICE1,  price1);
   ObjectSetDouble(0,  nom, OBJPROP_PRICE2,  price2);
   ObjectSetInteger(0, nom, OBJPROP_TIME1,   t1);
   ObjectSetInteger(0, nom, OBJPROP_TIME2,   t2);

   // Transparence simulée via RGBA (couleur de fond à 30 % d'opacité)
   color fillColor = (color)((col & 0x00FFFFFF) | 0x33000000);
   ObjectSetInteger(0, nom, OBJPROP_BGCOLOR, fillColor);

   if (ShowLabels)
   {
      string lblNom = nom + "_lbl";
      string txt = (StringFind(nom, "_R_") >= 0 ? "R" : "S") +
                   " [" + IntegerToString(touches) + "T]";
      if (ObjectFind(0, lblNom) < 0)
         ObjectCreate(0, lblNom, OBJ_TEXT, 0, t2, price2);
      ObjectSetString(0,  lblNom, OBJPROP_TEXT,  txt);
      ObjectSetInteger(0, lblNom, OBJPROP_COLOR, col);
      ObjectSetInteger(0, lblNom, OBJPROP_FONTSIZE, 8);
   }
}

//+------------------------------------------------------------------+
//| Supprime tous les objets créés par cet indicateur                |
//+------------------------------------------------------------------+
void DeleteAllObjects()
{
   for (int i = ObjectsTotal(0) - 1; i >= 0; i--)
   {
      string nom = ObjectName(0, i);
      if (StringFind(nom, prefix) == 0)
         ObjectDelete(0, nom);
   }
}
