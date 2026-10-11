import importlib.resources

import shtemplate

PUBLIC_API: list[str] = ["ExpansionError", "expand"]


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(shtemplate.__all__) == sorted(PUBLIC_API)


def test_every_exported_name_resolves() -> None:
    for name in shtemplate.__all__:
        assert hasattr(shtemplate, name)


def test_version_is_a_three_part_string() -> None:
    parts = shtemplate.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("shtemplate").joinpath("py.typed").is_file()
