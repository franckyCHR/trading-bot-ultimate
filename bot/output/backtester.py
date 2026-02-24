"""
backtester.py
─────────────
Valide les signaux du bot sur données historiques.
Répond à la question : "Est-ce que ce signal aurait marché ?"
Génère un rapport de performance (winrate, RR moyen, etc.)
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class BacktestTrade:
    timestamp   : str
    pair        : str
    pattern     : str
    direction   : str
    entry       : float
    sl          : float
    tp1         : float
    tp2         : float
    rr_ratio    : float
    result      : str = ""         # WIN_TP2 / WIN_TP1 / LOSS / PENDING
    pnl_pct     : float = 0.0
    bars_held   : int = 0


@dataclass
class BacktestReport:
    total_trades    : int
    wins            : int
    losses          : int
    winrate_pct     : float
    avg_rr          : float
    best_trade_pct  : float
    worst_trade_pct : float
    total_pnl_pct   : float
    trades          : List[BacktestTrade] = field(default_factory=list)

    def print(self):
        print("\n" + "═"*55)
        print("  📊 RAPPORT DE BACKTESTING")
        print("═"*55)
        print(f"  Trades totaux  : {self.total_trades}")
        print(f"  Gagnants       : {self.wins}  ({self.winrate_pct:.1f}%)")
        print(f"  Perdants       : {self.losses}")
        print(f"  RR moyen       : 1:{self.avg_rr:.2f}")
        print(f"  Meilleur trade : +{self.best_trade_pct:.2f}%")
        print(f"  Pire trade     : {self.worst_trade_pct:.2f}%")
        print(f"  PnL total      : {self.total_pnl_pct:+.2f}%")
        print("═"*55 + "\n")


class Backtester:
    """
    Prend les signaux détectés par le bot et les teste
    sur les données OHLCV historiques.

    Usage :
        bt = Backtester(risk_pct=1.0)   # risque 1% par trade
        report = bt.run(signals, historical_data)
        report.print()
    """

    def __init__(self, risk_pct: float = 1.0, max_bars: int = 100):
        self.risk_pct = risk_pct       # % du capital risqué par trade
        self.max_bars = max_bars       # Nombre max de bougies à attendre

    def run(self, signals: list, ohlcv_df: pd.DataFrame) -> BacktestReport:
        """
        signals    : liste de dicts (sortie du scanner)
        ohlcv_df   : DataFrame avec colonnes [open, high, low, close, volume]
        """
        trades = []

        for sig in signals:
            trade = self._simulate_trade(sig, ohlcv_df)
            if trade:
                trades.append(trade)

        return self._compute_report(trades)

    def _simulate_trade(self, sig: dict, df: pd.DataFrame) -> Optional[BacktestTrade]:
        entry     = sig.get("entry")
        sl        = sig.get("sl") or sig.get("stop_loss")
        tp2       = sig.get("tp2")
        tp1       = sig.get("tp1")
        direction = sig.get("direction", "LONG")
        pattern   = sig.get("pattern", "UNKNOWN")
        pair      = sig.get("pair", "")
        timestamp = sig.get("timestamp", "")
        rr        = sig.get("rr_ratio", 0)

        if not all([entry, sl, tp2]):
            return None

        # Trouver la bougie d'entrée dans le DataFrame
        try:
            entry_idx = df.index.get_loc(timestamp, method="nearest")
        except Exception:
            entry_idx = len(df) - self.max_bars

        result    = "PENDING"
        pnl_pct   = 0.0
        bars_held = 0

        risk = abs(entry - sl)
        if risk == 0:
            return None

        # Simuler les bougies suivantes
        future = df.iloc[entry_idx + 1 : entry_idx + 1 + self.max_bars]

        for i, (_, bar) in enumerate(future.iterrows()):
            bars_held = i + 1

            if direction == "LONG":
                # Stop touché
                if bar["low"] <= sl:
                    result  = "LOSS"
                    pnl_pct = -(self.risk_pct)
                    break
                # TP2 touché
                if bar["high"] >= tp2:
                    reward  = abs(tp2 - entry)
                    result  = "WIN_TP2"
                    pnl_pct = self.risk_pct * (reward / risk)
                    break
                # TP1 touché
                if tp1 and bar["high"] >= tp1:
                    reward  = abs(tp1 - entry)
                    result  = "WIN_TP1"
                    pnl_pct = self.risk_pct * (reward / risk) * 0.5
                    break

            else:  # SHORT
                if bar["high"] >= sl:
                    result  = "LOSS"
                    pnl_pct = -(self.risk_pct)
                    break
                if bar["low"] <= tp2:
                    reward  = abs(entry - tp2)
                    result  = "WIN_TP2"
                    pnl_pct = self.risk_pct * (reward / risk)
                    break
                if tp1 and bar["low"] <= tp1:
                    reward  = abs(entry - tp1)
                    result  = "WIN_TP1"
                    pnl_pct = self.risk_pct * (reward / risk) * 0.5
                    break

        return BacktestTrade(
            timestamp  = str(timestamp),
            pair       = pair,
            pattern    = pattern,
            direction  = direction,
            entry      = entry,
            sl         = sl,
            tp1        = tp1 or 0,
            tp2        = tp2,
            rr_ratio   = rr,
            result     = result,
            pnl_pct    = round(pnl_pct, 3),
            bars_held  = bars_held,
        )

    def _compute_report(self, trades: List[BacktestTrade]) -> BacktestReport:
        if not trades:
            return BacktestReport(0, 0, 0, 0, 0, 0, 0, 0, [])

        wins      = [t for t in trades if t.result.startswith("WIN")]
        losses    = [t for t in trades if t.result == "LOSS"]
        pnls      = [t.pnl_pct for t in trades if t.result != "PENDING"]
        rrs       = [t.rr_ratio for t in trades if t.rr_ratio > 0]

        return BacktestReport(
            total_trades    = len(trades),
            wins            = len(wins),
            losses          = len(losses),
            winrate_pct     = len(wins) / max(len(trades), 1) * 100,
            avg_rr          = float(np.mean(rrs)) if rrs else 0,
            best_trade_pct  = max(pnls) if pnls else 0,
            worst_trade_pct = min(pnls) if pnls else 0,
            total_pnl_pct   = sum(pnls),
            trades          = trades,
        )
