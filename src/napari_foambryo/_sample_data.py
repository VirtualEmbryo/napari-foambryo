"""Sample data: benchmark case 000 with its true tensions, three small generated foams, and four 2-D samples.

* **Benchmark case 000** (6 cells, 194 × 200 × 199 voxels): a simulated aggregate at mechanical equilibrium from the
  benchmark of the method's 2023 paper (Ichbiah et al., Nature Methods, doi:10.1038/s41592-023-02084-7), with its
  true tensions and pressures, so that inferred values can be compared with true ones. Voxel units.
* **Generated foams** (12 Voronoi cells in a ball, built here from a fixed seed): cubic voxels; the same foam
  sampled every second z slice (anisotropic voxels); and the same foam cut by the image box (cut cells). They are
  not at equilibrium, so their tensions mean nothing: they show the workflow, not the method's accuracy.

Two-dimensional samples, beside them (`sample_data/README.md` gives their provenance, licence and citation):

* **A 2-D foam with known tensions and pressures** (8 cells, 144 × 141 pixels): a circular-arc foam at mechanical
  equilibrium (force balance and Laplace's law certified to 1e-9 in the generator's units), from the generator of
  foambryo's 2-D benchmark at a fixed seed, rasterised exactly at pixel centres, mean cell radius 20 px; its true
  tensions and pressures (per pixel) travel with it, as case 000's do. Pixel units.
* **Three frames of 4-cell *C. elegans* embryos** from the data of Yamamoto et al., Developmental Cell 2026
  (CC BY-SA 4.0): a non-perturbed embryo inside its eggshell, one whose eggshell was removed, and an embryo after
  hmr-1; hmp-2 RNAi. Each opens as the membrane image and its segmentation (four cells), at 4.0702 pixels per µm.

A sample's Labels layer carries its voxel (or pixel) size in `metadata["foambryo"]`, which the Reconstruct widget reads.
"""

from __future__ import annotations

from functools import cache
from importlib.resources import files
from typing import Any

import numpy as np

__all__ = [
    "benchmark_case_000",
    "c_elegans_4_cell_with_eggshell",
    "c_elegans_4_cell_without_eggshell",
    "c_elegans_rnai_frame",
    "foam_anisotropic",
    "foam_cropped",
    "foam_cubic",
    "generated_foam",
    "true_values",
    "two_dimensional_foam",
    "two_dimensional_true_values",
]

#: The generated foams' voxel size, in micrometres (nominal: they are not images of anything).
FOAM_VOXEL_UM = 0.5


@cache
def _case_000() -> dict[str, np.ndarray]:
    with files("napari_foambryo").joinpath("sample_data/benchmark_case_000.npz").open("rb") as handle:
        data = np.load(handle, allow_pickle=False)
        return {key: data[key] for key in data.files}


def true_values() -> tuple[dict[tuple[int, int], float], dict[int, float]]:
    """Case 000's true tensions `(label_1, label_2) -> tension` and pressures `label -> pressure`."""
    data = _case_000()
    tensions = {
        (int(a), int(b)): float(t)
        for a, b, t in zip(
            data["true_tension_label_1"], data["true_tension_label_2"], data["true_tension"], strict=True
        )
    }
    pressures = {int(k): float(p) for k, p in zip(data["true_pressure_label"], data["true_pressure"], strict=True)}
    return tensions, pressures


def benchmark_case_000() -> list[tuple[Any, dict, str]]:
    """Case 000 as a Labels layer, with its voxel size and its true values in the layer's metadata."""
    data = _case_000()
    tensions, pressures = true_values()
    spacing = tuple(float(v) for v in data["spacing"])
    metadata = {
        "foambryo": {
            "sample": "benchmark case 000",
            "spacing": spacing,
            "spacing_unit": str(data["spacing_unit"]),
            "true_tensions": [[a, b, t] for (a, b), t in tensions.items()],
            "true_pressures": [[k, p] for k, p in pressures.items()],
            "about": "a simulated 6-cell aggregate at equilibrium, from the benchmark of the method's 2023 paper "
            "(doi:10.1038/s41592-023-02084-7); voxel units",
        }
    }
    return [(data["mask"], {"name": "benchmark case 000", "scale": spacing, "metadata": metadata}, "labels")]


def generated_foam(n: int = 96, radius: float = 44.0, n_cells: int = 12, seed: int = 7) -> np.ndarray:
    """Voronoi cells filling a ball, on an `n`³ grid of cubic voxels; 0 is the medium."""
    rng = np.random.default_rng(seed)
    centre = (n - 1) / 2
    seeds = []
    while len(seeds) < n_cells:
        point = rng.uniform(-radius * 0.75, radius * 0.75, 3)
        if np.linalg.norm(point) < radius * 0.75 and all(np.linalg.norm(point - s) > radius * 0.35 for s in seeds):
            seeds.append(point)
    seeds = np.asarray(seeds) + centre
    z, y, x = np.indices((n, n, n), dtype=np.float64)
    grid = np.stack([z, y, x], axis=-1)
    ball = ((grid - centre) ** 2).sum(axis=-1) <= radius**2
    distances = ((grid[..., None, :] - seeds) ** 2).sum(axis=-1)
    return np.where(ball, distances.argmin(axis=-1) + 1, 0).astype(np.uint16)


def _foam_layer(mask: np.ndarray, name: str, spacing: tuple[float, float, float], about: str) -> list:
    metadata = {"foambryo": {"sample": name, "spacing": spacing, "spacing_unit": "um", "about": about}}
    return [(mask, {"name": name, "scale": spacing, "metadata": metadata}, "labels")]


def foam_cubic() -> list[tuple[Any, dict, str]]:
    """The generated foam, cubic voxels."""
    return _foam_layer(
        generated_foam(),
        "generated foam",
        (FOAM_VOXEL_UM,) * 3,
        "12 Voronoi cells in a ball (not at equilibrium: its tensions mean nothing)",
    )


def foam_anisotropic() -> list[tuple[Any, dict, str]]:
    """The same foam sampled every second z slice: voxels twice as long along z."""
    return _foam_layer(
        generated_foam()[::2],
        "generated foam, z step 2×",
        (2 * FOAM_VOXEL_UM, FOAM_VOXEL_UM, FOAM_VOXEL_UM),
        "the generated foam, every second z slice (anisotropic voxels)",
    )


def foam_cropped() -> list[tuple[Any, dict, str]]:
    """The same foam cut by the image box (its first 20 z slices removed): cells reach the box and are cut."""
    return _foam_layer(
        np.ascontiguousarray(generated_foam()[20:]),
        "generated foam, cut by the image box",
        (FOAM_VOXEL_UM,) * 3,
        "the generated foam without its first 20 z slices (cut cells)",
    )


# ---------------------------------------------------------------------------------------------
# two-dimensional samples
# ---------------------------------------------------------------------------------------------
#: The citation of the data the three embryo frames come from (CC BY-SA 4.0); also in `sample_data/README.md`.
DEVELOPMENTAL_CELL_2026 = (
    "Yamamoto K., Ichbiah S., Perez M., Borrego-Pinto J., Delbary F., Goehring N. W., Northrop P., Turlier H., "
    "Charras G. Spatiotemporal mapping of the contractile and adhesive forces sculpting early C. elegans embryos. "
    "Developmental Cell 61(6), 1273-1288.e4 (2026). doi:10.1016/j.devcel.2026.04.013"
)


@cache
def _npz(name: str) -> dict[str, np.ndarray]:
    with files("napari_foambryo").joinpath(f"sample_data/{name}.npz").open("rb") as handle:
        data = np.load(handle, allow_pickle=False)
        return {key: data[key] for key in data.files}


def two_dimensional_true_values() -> tuple[dict[tuple[int, int], float], dict[int, float]]:
    """The 2-D foam's true tensions `(label_1, label_2) -> tension` and pressures `label -> pressure` (per pixel)."""
    data = _npz("two_dimensional_foam")
    tensions = {
        (int(a), int(b)): float(t)
        for a, b, t in zip(
            data["true_tension_label_1"], data["true_tension_label_2"], data["true_tension"], strict=True
        )
    }
    pressures = {int(k): float(p) for k, p in zip(data["true_pressure_label"], data["true_pressure"], strict=True)}
    return tensions, pressures


def two_dimensional_foam() -> list[tuple[Any, dict, str]]:
    """The 2-D foam as a Labels layer, with its pixel size and its true values in the layer's metadata."""
    data = _npz("two_dimensional_foam")
    tensions, pressures = two_dimensional_true_values()
    spacing = tuple(float(v) for v in data["spacing"])
    metadata = {
        "foambryo": {
            "sample": "2-D foam with known tensions",
            "spacing": spacing,
            "spacing_unit": str(data["spacing_unit"]),
            "true_tensions": [[a, b, t] for (a, b), t in tensions.items()],
            "true_pressures": [[k, p] for k, p in pressures.items()],
            "about": str(data["about"]),
        }
    }
    return [(data["mask"], {"name": "2-D foam", "scale": spacing, "metadata": metadata}, "labels")]


def _embryo_frame(name: str, title: str) -> list[tuple[Any, dict, str]]:
    """An embryo frame: its membrane image and its segmentation (Labels), both at the data's pixel size."""
    data = _npz(name)
    spacing = tuple(float(v) for v in data["spacing"])
    about = {"source": str(data["source"]), "licence": str(data["licence"]), "citation": str(data["citation"])}
    metadata = {"foambryo": {"sample": title, "spacing": spacing, "spacing_unit": str(data["spacing_unit"]), **about}}
    return [
        (data["image"], {"name": f"{title} (membrane)", "scale": spacing, "colormap": "gray",
                         "metadata": {"foambryo": about}}, "image"),
        (data["mask"], {"name": title, "scale": spacing, "metadata": metadata}, "labels"),
    ]


def c_elegans_4_cell_with_eggshell() -> list[tuple[Any, dict, str]]:
    """A 4-cell C. elegans embryo inside its eggshell (Developmental Cell 2026, CC BY-SA 4.0): image and cells."""
    return _embryo_frame("c_elegans_4_cell_with_eggshell_frame", "C. elegans 4-cell, with eggshell")


def c_elegans_4_cell_without_eggshell() -> list[tuple[Any, dict, str]]:
    """A 4-cell C. elegans embryo whose eggshell was removed (Developmental Cell 2026, CC BY-SA 4.0)."""
    return _embryo_frame("c_elegans_4_cell_without_eggshell_frame", "C. elegans 4-cell, without eggshell")


def c_elegans_rnai_frame() -> list[tuple[Any, dict, str]]:
    """A 4-cell C. elegans embryo after hmr-1; hmp-2 RNAi (Developmental Cell 2026 data, CC BY-SA 4.0)."""
    return _embryo_frame("c_elegans_rnai_frame", "C. elegans 4-cell, hmr-1; hmp-2 RNAi")
