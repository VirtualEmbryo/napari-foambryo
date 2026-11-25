# Changelog

User-facing changes only.

## Unreleased (planned for 0.2.0)

### Two-dimensional tissues

- **2-D segmentations go through the same docks.** A 2-D Labels layer (or one plane, `(1, Y, X)`) is meshed by delaunay-watershed-2d (Reconstruct: the pixel size `(y, x)`, square pixels only, from the layer, another layer or typed; `min_distance` in square pixels, default 4, the library's), inferred in 2D (Infer: Young-Dupré tensions with the 2-D angle readings, each junction-graph component gauged alone, and Laplace pressures, the methods offered in 2D; no seed ensemble) and drawn over the labels as 2-D layers: `<labels> interfaces` (the mesh, dark grey), `<labels> tensions` (each interface a ribbon one pixel wide in its tension's colour, an undetermined one green) and `<labels> pressures` (each cell a filled polygon in its pressure's colour), with `<labels> image border` (grey) for the segments that close a cell the image cuts. The colours and colour bars are foambryo's (the pressure scale runs over the cells). Results lists the interfaces and cells (the cells on the image border flagged); View explodes the cells (each moved away from the tissue's centre by its area centroid; there is no cut in 2D); Export writes the `foambryo` command's files from a 2-D run, `run.json` recording `dimension = 2`, and the command lines that rebuild them.
- **The reader and the writer take 2-D `.rec` files**: a 2-D file (as `foambryo mesh` writes it from a 2-D mask) opens as its interfaces and image border, and Infer runs on it as `foambryo infer` does. A 2-D file written before delaunay-watershed 0.8.0, whose edges are stored the other way round, opens as the same layers and gives the same numbers (foambryo measures a 2-D mesh's orientation and reverses it).
- **2-D samples**, beside the 3-D ones: a 2-D foam of 8 cells at mechanical equilibrium with its true tensions and pressures (the 2-D counterpart of benchmark case 000), and three frames of 4-cell *C. elegans* embryos (inside the eggshell, without eggshell, after hmr-1; hmp-2 RNAi), each its membrane image and its four cells, from the data of Yamamoto et al., Developmental Cell 61(6), 1273–1288.e4 (2026), doi:10.1016/j.devcel.2026.04.013, under CC BY-SA 4.0 (`sample_data/README.md`).

### Changed

- **Pad thin medium margins, on the Reconstruct dock**: delaunay-watershed's default (on for cubic voxels and square pixels, off for a mask resampled to cubic voxels), on, or off, as `foambryo mesh --pad-thin-medium-margins` / `--no-pad-thin-medium-margins`. With the default the reconstruction is the library's own default call, as before; a choice of on or off is recorded in `run.json` (`reconstruction.pad_thin_medium_margins`) and in the equivalent `foambryo mesh` command.
- **Selecting an interface or a cell no longer raises napari's `DeprecationWarning` on `viewer.camera`**: the camera is centred through `viewer.scene.camera`, which napari 0.9.0, the minimum, already has (napari deprecated `viewer.camera` in 0.9.0; measured: both 0.9.0 and 0.10.0 warn on it, neither on `viewer.scene.camera`, which is the same camera).
- **Angle reading in Infer › Advanced, for one mesh too**: the library's default for the mesh's dimension (chord in 3D, arc in 2D), or another reading; a reading other than the default is recorded in `run.json` and in the equivalent `foambryo infer --angle-reading` command.
- **Declared minimum versions, the ones the CI's floor jobs test**: scipy 1.14.0 (napari 0.9.0 requires it), magicgui 0.7.0, qtpy 2.4.0, superqt 0.7.8 and psutil 5.9.4, besides napari 0.9, numpy 2.0.0 and matplotlib 3.8.4. The four had no lower bound; theirs are napari 0.9.0's own, the oldest releases that can be installed with it, and the test suite passes with all of them (Python 3.12 and 3.13).
- **Requires delaunay-watershed 0.8.0 and foambryo 0.8.0** (`delaunay-watershed>=0.8.0rc1`, `foambryo[cli]>=0.8.0rc1`) and Python 3.12 or later. Their defaults that depend on the dimension (`min_distance`, the pressure method) are resolved for the mask or mesh in hand: 3 voxels and variational in 3D, as before.

Development of this release was supported by Anthropic's AI for Science program; parts of the code were written with Claude and reviewed by the developers.

## 0.1.0 — 2026-10-17

The first release of napari-foambryo, a napari plugin over delaunay-watershed-3d 0.7.0 and foambryo 0.7.0, released with them.

- **Five docks**, under *Plugins › foambryo*: **Reconstruct** (a Labels layer and its voxel size become a multimaterial mesh, by the reconstruction `foambryo mesh` runs, with a report of the mask and an estimate of the time and memory before the run), **Infer** (tensions, then pressures, as `foambryo infer`; or a seed ensemble, as `foambryo infer-over-seeds`), **Results** (the tensions and pressures on the mesh, in foambryo's colours, with their colour bars and tables; selecting a row shows its interface or cell), **View** (explode, cut, background) and **Export** (the files of the `foambryo` command, with the command lines that rebuild them).
- **One code path**: every number shown or written is one a public function of foambryo returns for the same mask and options; the tests check this bit for bit, and that the exported files are byte for byte the command's.
- **Runs in a separate process**: napari stays responsive, and Cancel stops a reconstruction, an inference or a seed ensemble at once and frees its memory. When the estimate exceeds the machine's memory, Reconstruct asks for *run anyway*.
- **Masks from other plugins**: the voxel size can be taken from another layer, the medium's label can be another value than 0, and results are marked out of date when the labels change.
- **Cropped tissues and anisotropic voxels**, as in foambryo 0.7.0: crop faces drawn as glass, cut cells' pressures `nan`; voxels longer along one axis resampled to cubic voxels before meshing.
- A reader and a writer for `.rec` meshes, and sample data: benchmark case 000 (6 cells, with its true tensions) and three small generated foams.
- Requires Python 3.11 or later, napari 0.9 or later, delaunay-watershed-3d 0.7.0 and foambryo 0.7.0 or later.
- **Dependencies**: the minimum versions are the oldest with which the test suite passes: napari 0.9 (0.8 lacks a call the plugin makes), numpy 2.0.0 and matplotlib 3.8.4.

Recent work on dw3d and foambryo is part of a collaboration with Alejandro Aguilera Castrejon (Janelia Research Campus, Howard Hughes Medical Institute). We thank him and his Janelia colleagues Adam L. Taylor, Wenhong Li and Francesco Roncato. Adam L. Taylor found the border-triangle winding defect fixed in 0.6.0 and pointed us to the seed-extraction and dense tension-solve bottlenecks on large tissues.
