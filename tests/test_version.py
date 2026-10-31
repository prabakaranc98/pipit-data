from importlib.metadata import version

import pipit


def test_package_and_distribution_versions_agree() -> None:
    assert pipit.__version__ == version("pipit-data")
