"""Selecting an interface centres napari's camera through `viewer.scene.camera`, not the deprecated `viewer.camera`.

napari deprecated `viewer.camera` in 0.9.0 (napari-foambryo's minimum), where `viewer.scene.camera` is the same camera:
the plugin centres the camera without the `DeprecationWarning`, through the proxy the docks hold too.
"""

from __future__ import annotations

import warnings

import numpy as np


def test_highlight_centres_the_camera_without_the_deprecated_attribute():
    from napari.components import ViewerModel
    from napari.utils._proxies import PublicOnlyProxy

    from napari_foambryo._layers import highlight

    model = ViewerModel()
    model.dims.ndisplay = 3
    vertices = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [10.0, 10.0, 10.0]])
    layer = model.add_surface((vertices, np.array([[0, 1, 2], [1, 2, 3]])), scale=(1.0, 2.0, 0.5),
                              translate=(1.0, 0.0, -1.0))
    layer.metadata["foambryo"] = {"base_colours": np.ones((4, 4)), "vertex_group": np.array([7, 7, 7, 8])}
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        highlight(PublicOnlyProxy(model), layer, 7)
    expected = vertices[:3].mean(axis=0) * np.array([1.0, 2.0, 0.5]) + np.array([1.0, 0.0, -1.0])
    np.testing.assert_allclose(model.scene.camera.center, expected, rtol=0, atol=1e-12)
