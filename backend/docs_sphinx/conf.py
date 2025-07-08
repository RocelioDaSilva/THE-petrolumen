import os
import sys

# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath("../.."))  # Points to the repository root
sys.path.insert(0, os.path.abspath(".."))  # Points to backend/

# -- Project information -----------------------------------------------------
project = "PetroLúmen Backend"
copyright = "2024, PetroLúmen Team"
author = "PetroLúmen Team"

# The full version, including alpha/beta/rc tags
release = "0.3.0"
version = "0.3.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",  # Include documentation from docstrings
    "sphinx.ext.doctest",  # Test snippets in the documentation
    "sphinx.ext.intersphinx",  # Link to other projects' documentation
    "sphinx.ext.todo",  # Support for todo items
    "sphinx.ext.coverage",  # Collect doc coverage stats
    "sphinx.ext.mathjax",  # Render math via MathJax
    "sphinx.ext.ifconfig",  # Conditionally include content based on configuration
    "sphinx.ext.viewcode",  # Add links to highlighted source code
    "sphinx.ext.githubpages",  # Support for GitHub Pages
    "sphinx.ext.napoleon",  # Support for Google and NumPy style docstrings
    "sphinx_rtd_theme",  # Read the Docs theme
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# -- Options for intersphinx extension ---------------------------------------
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# -- Options for todo extension ----------------------------------------------
todo_include_todos = True

# -- Autodoc options ---------------------------------------------------------
autodoc_member_order = "bysource"  # Or 'alphabetical', 'groupwise'
autodoc_default_options = {
    "members": True,
    "undoc-members": True,  # Good to see what's missing docs
    "private-members": False,
    "special-members": "__init__",
    "show-inheritance": True,
}
# autodoc_typehints = "description" # Alternative: "signature" or "none"
# napoleon_google_docstring = True
# napoleon_numpy_docstring = True
# napoleon_include_init_with_doc = False
# napoleon_include_private_with_doc = False
# napoleon_include_special_with_doc = True
# napoleon_use_admonition_for_examples = False
# napoleon_use_admonition_for_notes = False
# napoleon_use_admonition_for_references = False
# napoleon_use_ivar = False
# napoleon_use_param = True
# napoleon_use_rtype = True
# napoleon_preprocess_types = False
# napoleon_type_aliases = None
# napoleon_attr_annotations = True
