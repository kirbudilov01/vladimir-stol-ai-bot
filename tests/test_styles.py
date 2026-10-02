from app.bot import resolve_style


def test_resolve_style_aliases():
    assert resolve_style("букет", 1) == "flowers"
    assert resolve_style("Дубай", 1) == "dubai"
    assert resolve_style("car", 1) == "car"
