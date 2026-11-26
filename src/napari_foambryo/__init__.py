"""napari-foambryo: surface tensions and cell pressures of a 2-D or 3-D segmentation, in napari.

A napari plugin over delaunay-watershed (the multimaterial mesh of a segmentation) and foambryo (relative surface
tensions and cell pressures from the mesh's geometry). Every number it shows or writes is one a public function of
the two libraries returns for the same inputs, the same functions the `foambryo` command calls; it computes nothing
scientific of its own. How it works, dock by dock: `docs/how-it-works.md`.
"""

__version__ = "0.2.0"
