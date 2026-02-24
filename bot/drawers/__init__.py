"""
drawers/__init__.py
───────────────────
REGISTRE DES DRAWERS — Auto-chargement de tous les drawers disponibles.

Fonctionnement :
  1. Au démarrage, charge automatiquement tous les drawers définis
  2. Si un drawer spécifique est trouvé → l'utilise
  3. Si AUCUN drawer n'est trouvé pour une figure → utilise le FALLBACK GÉNÉRIQUE
  4. AUCUNE erreur possible, JAMAIS

Usage :
    from bot.drawers import DrawerRegistry
    registry = DrawerRegistry()
    output = registry.draw(signal)
"""

import importlib
import inspect
import logging
from typing import Dict, Type

from .base_drawer import BaseDrawer, DrawingOutput, GenericFallbackDrawer

# Import explicite de tous les modules de drawers disponibles
_DRAWER_MODULES = [
    "bot.drawers.chart_drawers",
    "bot.drawers.harmonic_drawers",
    "bot.drawers.special_drawers",
]

logger = logging.getLogger("DrawerRegistry")


class DrawerRegistry:
    """
    Registre central de tous les drawers.
    ─────────────────────────────────────
    - Charge automatiquement TOUS les drawers disponibles au démarrage
    - Mappe chaque pattern_name à son drawer
    - Si un drawer manque → Fallback générique (jamais d'erreur)
    - Permet d'ajouter de nouveaux drawers sans modifier ce fichier
    """

    # Mapping manuel : nom du pattern → classe du drawer
    # Permet les alias (ex: "ETE" et "HEAD_SHOULDERS" → même drawer)
    PATTERN_MAP: Dict[str, str] = {
        # Figures chartistes
        "ETE"                    : "HeadShouldersDrawer",
        "HEAD_SHOULDERS"         : "HeadShouldersDrawer",
        "ETE_INVERSE"            : "InverseHSDrawer",
        "INVERSE_HEAD_SHOULDERS" : "InverseHSDrawer",
        "DOUBLE_TOP"             : "DoubleTopDrawer",
        "DOUBLE_BOTTOM"          : "DoubleBottomDrawer",
        "BULL_FLAG"              : "BullFlagDrawer",
        "DRAPEAU_HAUSSIER"       : "BullFlagDrawer",
        "BEAR_FLAG"              : "BearFlagDrawer",
        "DRAPEAU_BAISSIER"       : "BearFlagDrawer",
        "BISEAU_ASCENDANT"       : "RisingWedgeDrawer",
        "RISING_WEDGE"           : "RisingWedgeDrawer",
        "BISEAU_DESCENDANT"      : "FallingWedgeDrawer",
        "FALLING_WEDGE"          : "FallingWedgeDrawer",
        "TRIANGLE_ASCENDANT"     : "AscendingTriangleDrawer",
        "ASCENDING_TRIANGLE"     : "AscendingTriangleDrawer",
        "TRIANGLE_DESCENDANT"    : "DescendingTriangleDrawer",
        "DESCENDING_TRIANGLE"    : "DescendingTriangleDrawer",
        "TRIANGLE_SYMETRIQUE"    : "SymmetricTriangleDrawer",
        "SYMMETRIC_TRIANGLE"     : "SymmetricTriangleDrawer",
        "PENNANT"                : "GenericFallbackDrawer",   # Fallback jusqu'au drawer dédié
        "FANION"                 : "GenericFallbackDrawer",

        # Harmoniques
        "BUTTERFLY"              : "ButterflyDrawer",
        "BUTTERFLY_BULLISH"      : "ButterflyDrawer",
        "BUTTERFLY_BEARISH"      : "ButterflyDrawer",
        "SHARK"                  : "SharkDrawer",
        "SHARK_BULLISH"          : "SharkDrawer",
        "SHARK_BEARISH"          : "SharkDrawer",

        # Compressions
        "COMPRESSION"            : "CompressionDrawer",
        "ZONE_COMPRESSION"       : "CompressionDrawer",

        # Chandeliers reversal (tous → même drawer universel)
        "PIN_BAR_BULLISH"        : "ReversalCandleDrawer",
        "PIN_BAR_BEARISH"        : "ReversalCandleDrawer",
        "MARTEAU"                : "ReversalCandleDrawer",
        "HAMMER"                 : "ReversalCandleDrawer",
        "ETOILE_FILANTE"         : "ReversalCandleDrawer",
        "SHOOTING_STAR"          : "ReversalCandleDrawer",
        "BULLISH_ENGULFING"      : "ReversalCandleDrawer",
        "BEARISH_ENGULFING"      : "ReversalCandleDrawer",
        "MORNING_STAR"           : "ReversalCandleDrawer",
        "EVENING_STAR"           : "ReversalCandleDrawer",
        "HARAMI_BULLISH"         : "ReversalCandleDrawer",
        "HARAMI_BEARISH"         : "ReversalCandleDrawer",
        "DOJI"                   : "ReversalCandleDrawer",
    }

    def __init__(self):
        self._drawers: Dict[str, BaseDrawer] = {}
        self._classes: Dict[str, Type[BaseDrawer]] = {}
        self._fallback = GenericFallbackDrawer()
        self._load_all_drawers()

    def _load_all_drawers(self):
        """
        Charge automatiquement tous les drawers depuis les modules définis.
        Découverte automatique = pas besoin de toucher ce fichier pour ajouter un drawer.
        """
        # Toujours enregistrer le fallback
        self._classes["GenericFallbackDrawer"] = GenericFallbackDrawer

        for module_path in _DRAWER_MODULES:
            try:
                module = importlib.import_module(module_path)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseDrawer) and obj not in (BaseDrawer, GenericFallbackDrawer):
                        self._classes[name] = obj
                        logger.debug(f"✅ Drawer chargé : {name}")
            except ImportError as e:
                logger.warning(f"⚠️ Module {module_path} non chargé : {e}")
            except Exception as e:
                logger.warning(f"⚠️ Erreur chargement {module_path} : {e}")

        logger.info(f"📦 {len(self._classes)} drawers disponibles : {list(self._classes.keys())}")

    def register(self, pattern_name: str, drawer_class: Type[BaseDrawer]):
        """
        Enregistre manuellement un nouveau drawer.
        Utile pour ajouter des drawers externes sans modifier le code existant.

        Usage :
            from mon_nouveau_drawer import GartleyDrawer
            registry.register("GARTLEY", GartleyDrawer)
        """
        self._classes[drawer_class.__name__] = drawer_class
        self.PATTERN_MAP[pattern_name] = drawer_class.__name__
        logger.info(f"✅ Drawer enregistré manuellement : {pattern_name} → {drawer_class.__name__}")

    def get_drawer(self, pattern_name: str) -> BaseDrawer:
        """
        Retourne le drawer approprié pour un pattern.
        Si le pattern n'est pas connu → retourne le fallback générique.
        JAMAIS d'erreur.
        """
        pattern_upper = pattern_name.upper()

        # 1. Chercher dans le mapping
        class_name = self.PATTERN_MAP.get(pattern_upper)

        # 2. Chercher par nom exact de classe
        if not class_name and pattern_upper in self._classes:
            class_name = pattern_upper

        # 3. Instancier si trouvé
        if class_name and class_name in self._classes:
            if class_name not in self._drawers:
                self._drawers[class_name] = self._classes[class_name]()
            return self._drawers[class_name]

        # 4. Fallback générique — JAMAIS d'erreur
        logger.warning(f"⚠️ Aucun drawer pour '{pattern_name}' → Fallback générique utilisé")
        return self._fallback

    def draw(self, signal: dict) -> DrawingOutput:
        """
        Point d'entrée principal.
        Appelle le bon drawer selon signal["pattern"].
        Toujours retourne un DrawingOutput valide.
        """
        pattern = signal.get("pattern", "UNKNOWN")
        drawer  = self.get_drawer(pattern)

        try:
            return drawer.draw(signal)
        except Exception as e:
            # Si le drawer spécifique plante → fallback sans erreur
            logger.error(f"❌ Erreur dans drawer {type(drawer).__name__} : {e}")
            logger.warning("🔄 Utilisation du fallback générique")
            try:
                return self._fallback.draw(signal)
            except Exception as e2:
                # Dernier recours absolu
                logger.critical(f"💀 Même le fallback a planté : {e2}")
                return DrawingOutput(
                    pattern_name   = pattern,
                    direction      = signal.get("direction", "NEUTRE"),
                    entry_price    = signal.get("entry", 0),
                    stop_loss      = 0, tp1=0, tp2=0,
                    pine_script    = f'// ERREUR: Impossible de générer le dessin pour {pattern}',
                    mql4_script    = f'// ERREUR: Impossible de générer le dessin pour {pattern}',
                    description    = f"ERREUR CRITIQUE — {pattern} non dessinable",
                    elements_drawn = []
                )

    def list_available(self) -> list:
        """Retourne la liste de tous les patterns supportés avec leur drawer."""
        result = []
        for pattern, class_name in self.PATTERN_MAP.items():
            is_fallback = class_name == "GenericFallbackDrawer"
            status = "🔄 fallback" if is_fallback else "✅ dédié"
            result.append({"pattern": pattern, "drawer": class_name, "status": status})
        return result

    def print_status(self):
        """Affiche l'état du registre dans le terminal."""
        print("\n" + "═"*55)
        print("  📦 DRAWER REGISTRY — ÉTAT")
        print("═"*55)
        dedicated = sum(1 for v in self.PATTERN_MAP.values() if v != "GenericFallbackDrawer")
        fallback  = len(self.PATTERN_MAP) - dedicated
        print(f"  Drawers dédiés   : {dedicated}")
        print(f"  Fallback générique: {fallback}")
        print(f"  Total patterns   : {len(self.PATTERN_MAP)}")
        print(f"  Classes chargées : {len(self._classes)}")
        print("═"*55)
        for item in self.list_available():
            print(f"  {item['status']}  {item['pattern']:30s} → {item['drawer']}")
        print("═"*55 + "\n")


# ──────────────────────────────────────────────────────────────────
# Instance globale — importer directement pour utiliser
# ──────────────────────────────────────────────────────────────────
registry = DrawerRegistry()

__all__ = ["DrawerRegistry", "DrawingOutput", "registry"]
