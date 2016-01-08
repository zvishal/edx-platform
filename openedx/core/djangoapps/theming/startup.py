"""
Startup code for Comprehensive Theming
"""

from path import Path as path
from django.conf import settings

from .core import enable_comprehensive_theme


def run():
    """Enable comprehensive theming, if we should."""
    if settings.COMPREHENSIVE_THEME_DIR:
        theme_dirs = [settings.COMPREHENSIVE_THEME_DIR]
    elif settings.COMPREHENSIVE_THEME_DIRS:
        theme_dirs = settings.COMPREHENSIVE_THEME_DIRS
    for theme_dir in theme_dirs:
        enable_comprehensive_theme(theme_dir=path(theme_dir))
