# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "acoupi"

release = "0.1.0"

copyright = "2023, Aude Vuilliomenet, Santiago Martinez Balvanera"

author = "Aude Vuilliomenet, Santiago Martinez Balvanera"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.duration",
    "sphinx_copybutton",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference/", None),
    "matplotlib": ("https://matplotlib.org/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable/", None),
    "seaborn": ("https://seaborn.pydata.org/", None),
    "sklearn": ("https://scikit-learn.org/stable/", None),
    "statsmodels": ("https://www.statsmodels.org/stable/", None),
    "pytorch": ("https://pytorch.org/docs/stable/", None),
    "torchvision": ("https://pytorch.org/vision/stable/", None),
    "torchaudio": ("https://pytorch.org/audio/stable/", None),
    "xarray": ("https://xarray.pydata.org/en/stable/", None),
    "dask": ("https://docs.dask.org/en/latest/", None),
    "jax": ("https://jax.readthedocs.io/en/latest/", None),
    "pony": ("https://docs.ponyorm.org/", None),
}

templates_path = ["_templates"]

exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"

html_static_path = ["_static"]

html_theme_options = {
    "source_repository": "https://github.com/audevuilli/acoupi",
    "source_branch": "main",
    "source_directory": "docs/",
}
