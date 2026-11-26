"""The package's `__version__` is the installed distribution's version.

Until the first release candidate of 0.2.0, `napari_foambryo.__version__` still said 0.1.0 while the distribution was
a development version of 0.2.0.
"""

from importlib.metadata import version

import napari_foambryo


def test_version_attribute_is_the_installed_distribution_version():
    assert napari_foambryo.__version__ == version("napari-foambryo")
