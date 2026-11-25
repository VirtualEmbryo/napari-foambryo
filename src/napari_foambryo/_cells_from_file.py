"""A mesh file opened as layer data: the reader's work, without a viewer (so that it can be tested alone).

A 3-D file opens as `<file> cells` (each cell's closed surface) and `<file> crop faces`; a 2-D file (its appendix's
`dimension = 2`, or its layout) as `<file> interfaces` (dark grey ribbons, 2-D) and `<file> image border`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from foambryo import dcel_mesh_from_file

from napari_foambryo._display import cell_side_copy, crop_face_copy, is_planar
from napari_foambryo._layers import (
    CROP_FACE_LAYER,
    CROP_FACE_RGBA,
    RUNS,
    _label_palette,
    _metadata,
    new_run_id,
    prepare_mesh_layers,
)
from napari_foambryo._runs import Run

__all__ = ["mesh_layers_from_file"]


def mesh_layers_from_file(path: Path) -> list[tuple[Any, dict, str]]:
    """Read a mesh file with foambryo's reader, register it as a run, and return its layers' data."""
    mesh = dcel_mesh_from_file(path)
    run = Run(run_id=new_run_id(), mesh=mesh, rec_bytes=path.read_bytes(), rec_name=path.name)
    RUNS[run.run_id] = run
    if is_planar(mesh):
        return [
            (
                (layer.vertices, layer.copy.faces),
                {
                    "name": f"{path.stem} {layer.kind}",
                    "vertex_colors": layer.colours,
                    "metadata": _metadata(run, layer.kind, layer.copy, base_name=path.stem, **layer.extra),
                },
                "surface",
            )
            for layer in prepare_mesh_layers(run, path.stem)
        ]
    cells = cell_side_copy(mesh)
    layers = [
        (
            (cells.vertices, cells.faces),
            {
                "name": f"{path.stem} cells",
                "vertex_colors": _label_palette(cells.vertex_group),
                "metadata": _metadata(run, "cells", cells, base_name=path.stem),
            },
            "surface",
        )
    ]
    crop = crop_face_copy(mesh)
    if crop is not None:
        layers.append(
            (
                (crop.vertices, crop.faces),
                {
                    "name": f"{path.stem} crop faces",
                    "vertex_colors": np.tile(np.asarray(CROP_FACE_RGBA, dtype=np.float32), (len(crop.vertices), 1)),
                    **CROP_FACE_LAYER,
                    "metadata": _metadata(run, "crop faces", crop, base_name=path.stem),
                },
                "surface",
            )
        )
    return layers
