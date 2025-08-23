from board.combat import resolve_attack, success_probability


def fixed_rng_success():
    return 0.1


def fixed_rng_fail():
    return 0.9


def test_success_probability_basic():
    # A > D should give prob > 0.5
    p = success_probability(6, 3)
    assert p > 0.5


def test_resolve_attack_success():
    res = resolve_attack(8, 4, 8, rng=fixed_rng_success)
    assert res["ammo_used"] == 8
    assert res["participating"] == 8
    assert res["success"] is True
    assert res["damage"] >= 1


def test_resolve_attack_fail_and_losses():
    res = resolve_attack(4, 10, 4, rng=fixed_rng_fail)
    assert res["success"] is False
    assert res["attacker_loss"] == int(4 * 0.1)


def test_no_ammo():
    res = resolve_attack(5, 3, 0)
    assert res["participating"] == 0
    assert res["ammo_used"] == 0
