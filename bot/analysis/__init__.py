"""
bot.analysis
────────────
Module d'analyse visuelle pour Trading Bot Ultimate.

Workflow sans API externe :
  1. Capturer les screenshots (semi-auto ou manuellement)
  2. Les organiser dans outputs/screenshots/
  3. Analyser directement dans Claude Code (qui lit les images nativement)

Modules :
  - vision_client      : Organisateur de screenshots
  - prompt_builder     : Construction des prompts optimisés
  - response_parser    : Parsing des résultats JSON
  - screenshot_capture : Capture d'écran macOS
"""

from bot.analysis.vision_client import VisionAnalyzer
from bot.analysis.prompt_builder import PromptBuilder
from bot.analysis.response_parser import ResponseParser

__all__ = ["VisionAnalyzer", "PromptBuilder", "ResponseParser"]
