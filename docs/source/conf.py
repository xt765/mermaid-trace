import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))

project = 'LogCapy'
copyright = '2026, LogCapy Team'
author = 'LogCapy Team'
release = '0.1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'alabaster'
html_static_path = ['_static']
