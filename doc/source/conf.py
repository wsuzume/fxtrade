# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'fxtrade'
copyright = '2022, Josh Nobus'
author = 'Josh Nobus'
release = '0.0.6'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

#extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx.ext.napoleon',
    'sphinx.ext.githubpages'
]

templates_path = ['_templates']
exclude_patterns = []

language = 'ja'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'bizstyle'
html_static_path = ['_static']

#autodoc_default_flags = [
#    'members',
#    'special-members',
#]

autodoc_default_options = {
    #'members': 'var1, var2',
    'member-order': 'bysource',
    'special-members': '__init__, __abs__, __pos__, __neg__, __invert__, ' \
			+ '__lt__, __le__, __eq__, __ne__, __ge__, __gt__, ' \
			+ '__add__, __radd__, __sub__, __rsub__, ' \
			+ '__mul__, __rmul__, __truediv__, __floordiv__, ' \
			+ '__pow__, __mod__',
    'undoc-members': True,
    #'exclude-members': '__weakref__'
}

import os
import sys
sys.path.insert(0, os.path.abspath('../../'))
