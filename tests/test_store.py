from app.db import Store


def test_user_credits_style_and_payment(tmp_path):
    store = Store(str(tmp_path / "db.sqlite3"))
    store.ensure_user(1, "user")

    assert store.selected_style(1) == "flowers"
    store.set_style(1, "dubai")
    assert store.selected_style(1) == "dubai"

    assert store.can_generate(1, free_generations=1)
    assert store.charge_generation(1, free_generations=1) == "free"
    assert not store.can_generate(1, free_generations=1)

    store.grant(1, 2)
    assert store.charge_generation(1, free_generations=1) == "credit"

    store.save_payment(1, "charge", "plan:one:1", 9900, "RUB", 1)
    assert store.stats()["payments"] == 1
