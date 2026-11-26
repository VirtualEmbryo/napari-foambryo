"""Tiers T1 and T3: a 2-D segmentation through the docks, the 2-D layers, the reader, Export and the 2-D samples.

What this pins, and why:

* **the numbers are the library's**: a 2-D Labels layer reconstructed and inferred in the docks gives bitwise
  `infer_forces(reconstruct_mask(mask, spacing).mesh())`; the angle reading chosen in Infer › Advanced gives the
  library's numbers for that reading and is recorded;
* **the 2-D layers**: interfaces as ribbons one pixel wide (one quad per segment), coloured by `foambryo.colour_scales`
  (an undetermined tension green), cells as filled polygons whose triangles cover each cell exactly, coloured by
  pressure on the one scale over the cells; the image-border segments of a cut cell have their own layer;
* **Export** writes the `foambryo` command's files from a 2-D run (`mesh.rec` and the tables byte for byte the
  command's, `run.json` with `dimension = 2`);
* **the reader** opens a 2-D `.rec` file, and Infer on it is `foambryo infer` on the file;
* **View**: explode moves each cell by its area centroid's offset; there is no cut in 2D;
* **the samples**: the 2-D foam ships its true tensions and pressures; the three embryo frames ship an image, four
  cells, the pixel size 1 / 4.0702 µm, their licence (CC BY-SA 4.0) and their citation.
"""

from __future__ import annotations

import json
import os
import shlex
import warnings

import numpy as np
import pytest
from foambryo import cli, colour_scales, dcel_mesh_from_file, infer_forces, reconstruct_mask
from foambryo import results as tables

from napari_foambryo._display import planar_cell_copy, planar_interface_copy, planar_scene_of
from napari_foambryo._io import get_reader
from napari_foambryo._layers import RUNS
from napari_foambryo._runner import run_in_child
from napari_foambryo._runs import InferenceOptions, Run, SourceMask, export_run, infer_on_mesh
from napari_foambryo._sample_data import (
    DEVELOPMENTAL_CELL_2026,
    c_elegans_4_cell_with_eggshell,
    c_elegans_4_cell_without_eggshell,
    c_elegans_rnai_frame,
    two_dimensional_foam,
    two_dimensional_true_values,
)
from napari_foambryo._widgets import ExportWidget, InferWidget, ReconstructWidget, ResultsWidget, ViewWidget
from tests.conftest import same_floats, sha

TIMEOUT_MS = 180_000


def _quiet(function, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return function(*args, **kwargs)


def _foam() -> tuple[np.ndarray, tuple[float, float]]:
    ((mask, meta, _),) = two_dimensional_foam()
    return mask, tuple(meta["scale"])


def _cut_foam() -> np.ndarray:
    mask, _ = _foam()
    return np.ascontiguousarray(mask[:, 50:])


# ------------------------------------------------------------------------------------------------
# T1: the 2-D display copies and the samples
# ------------------------------------------------------------------------------------------------
def test_cells_are_exact_polygons_and_interfaces_one_quad_per_segment():
    mask, spacing = _foam()
    mesh = _quiet(reconstruct_mask, mask, spacing).mesh()
    scene = planar_scene_of(mesh)
    cells = planar_cell_copy(mesh, scene)
    corners = cells.vertices[cells.faces]
    u, v = corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0]
    areas = 0.5 * np.abs(u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0])
    for cell in scene.cells:
        assert areas[cells.face_group == cell].sum() == pytest.approx(scene.areas[cell], rel=1e-12)
        assert scene.areas[cell] == pytest.approx(np.count_nonzero(mask == cell), rel=0.05)
    interfaces, keys = planar_interface_copy(mesh, scene)
    interior = np.flatnonzero(~scene.border)
    assert len(interfaces.vertices) == 4 * len(interior)
    assert np.array_equal(interfaces.vertex_group[::4], scene.segment_pair[interior])
    assert keys == [tuple(p) for p in scene.pairs]
    exploded, _ = planar_interface_copy(mesh, scene, exploded=True)
    assert set(np.unique(exploded.vertex_cell)) == set(scene.cells)


def test_the_two_dimensional_samples():
    ((mask, meta, kind),) = two_dimensional_foam()
    assert kind == "labels"
    assert mask.shape == (144, 141)
    assert sorted(np.unique(mask).tolist()) == list(range(9))
    tensions, pressures = two_dimensional_true_values()
    assert len(tensions) == 21
    assert len(pressures) == 9
    assert pressures[0] == 0.0
    assert meta["metadata"]["foambryo"]["spacing_unit"] == "pixel"
    for sample in (c_elegans_4_cell_with_eggshell, c_elegans_4_cell_without_eggshell, c_elegans_rnai_frame):
        (image, image_meta, image_kind), (labels, labels_meta, labels_kind) = sample()
        assert (image_kind, labels_kind) == ("image", "labels")
        assert image.shape == labels.shape
        assert image.dtype == np.uint16
        assert sorted(np.unique(labels).tolist()) == [0, 1, 2, 3, 4]
        assert labels_meta["scale"] == pytest.approx((1 / 4.0702, 1 / 4.0702))
        info = labels_meta["metadata"]["foambryo"]
        assert info["licence"] == "CC BY-SA 4.0"
        assert info["citation"] == DEVELOPMENTAL_CELL_2026
        assert "doi:10.1016/j.devcel.2026.04.013" in info["citation"]
        assert image_meta["metadata"]["foambryo"]["licence"] == "CC BY-SA 4.0"
    from importlib.resources import files

    readme = files("napari_foambryo").joinpath("sample_data/README.md").read_text()
    assert "CC BY-SA 4.0" in readme
    assert "doi:10.1016/j.devcel.2026.04.013" in readme


def _run_for(mask, spacing, options: InferenceOptions) -> Run:
    child = run_in_child(
        "foambryo.io:reconstruct_mask", {"segmentation_mask": mask, "spacing": spacing, "spacing_unit": "um"}
    )
    reconstruction = child.value
    source = SourceMask("sample", tuple(mask.shape), str(mask.dtype), "", spacing, "um", "this layer")
    run = Run("run-2d", reconstruction.mesh(), source=source, mask=mask, reconstruction=reconstruction,
              rec_bytes=reconstruction.rec_bytes)
    run.options = options
    run.outcome, run.infer_warnings, run.infer_seconds = infer_on_mesh(run.mesh, options)
    run.infer_date = "2026-11-13T00:00:00+00:00"
    return run


@pytest.mark.parametrize("reading", [None, "chord"])
def test_a_2d_export_is_what_the_command_writes(tmp_path, capsys, reading):
    mask, _ = _foam()
    options = InferenceOptions("young-dupre", "laplace", 1.0, 0.0, "auto", "none", angle_reading=reading)
    run = _run_for(mask, (0.5, 0.5), options)
    exported = tmp_path / "exported"
    written = export_run(run, exported, include_mask=True)
    assert set(written) == {"mesh.rec", "tensions.csv", "pressures.csv", "colour_bars.png", "mask.npz", "run.json"}
    record = json.loads((exported / "run.json").read_text())
    assert record["dimension"] == 2
    commands = record["equivalent_commands"]
    assert "--spacing 0.5 0.5" in commands[0]
    assert ("--angle-reading chord" in commands[1]) == (reading == "chord")
    folder = tmp_path / "command"
    folder.mkdir()
    (folder / "mask.npz").write_bytes((exported / "mask.npz").read_bytes())
    cwd = os.getcwd()
    try:
        os.chdir(folder)
        for line in commands:
            assert cli.main(shlex.split(line)[1:]) == cli.EXIT_OK
    finally:
        os.chdir(cwd)
    capsys.readouterr()
    assert (folder / "mesh.rec").read_bytes() == (exported / "mesh.rec").read_bytes()
    for table in ("tensions.csv", "pressures.csv"):
        assert (folder / table).read_bytes() == (exported / table).read_bytes(), table
    command_record = json.loads((folder / "run.json").read_text())
    for key in ("schema", "dimension", "options", "library_call", "mesh", "results", "units", "status"):
        assert record[key] == command_record[key], key


def test_the_reader_opens_a_2d_file_and_infer_on_it_is_the_command(tmp_path):
    mask = _cut_foam()
    reconstruction = _quiet(reconstruct_mask, mask, (1.0, 1.0))
    path = tmp_path / "foam2d.rec"
    reconstruction.write_rec(path)
    layers = get_reader(str(path))(str(path))
    assert [meta["name"] for _, meta, _ in layers] == ["foam2d interfaces", "foam2d image border"]
    assert all(data[0].shape[1] == 2 for data, _, _ in layers)
    run = RUNS[layers[0][1]["metadata"]["foambryo"]["run_id"]]
    from_file = _quiet(dcel_mesh_from_file, path)
    assert sha(run.mesh.points) == sha(from_file.points)
    ours = _quiet(infer_on_mesh, run.mesh, InferenceOptions("young-dupre", "laplace", 1.0, 0.0, "auto", "none"))[0]
    theirs = _quiet(infer_forces, from_file)
    assert same_floats(ours.tensions, theirs[0])
    assert same_floats(ours.pressures, theirs[1])


def test_a_2d_file_in_the_former_orientation_opens_as_the_same_layers_and_numbers(tmp_path):
    """A 2-D `.rec` written before delaunay-watershed 0.8.0 (every edge stored the other way round, no `orientation`
    in its appendix): foambryo measures and reverses it, so the reader's layers and Infer's numbers are the same."""
    from dw2d.io import load_rec, save_rec

    mask = _cut_foam()
    reconstruction = _quiet(reconstruct_mask, mask, (1.0, 1.0))
    one_rule = tmp_path / "one_rule.rec"
    reconstruction.write_rec(one_rule)
    points, segments, labels = load_rec(one_rule)
    former = tmp_path / "former.rec"
    border = tuple(int(v) for v in reconstruction.image_border_vertices)
    save_rec(former, points, segments[:, ::-1], labels,
             metadata={"dimension": 2, "axis_order": "yx", "image_border_vertices": border})
    opened = [get_reader(str(p))(str(p)) for p in (one_rule, former)]
    for (data_a, meta_a, kind_a), (data_b, meta_b, kind_b) in zip(*opened, strict=True):
        assert kind_a == kind_b and meta_a["name"].split(" ", 1)[1] == meta_b["name"].split(" ", 1)[1]
        assert all(sha(a) == sha(b) for a, b in zip(data_a, data_b, strict=True))
    runs = [RUNS[layers[0][1]["metadata"]["foambryo"]["run_id"]] for layers in opened]
    assert sha(runs[0].mesh.segments) == sha(runs[1].mesh.segments)
    options = InferenceOptions("young-dupre", "laplace", 1.0, 0.0, "auto", "none")
    first, second = (_quiet(infer_on_mesh, run.mesh, options)[0] for run in runs)
    assert same_floats(first.tensions, second.tensions)
    assert same_floats(first.pressures, second.pressures)


# ------------------------------------------------------------------------------------------------
# T3: the docks on a ViewerModel
# ------------------------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _wait_for_background_workers(qtbot):
    yield
    from napari_foambryo._widgets import _LIVE_WORKERS

    qtbot.waitUntil(lambda: not _LIVE_WORKERS, timeout=TIMEOUT_MS)


@pytest.fixture
def viewer():
    from napari.components import ViewerModel

    return ViewerModel()


@pytest.fixture
def docks(qtbot, viewer):
    from napari.utils._proxies import PublicOnlyProxy

    widgets = tuple(cls(PublicOnlyProxy(viewer)) for cls in (ReconstructWidget, InferWidget, ResultsWidget,
                                                              ExportWidget, ViewWidget))
    for widget in widgets:
        qtbot.addWidget(widget)
    return widgets


def _reconstruct_and_infer(qtbot, docks, layer_name, reading=None):
    reconstruct, infer = docks[0], docks[1]
    reconstruct.select_layer(layer_name)
    assert reconstruct.run_button.isEnabled(), reconstruct.spacing_label.text()
    reconstruct.start()
    qtbot.waitUntil(lambda: reconstruct._worker is None, timeout=TIMEOUT_MS)
    assert reconstruct.last_error is None, reconstruct.status.text()
    if reading is not None:
        infer.one_mesh_reading_box.setCurrentIndex(infer.one_mesh_reading_box.findData(reading))
    infer.start()
    qtbot.waitUntil(lambda: infer._worker is None, timeout=TIMEOUT_MS)
    assert infer.status.text().startswith("complete"), infer.status.text()


def test_the_2d_foam_through_the_docks_gives_the_library_s_numbers_and_colours(qtbot, viewer, docks):
    reconstruct, infer, results, _, view = docks
    ((data, kwargs, _),) = two_dimensional_foam()
    layer = viewer.add_labels(data, **kwargs)
    reconstruct.select_layer(layer.name)
    assert reconstruct.min_distance.value() == 4
    assert reconstruct.min_distance_label.text() == "min_distance (square pixels)"
    assert not reconstruct.spacing_boxes[0].isVisibleTo(reconstruct)
    _reconstruct_and_infer(qtbot, docks, layer.name)
    assert infer.pressure_box.currentText() == "laplace"
    assert not infer.mode_box.model().item(1).isEnabled()  # no seed ensemble in 2D
    run = RUNS[infer.mesh_box.currentData()]
    library = _quiet(reconstruct_mask, data, (1.0, 1.0))
    assert sha(run.mesh.points) == sha(library.mesh().points)
    tensions, pressures = _quiet(infer_forces, library.mesh())
    assert same_floats(run.outcome.tensions, tensions)
    assert same_floats(run.outcome.pressures, pressures)

    tension_layer = viewer.layers["2-D foam tensions"]
    pressure_layer = viewer.layers["2-D foam pressures"]
    assert tension_layer.ndim == 2
    assert tension_layer.visible
    assert not pressure_layer.visible
    info = tension_layer.metadata["foambryo"]
    keys = info["interfaces"]
    values = np.array([tensions[keys[g]] for g in info["vertex_group"]])
    ranges = colour_scales.colour_bar_ranges(run.mesh, tensions, pressures)
    expected = colour_scales.tension_colours(colour_scales.tension_colour_fractions(values, ranges.tension))
    assert np.allclose(tension_layer.vertex_colors[:, :3], expected, atol=1e-6)
    cells = pressure_layer.metadata["foambryo"]["vertex_group"]
    values = np.array([pressures[int(c)] for c in cells])
    expected = colour_scales.pressure_colours(colour_scales.pressure_colour_fractions(values, ranges.pressure[1]))
    assert np.allclose(pressure_layer.vertex_colors[:, :3], expected, atol=1e-6)
    assert "True tensions known" in results.summary.text()

    view._run_changed()
    assert not view.cut_box.isEnabled()
    before = pressure_layer.data[0].copy()
    view.set_explode(0.4)
    after = pressure_layer.data[0]
    moved = after - before
    scene = planar_scene_of(run.mesh)
    for cell in scene.cells:
        rows = np.asarray(pressure_layer.metadata["foambryo"]["vertex_cell"]) == cell
        assert np.allclose(moved[rows], 0.4 * (scene.centroids[cell] - scene.tissue_centroid))


def test_an_embryo_frame_in_micrometres_with_another_angle_reading(qtbot, viewer, docks, tmp_path):
    reconstruct, infer, _, export, _ = docks
    (image, image_kwargs, _), (labels, labels_kwargs, _) = c_elegans_rnai_frame()
    viewer.add_image(image, **image_kwargs)
    layer = viewer.add_labels(labels, **labels_kwargs)
    reconstruct.select_layer(layer.name)
    assert "the sample's metadata" in reconstruct.spacing_label.text()
    _reconstruct_and_infer(qtbot, docks, layer.name, reading="chord")
    run = RUNS[infer.mesh_box.currentData()]
    assert run.options.angle_reading == "chord"
    spacing = tuple(labels_kwargs["scale"])
    mesh = _quiet(reconstruct_mask, labels, spacing).mesh()
    tensions, pressures = _quiet(infer_forces, mesh, angle_reading="chord")
    assert same_floats(run.outcome.tensions, tensions)
    assert same_floats(run.outcome.pressures, pressures)
    export.folder.setText(str(tmp_path / "out"))
    written = export.export()
    assert "run.json" in written
    record = json.loads((tmp_path / "out" / tables.RUN_RECORD).read_text())
    assert record["options"]["angle_reading"] == "chord"
    assert record["dimension"] == 2
    assert record["units"]["pressure"] == "tension per um"
