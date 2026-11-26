"""The plugin imports only public names of foambryo and delaunay-watershed (dw3d, dw2d).

A private module or name (one whose name starts with an underscore) may change or vanish in any release of the
library without notice, and the plugin would break with nothing to tell. Every import of the plugin's source, at
module level or inside a function, is read from its syntax tree; the test fails on a private module
(`foambryo._planar_drawing`), a private name (`from foambryo.io import _helper`) or an attribute of a library module
read by a private name (`foambryo._two_dimensional`).
"""

import ast
from pathlib import Path

import napari_foambryo

LIBRARIES = ("foambryo", "dw3d", "dw2d", "delaunay_watershed")
SOURCE = Path(napari_foambryo.__file__).parent


def _private(name: str) -> bool:
    return any(part.startswith("_") and not part.startswith("__") for part in name.split("."))


def _private_uses(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    aliases = set()
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in LIBRARIES:
            if _private(node.module):
                found.append(f"{path.name}:{node.lineno} from {node.module}")
            for alias in node.names:
                if _private(alias.name):
                    found.append(f"{path.name}:{node.lineno} {node.module}.{alias.name}")
                aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in LIBRARIES:
                    if _private(alias.name):
                        found.append(f"{path.name}:{node.lineno} import {alias.name}")
                    aliases.add(alias.asname or alias.name.split(".")[0])
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases
                and _private(node.attr)):
            found.append(f"{path.name}:{node.lineno} {node.value.id}.{node.attr}")
    return found


def test_the_source_is_where_the_test_looks():
    names = {path.name for path in SOURCE.glob("*.py")}
    assert {"_display.py", "_widgets.py", "_runs.py"} <= names


def test_no_private_module_or_name_of_the_libraries_is_imported():
    found = [use for path in sorted(SOURCE.glob("*.py")) for use in _private_uses(path)]
    assert found == []


def test_the_check_sees_a_private_import(tmp_path):
    sample = tmp_path / "sample.py"
    sample.write_text(
        "import foambryo\n"
        "def f():\n"
        "    from foambryo._planar_drawing import planar_scene\n"
        "    from foambryo.io import _hidden\n"
        "    return foambryo._two_dimensional\n",
        encoding="utf-8",
    )
    assert len(_private_uses(sample)) == 3
