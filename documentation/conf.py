# -*- coding: utf-8 -*-

import sys
import os

try:
    import sphinx_rtd_theme
    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
except ImportError:
    pass

DOCDIR = os.path.dirname(__file__)
PACKAGE_DIR = os.path.dirname(DOCDIR)
SRC_DIR = os.path.join(PACKAGE_DIR, "src")
CHANGES_FILE = os.path.join(PACKAGE_DIR, "CHANGES")

sys.path.append(SRC_DIR)

extensions = [
    'sphinx.ext.autodoc'
]

source_suffix = '.rst'

master_doc = 'index'

project = u'Resource API'
copyright = u'2014, F-Secure'

with open(CHANGES_FILE) as fil:
    version = fil.readline().split()[0]

release = version
exclude_patterns = ['_build']
pygments_style = 'sphinx'
htmlhelp_basename = 'ResourceAPIdoc'
