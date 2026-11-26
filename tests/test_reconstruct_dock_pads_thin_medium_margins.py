"""The Reconstruct dock's choice of delaunay-watershed's padding of thin medium margins.

The same choice as `foambryo mesh --pad-thin-medium-margins` / `--no-pad-thin-medium-margins`: by default the dock
makes the library's own default call (padded on cubic voxels, not when resampled); on or off is passed to
`foambryo.reconstruct_mask`, recorded in the run, and written in the equivalent command line. A 12-voxel cube 3 voxels
from every face of an 18-voxel image is padded by default, and its mesh changes when the padding is refused.
"""

from __future__ import annotations

import numpy as np
import pytest
from superqt import QCollapsible

from napari_foambryo._layers import RUNS
from napari_foambryo._widgets import PADDING_CHOICES
from tests.conftest import quietly
from tests.test_view_dock_diagnostics_and_export_dialog import docks, viewer  # noqa: F401
from tests.test_widgets_walk_through import _reconstruct


def _cube() -> np.ndarray:
    cube = np.zeros((18, 18, 18), dtype=np.int32)
    cube[3:15, 3:15, 3:15] = 1
    return cube


def test_the_choice_is_on_the_dock_and_defaults_to_the_librarys(docks):  # noqa: F811
    reconstruct = docks[0]
    assert [reconstruct.padding_box.itemData(i) for i in range(reconstruct.padding_box.count())] == [None, True, False]
    assert reconstruct.padding_box.currentData() is None
    assert [reconstruct.padding_box.itemText(i) for i in range(3)] == [text for text, _ in PADDING_CHOICES]
    assert not any(fold.isAncestorOf(reconstruct.padding_box) for fold in reconstruct.findChildren(QCollapsible))


@pytest.mark.parametrize("index", [0, 1, 2])
def test_the_choice_reaches_the_reconstruction_the_run_and_its_command(qtbot, viewer, docks, monkeypatch, index):  # noqa: F811
    import napari_foambryo._widgets as widgets
    from foambryo import reconstruct_mask

    sent: list[dict] = []
    real = widgets.run_in_child

    def recorded(target: str, kwargs: dict, *args: object, **options: object):
        sent.append(dict(kwargs))
        return real(target, kwargs, *args, **options)

    monkeypatch.setattr(widgets, "run_in_child", recorded)
    reconstruct = docks[0]
    viewer.add_labels(_cube(), name="cube")
    reconstruct.padding_box.setCurrentIndex(index)
    reconstruct.confirm_voxels.setChecked(True)  # voxel units: 1 x 1 x 1, cubic
    _reconstruct(qtbot, reconstruct, "cube")
    chosen = PADDING_CHOICES[index][1]
    if chosen is None:
        assert "pad_thin_medium_margins" not in sent[-1]  # the library's own default call
    else:
        assert sent[-1]["pad_thin_medium_margins"] is chosen
    run = RUNS[max(RUNS, key=lambda key: list(RUNS).index(key))]
    assert run.pad_thin_medium_margins is chosen
    command = run.equivalent_commands()[0]
    assert command.endswith({None: str(run.reconstruction.min_distance), True: " --pad-thin-medium-margins",
                             False: " --no-pad-thin-medium-margins"}[chosen])
    expected = quietly(reconstruct_mask, _cube(), (1.0, 1.0, 1.0), spacing_unit=sent[-1]["spacing_unit"],
                       pad_thin_medium_margins=chosen)
    assert run.reconstruction.points.tobytes() == expected.points.tobytes()
    unpadded = quietly(reconstruct_mask, _cube(), (1.0, 1.0, 1.0), pad_thin_medium_margins=False)
    assert (run.reconstruction.points.shape == unpadded.points.shape
            and run.reconstruction.points.tobytes() == unpadded.points.tobytes()) is (chosen is False)
