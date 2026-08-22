"""Sphinx configuration for PhotoShare API documentation."""

import sys
from pathlib import Path

PROJECT_ROOT = Path( __file__ ).resolve().parents[ 1 ]

sys.path.insert( 0, str( PROJECT_ROOT ), )

project = "PhotoShare API"
copyright = "2026, Andrey Rybchenko"
author = "Andrey Rybchenko"
release = "0.1.0"

extensions = [ "sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.viewcode", "sphinx.ext.autosectionlabel", ]

templates_path = [ "_templates", ]

exclude_patterns = [ "_build", "Thumbs.db", ".DS_Store", ]

language = "uk"

html_theme = "alabaster"

html_static_path = [ "_static", ]

autodoc_typehints = "description"
autodoc_member_order = "bysource"

autosectionlabel_prefix_document = True
