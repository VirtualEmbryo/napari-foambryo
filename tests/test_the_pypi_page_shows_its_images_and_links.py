"""The README is the PyPI and napari-hub page: its images and links must work there.

PyPI renders the README without the repository beside it, so a relative image path shows a broken image and a
relative link leads nowhere. Every image and link of the README is therefore absolute, pinned to this version's tag
in the public repository, and the package metadata names that repository (napari hub shows the Project-URLs).
"""

import re
import tomllib

from packaging.version import Version  # pytest's own dependency

from tests.conftest import REPOSITORY

PUBLIC_REPOSITORY = "https://github.com/VirtualEmbryo/napari-foambryo"


def test_every_readme_image_and_link_is_absolute() -> None:
    readme = (REPOSITORY / "README.md").read_text(encoding="utf-8")
    targets = re.findall(r"\]\(([^)\s]+)", readme) + re.findall(r'src="([^"]+)"', readme)
    assert targets
    relative = [t for t in targets if not t.startswith(("https://", "http://", "#", "mailto:"))]
    assert not relative, relative


def test_the_readme_images_are_pinned_to_this_versions_tag() -> None:
    """A release's images point to its tag; a release candidate's to the tag of the release it precedes.

    A release candidate ships the release's README unchanged, so its images point to the release's tag; a development
    version is not checked.
    """
    version = Version(tomllib.loads((REPOSITORY / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"])
    readme = (REPOSITORY / "README.md").read_text(encoding="utf-8")
    images = re.findall(r"!\[[^\]]*\]\(([^)\s]+)", readme)
    assert images
    pinned = f"https://raw.githubusercontent.com/VirtualEmbryo/napari-foambryo/v{version.base_version}/"
    if not version.is_devrelease:
        for image in images:
            assert image.startswith(pinned), image


def test_the_metadata_names_the_public_repository() -> None:
    urls = tomllib.loads((REPOSITORY / "pyproject.toml").read_text(encoding="utf-8"))["project"]["urls"]
    assert urls["Source"] == PUBLIC_REPOSITORY
    assert urls["Issues"] == f"{PUBLIC_REPOSITORY}/issues"
