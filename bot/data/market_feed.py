"""
market_feed.py
==============
Récupération des données OHLCV pour le FOREX via yfinance.
Supporte aussi la crypto via CCXT en mode secondaire.

Paires forex supportées : EUR/USD, GBP/USD, USD/JPY, USD/CHF,
                          AUD/USD, NZD/USD, USD/CAD, EUR/GBP,
                          EUR/JPY, GBP/JPY, etc.
"""

import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# ── Correspondance paires forex → symboles yfinance ──────────────────────────
# Format : "EUR/USD" → "EURUSD=X"
# yfinance utilise le suffixe "=X" pour les paires de change spot.

# Mapping spécial pour les matières premières et indices
_SPECIAL_SYMBOLS = {
    # Or
    "XAU/USD": "GC=F",    # Gold Futures
    "GOLD":    "GC=F",
    "OR":      "GC=F",
    # Indices américains
    "DJ30":    "YM=F",    # Dow Jones Futures (Mini)
    "US30":    "YM=F",
    "DOW":     "YM=F",
    "SP500":   "ES=F",    # S&P 500 Futures
    "US500":   "ES=F",
    "NAS100":  "NQ=F",    # Nasdaq 100 Futures
    "US100":   "NQ=F",
    # Indices européens
    "DAX":     "^GDAXI",  # DAX Allemand
    "GER40":   "^GDAXI",
    "CAC40":   "^FCHI",   # CAC 40 Français
    "UK100":   "^FTSE",   # FTSE 100 Britannique
    # Pétrole
    "WTI":     "CL=F",    # Crude Oil Futures
    "BRENT":   "BZ=F",    # Brent Oil Futures
    # Argent
    "XAG/USD": "SI=F",    # Silver Futures
}

# ── Correspondance timeframes scanner → yfinance ─────────────────────────────
TF_YF = {
    "1m":  "1m",
    "5m":  "5m",
    "15m": "15m",
    "30m": "30m",
    "1h":  "1h",
    "4h":  "1h",    # yfinance n'a pas de 4h → on télécharge 1h et on rééchantillonne
    "1d":  "1d",
    "1w":  "1wk",
}

# Nombre de jours à demander selon le timeframe pour obtenir ~limit bougies
# (×3 pour compenser weekends + jours fériés forex)
TF_DAYS = {
    "1m":  2,
    "5m":  5,
    "15m": 10,
    "30m": 20,
    "1h":  60,
    "4h":  120,    # on télécharge 1h puis on rééchantillonne en 4h
    "1d":  500,
    "1w":  600,
}


def _pair_to_yf(pair: str) -> str:
    """
    Convertit un instrument en symbole yfinance.

    Exemples :
        "EUR/USD"  → "EURUSD=X"
        "XAU/USD"  → "GC=F"
        "DJ30"     → "YM=F"
        "DAX"      → "^GDAXI"
        "GC=F"     → "GC=F"   (déjà formaté)
    """
    # Déjà un symbole yfinance natif
    if pair in ("=X", "=F") or pair.endswith("=X") or pair.endswith("=F") or pair.startswith("^"):
        return pair

    # Vérifier le mapping spécial (matières premières, indices)
    key = pair.upper()
    if key in _SPECIAL_SYMBOLS:
        return _SPECIAL_SYMBOLS[key]

    # Paire forex standard : "EUR/USD" → "EURUSD=X"
    return pair.replace("/", "") + "=X"


class MarketFeed:
    """
    Source de données de marché principale.

    Mode FOREX (défaut) : utilise yfinance, aucune clé API requise.
    Mode CRYPTO         : utilise CCXT (Binance, Bybit, etc.).

    Utilisation :
        feed = MarketFeed()                     # forex
        feed = MarketFeed("binance")            # crypto Binance
        df   = feed.get_ohlcv("EUR/USD", "1h", limit=300)
    """

    def __init__(self, exchange_id: str = "forex"):
        """
        Args:
            exchange_id : "forex" pour le forex via yfinance,
                          ou un exchange ccxt (ex: "binance") pour la crypto.
        """
        self.exchange_id = exchange_id
        self._ccxt_exchange = None   # Initialisation paresseuse pour CCXT

        if exchange_id == "forex":
            logger.info("MarketFeed initialisé en mode FOREX (yfinance)")
        else:
            self._init_ccxt(exchange_id)

    def _init_ccxt(self, exchange_id: str) -> None:
        """Initialise l'exchange CCXT (crypto uniquement)."""
        try:
            import ccxt
            if exchange_id not in ccxt.exchanges:
                raise ValueError(f"Exchange '{exchange_id}' inconnu dans ccxt.")
            exchange_class = getattr(ccxt, exchange_id)
            self._ccxt_exchange = exchange_class({"enableRateLimit": True})
            logger.info("MarketFeed initialisé sur l'exchange CCXT : %s", exchange_id)
        except ImportError:
            logger.error("ccxt non installé — impossible d'utiliser le mode crypto.")

    # ------------------------------------------------------------------
    # Méthode principale : récupération OHLCV
    # ------------------------------------------------------------------

    def get_ohlcv(
        self, pair: str, timeframe: str, limit: int = 300
    ) -> pd.DataFrame | None:
        """
        Récupère les bougies OHLCV pour une paire et un timeframe.

        Args:
            pair      : Paire forex (ex: "EUR/USD") ou crypto (ex: "BTC/USDT").
            timeframe : Timeframe ("30m", "1h", "4h", "1d", etc.).
            limit     : Nombre de bougies souhaitées (défaut: 300).

        Returns:
            DataFrame avec colonnes [timestamp, open, high, low, close, volume]
            ou None en cas d'erreur.
        """
        if self.exchange_id == "forex":
            return self._get_ohlcv_forex(pair, timeframe, limit)
        else:
            return self._get_ohlcv_ccxt(pair, timeframe, limit)

    # ------------------------------------------------------------------
    # FOREX via yfinance
    # ------------------------------------------------------------------

    def _get_ohlcv_forex(
        self, pair: str, timeframe: str, limit: int
    ) -> pd.DataFrame | None:
        """Récupère les données forex depuis Yahoo Finance."""
        symbol = _pair_to_yf(pair)
        yf_interval = TF_YF.get(timeframe, "1h")
        days = TF_DAYS.get(timeframe, 60)

        # Augmenter la période si limit est grand
        days_needed = max(days, int(limit * days / 300) + 10)

        logger.debug(
            "yfinance — %s / %s (interval=%s, days=%d)",
            symbol, timeframe, yf_interval, days_needed,
        )

        try:
            # Téléchargement des données
            df_raw = yf.download(
                symbol,
                period=f"{days_needed}d",
                interval=yf_interval,
                progress=False,
                auto_adjust=True,
            )

            if df_raw is None or df_raw.empty:
                logger.warning("Aucune donnée yfinance pour %s / %s", pair, timeframe)
                return None

            # Normaliser les colonnes (yfinance peut retourner MultiIndex)
            if isinstance(df_raw.columns, pd.MultiIndex):
                df_raw.columns = df_raw.columns.get_level_values(0)

            df_raw.columns = [c.lower() for c in df_raw.columns]

            # Rééchantillonnage 1h → 4h si nécessaire
            if timeframe == "4h":
                df_raw = self._resample_4h(df_raw)

            # Construire le DataFrame standardisé
            df = pd.DataFrame()
            df["timestamp"] = df_raw.index
            df["open"]      = df_raw["open"].astype(float).values
            df["high"]      = df_raw["high"].astype(float).values
            df["low"]       = df_raw["low"].astype(float).values
            df["close"]     = df_raw["close"].astype(float).values
            df["volume"]    = df_raw.get("volume", pd.Series([0] * len(df_raw))).astype(float).values

            # Supprimer les lignes avec des NaN (jours fériés, weekends)
            df.dropna(subset=["open", "high", "low", "close"], inplace=True)
            df.reset_index(drop=True, inplace=True)

            # Garder seulement les dernières `limit` bougies
            if len(df) > limit:
                df = df.iloc[-limit:].reset_index(drop=True)

            logger.info(
                "OHLCV récupéré avec succès — %s / %s : %d bougies | Prix actuel: %.5f",
                pair, timeframe, len(df),
                df["close"].iloc[-1] if len(df) > 0 else 0,
            )
            return df

        except Exception as exc:
            logger.exception(
                "Erreur lors de la récupération forex %s / %s : %s",
                pair, timeframe, exc,
            )
            return None

    def _resample_4h(self, df_1h: pd.DataFrame) -> pd.DataFrame:
        """Rééchantillonne un DataFrame 1h en 4h."""
        try:
            df_1h.index = pd.to_datetime(df_1h.index)
            df_4h = df_1h.resample("4h").agg({
                "open":   "first",
                "high":   "max",
                "low":    "min",
                "close":  "last",
                "volume": "sum",
            }).dropna()
            return df_4h
        except Exception as exc:
            logger.warning("Erreur rééchantillonnage 4h : %s", exc)
            return df_1h

    # ------------------------------------------------------------------
    # CRYPTO via CCXT (inchangé)
    # ------------------------------------------------------------------

    def _get_ohlcv_ccxt(
        self, pair: str, timeframe: str, limit: int
    ) -> pd.DataFrame | None:
        """Récupère les données crypto depuis un exchange CCXT."""
        if not self._ccxt_exchange:
            logger.error("Exchange CCXT non initialisé.")
            return None
        try:
            import ccxt
            raw_data = self._ccxt_exchange.fetch_ohlcv(pair, timeframe, limit=limit)
            if not raw_data:
                return None
            df = pd.DataFrame(
                raw_data,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)
            df.sort_values("timestamp", inplace=True)
            df.reset_index(drop=True, inplace=True)
            logger.info(
                "OHLCV CCXT récupéré — %s / %s : %d bougies",
                pair, timeframe, len(df),
            )
            return df
        except Exception as exc:
            logger.exception("Erreur CCXT %s / %s : %s", pair, timeframe, exc)
            return None

    # ------------------------------------------------------------------
    # Prix actuel
    # ------------------------------------------------------------------

    def get_current_price(self, pair: str) -> float:
        """
        Retourne le dernier prix coté pour une paire.
        """
        if self.exchange_id == "forex":
            try:
                symbol = _pair_to_yf(pair)
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d", interval="1m")
                if hist is not None and not hist.empty:
                    return float(hist["Close"].iloc[-1])
                return 0.0
            except Exception as exc:
                logger.error("Erreur prix actuel %s : %s", pair, exc)
                return 0.0
        else:
            if not self._ccxt_exchange:
                return 0.0
            try:
                import ccxt
                ticker = self._ccxt_exchange.fetch_ticker(pair)
                return float(ticker.get("last") or 0.0)
            except Exception:
                return 0.0
