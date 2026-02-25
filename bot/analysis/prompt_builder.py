"""
prompt_builder.py
─────────────────
Construction des prompts système et utilisateur pour l'analyse visuelle.
Charge les 17 modules de connaissances + la grille de scoring.
"""

import logging
from pathlib import Path

from bot.brain.claude_brain import ClaudeBrain

logger = logging.getLogger("PromptBuilder")

# Grille de scoring intégrée directement (depuis memory/scoring.md)
SCORING_RULES = """
## GRILLE DE SCORING — À SUIVRE STRICTEMENT

### Critères obligatoires (les 2 portes)
| # | Critère | Points |
|---|---------|--------|
| 1 | Zone S/R identifiée + testée | +1 (obligatoire) |
| 2 | Figure chartiste OU reversal candle | +1 (obligatoire) |

Si une porte manque → STOP TOTAL, score = 0, direction = NEUTRAL.

### Critères de confirmation
| # | Critère | Points |
|---|---------|--------|
| 3 | RSI sortie survente/surachat (zone 30/70) | +1 |
| 4 | RSI > 50 (ou < 50 pour short) | +0.5 |
| 5 | RSI divergence (Higher Lows / Lower Highs) | +1 |
| 6 | Ichimoku — prix au-dessus/sous kumo dans le bon sens | +1 |
| 7 | Ichimoku — twist du kumo dans le bon sens | +0.5 |
| 8 | EMAs alignées (8/21/50) dans le bon sens | +1 |
| 9 | ADX >= 20 + DI dans le bon sens | +0.5 |
| 10 | QQE croisé dans le bon sens | +0.5 |

### Bonus harmoniques
| 11 | Harmonique validée (point D + rebond) sur 1 TF | +1 |
| 12 | Harmonique validée sur 2 TF (même point D) | +1.5 |
| 13 | Harmonique validée sur 3+ TF (même point D) | +2 |
| 14 | Pattern harmonique Daily en formation vers la cible | +0.5 |

### Bonus supplémentaires
| 15 | Zone de compression avant breakout | +0.5 |
| 16 | Alignement multi-TF (>=3 TF même direction) | +1 |

### Score maximum : plafonné à 10

### Interprétation
| Score | Verdict | Action |
|-------|---------|--------|
| 0-2 | PAS DE TRADE | STOP |
| 3-4 | Faible conviction | Petit lot si 2 portes OK |
| 5-6 | Trade valide | Lot normal, SL strict |
| 7-8 | Signal fort | Lot normal, laisser courir |
| 9-10 | Signal premium | Confiance maximale |

### Scores minimum garantis
- 2 portes ouvertes seules = 4/10
- 2 portes + zone de demande forte = 5/10
- 2 portes + zone de demande + RSI sortie survente = 6/10
- JAMAIS donner un score < 4 si les 2 portes sont ouvertes
"""

# Adaptations par template MT4
TEMPLATE_FOCUS = {
    "Momentum": (
        "Tu analyses le template MOMENTUM. Focus sur :\n"
        "- Zones S/R (horizontales, niveaux clés)\n"
        "- Figures chartistes (ETE, Double Top/Bottom, triangles, drapeaux)\n"
        "- EMAs (8/21/50/200) : alignement et position du prix\n"
        "- ADX + DI : force de tendance\n"
        "- QQE : croisement ligne rapide/lente\n"
        "- MACD : croisement signal"
    ),
    "EXTREM_MONEY": (
        "Tu analyses le template EXTREM_MONEY OR 2. Focus sur :\n"
        "- Zones S/R (horizontales)\n"
        "- Ichimoku : position prix vs kumo, Tenkan/Kijun, twist kumo\n"
        "- Stochastique : zones surachat >80 / survente <20\n"
        "- Figures chartistes si visibles"
    ),
    "RSI": (
        "Tu analyses le template RSI. Focus sur :\n"
        "- RSI valeur actuelle et zones 30/70\n"
        "- RSI divergences (prix HH + RSI LH = bearish, prix LL + RSI HL = bullish)\n"
        "- RSI par rapport à 50 (au-dessus = bullish, en-dessous = bearish)\n"
        "- Zones S/R en arrière-plan\n"
        "- EMAs si visibles"
    ),
    "Harmoniques": (
        "Tu analyses le template HARMONIQUES. Focus sur :\n"
        "- Patterns harmoniques : Butterfly, Shark, Gartley, Bat, Crab\n"
        "- Points X, A, B, C, D et ratios Fibonacci\n"
        "- Point D atteint ou pas (zone de retournement)\n"
        "- Zone S/R au niveau du point D\n"
        "- Rebond ou non au point D"
    ),
}

# Format JSON attendu
RESPONSE_SCHEMA = """
Tu DOIS répondre UNIQUEMENT avec un bloc JSON valide (pas de texte avant/après) :

```json
{
  "gate1_sr": {
    "found": true/false,
    "type": "support|resistance",
    "level": 1.2650,
    "strength": "forte|moyenne|faible",
    "description": "Support horizontal testé 3 fois"
  },
  "gate2_pattern": {
    "found": true/false,
    "type": "figure|candle",
    "name": "Double Bottom W",
    "direction": "LONG|SHORT",
    "description": "Double bottom clair avec neckline à 1.2700"
  },
  "indicators": {
    "adx": {"value": 28.5, "di_direction": "LONG|SHORT|NEUTRAL", "valid": true},
    "rsi": {"value": 42.0, "zone": "normal|surachat|survente", "divergence": "none|bullish|bearish"},
    "qqe": {"crossed": true, "direction": "LONG|SHORT"},
    "ema": {"aligned": true, "direction": "LONG|SHORT", "price_vs_200": "above|below"},
    "ichimoku": {"price_vs_kumo": "above|below|inside", "twist": true, "direction": "LONG|SHORT|NEUTRAL"},
    "macd": {"crossed": true, "direction": "LONG|SHORT"},
    "stoch": {"value": 25.0, "zone": "normal|surachat|survente"}
  },
  "harmonics": {
    "found": false,
    "pattern": null,
    "point_d_reached": false,
    "description": null
  },
  "compression": {
    "found": false,
    "description": null
  },
  "confluence_score": 7,
  "direction": "LONG|SHORT|NEUTRAL",
  "entry": 1.2650,
  "sl": 1.2600,
  "tp1": 1.2750,
  "tp2": 1.2850,
  "rr_ratio": 2.0,
  "summary": "Double bottom W sur support fort à 1.2650. RSI en divergence bullish. EMAs alignées haussières. Score 7/10 — signal fort.",
  "warnings": ["H4 pas encore aligné", "Attendre clôture bougie H1"]
}
```

RÈGLES :
- Si gate1 OU gate2 est false → confluence_score = 0, direction = "NEUTRAL"
- entry/sl/tp1/tp2 = prix réels lus sur le graphique (pas inventés)
- rr_ratio = distance entry→tp1 / distance entry→sl (minimum 1:2)
- Ne JAMAIS donner un score < 4 si les 2 portes sont ouvertes
"""


class PromptBuilder:
    """Construit les prompts système et utilisateur pour l'analyse visuelle."""

    def __init__(self):
        self.brain = ClaudeBrain()

    def build_system_prompt(self) -> str:
        """
        Construit le prompt système complet avec :
        - Identité du trader expert
        - Les 17 modules de connaissances
        - La grille de scoring
        - Le format de réponse JSON
        """
        knowledge = self.brain.get_context()

        return (
            "Tu es un trader technique expert. Tu analyses les graphiques MT4/TradingView "
            "exactement comme un trader professionnel formé aux méthodes suivantes.\n\n"
            "# CONNAISSANCES TRADING\n\n"
            f"{knowledge}\n\n"
            "# GRILLE DE SCORING\n\n"
            f"{SCORING_RULES}\n\n"
            "# FORMAT DE RÉPONSE\n\n"
            f"{RESPONSE_SCHEMA}"
        )

    def build_user_prompt(self, pair: str, timeframe: str, template: str = "Momentum") -> str:
        """
        Construit le prompt utilisateur adapté au template MT4.

        Args:
            pair: Paire tradée
            timeframe: Timeframe affiché
            template: Template MT4 (Momentum, RSI, Harmoniques, EXTREM_MONEY)
        """
        focus = TEMPLATE_FOCUS.get(template, TEMPLATE_FOCUS["Momentum"])

        return (
            f"Analyse ce graphique : **{pair}** en **{timeframe}**\n\n"
            f"{focus}\n\n"
            "Applique la méthode des 2 portes obligatoires, puis score chaque confirmation.\n"
            "Donne l'analyse complète en JSON structuré comme demandé.\n"
            "Lis les prix RÉELS sur le graphique pour entry/SL/TP."
        )

    def build_batch_summary_prompt(self, pair: str, analyses: list[dict]) -> str:
        """
        Construit un prompt pour synthétiser les analyses de 4 templates.
        Utilisé en mode semi-auto après avoir analysé les 4 templates d'un TF.
        """
        import json

        summaries = []
        for a in analyses:
            template = a.get("_meta", {}).get("template", "?")
            score = a.get("confluence_score", 0)
            direction = a.get("direction", "NEUTRAL")
            summary = a.get("summary", "N/A")
            summaries.append(f"- **{template}** : Score {score}/10, {direction} — {summary}")

        templates_text = "\n".join(summaries)

        return (
            f"Synthèse multi-template pour **{pair}** :\n\n"
            f"{templates_text}\n\n"
            "Donne le score final consolidé et la recommandation."
        )
