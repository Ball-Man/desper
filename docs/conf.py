# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
import os.path

# Current path
sys.path.insert(0, os.path.abspath('.'))

# Desper path
sys.path.insert(0, os.path.abspath('..'))

try:
    import desper
    print("Desper docs")
except ImportError:
    print("Desper not found")
    sys.exit(1)

project = 'desper'
copyright = '2022, Francesco Mistri'
author = 'Francesco Mistri'
release = desper.version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = '_static/desper-logo.png'
html_favicon = '_static/desper-logo.png'

# Autodoc options
# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = False
