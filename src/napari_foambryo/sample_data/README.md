# napari-foambryo's sample data

Each file opens from napari's File › Open Sample › foambryo menu.

## Three-dimensional

| file | what it is | licence |
|---|---|---|
| `benchmark_case_000.npz` | case 000 of the benchmark of Ichbiah et al., Nature Methods 20(12), 1989–1999 (2023), doi:10.1038/s41592-023-02084-7: a simulated aggregate of 6 cells at mechanical equilibrium, its segmentation mask (194 × 200 × 199 voxels) and its true tensions and pressures; voxel units | GPL-3.0-or-later, as the package |

The generated 3-D foams are computed when opened (12 Voronoi cells in a ball, a fixed seed); they are not at equilibrium.

## Two-dimensional

| file | what it is | licence |
|---|---|---|
| `two_dimensional_foam.npz` | an 8-cell circular-arc foam at mechanical equilibrium, from the generator of foambryo's 2-D benchmark at the fixed seed 20261113: junctions and arcs solved so that force balance at every junction and Laplace's law on every interface hold to 1e-9 (in the generator's units), the cells rasterised exactly at pixel centres with a mean cell radius of 20 px (144 × 141 pixels); its true tensions (one per interface) and pressures (per pixel, the medium at 0); pixel units | GPL-3.0-or-later, as the package |
| `c_elegans_4_cell_with_eggshell_frame.npz` | a non-perturbed 4-cell *C. elegans* embryo inside its eggshell (embryo 190429-2 of the data below): one frame of the membrane channel (uint16, 236 × 154 pixels) and the four cells segmented with Cellpose-SAM | CC BY-SA 4.0 |
| `c_elegans_4_cell_without_eggshell_frame.npz` | a 4-cell embryo whose eggshell was removed (embryo 190430-9): one frame (192 × 235 pixels) and its four cells | CC BY-SA 4.0 |
| `c_elegans_rnai_frame.npz` | a 4-cell embryo after hmr-1; hmp-2 RNAi (embryo 190626_210, strain LP162, NMY-2::GFP): one frame (200 × 298 pixels) and its four cells | CC BY-SA 4.0 |

Each embryo file holds `image`, `mask` (0 the medium, 1 to 4 the cells), `spacing` (the pixel size, 1 / 4.0702 µm: 4.0702 pixels per µm), `spacing_unit`, `source` (the movie, the layer and the crop it was taken from), `licence` and `citation`. The two wild-type frames are the layers of normalised time closest to 0.5 in the paper's 4-cell window; the cells are numbered in the order of the data's own map (1 EMS, 2 ABa or ABL, 3 ABp or ABR, 4 P2).

The three embryo frames are derived from the data of, and when you use them please cite:

Yamamoto K., Ichbiah S., Perez M., Borrego-Pinto J., Delbary F., Goehring N. W., Northrop P., Turlier H., Charras G. Spatiotemporal mapping of the contractile and adhesive forces sculpting early *C. elegans* embryos. *Developmental Cell* 61(6), 1273–1288.e4 (2026). doi:10.1016/j.devcel.2026.04.013.

The data are distributed under the Creative Commons Attribution-ShareAlike 4.0 International licence (CC BY-SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/); the deposit is Zenodo doi:10.5281/zenodo.19627642. The frames were cropped and their segmentations relabelled; the image values are unchanged.
