import nonce_strategies as ns
from blackout_sim import b_min


def run(strategy, messages, outage_every):
    used, reuses = set(), 0
    for i in range(messages):
        if i and i % outage_every == 0:
            strategy.power_loss()
        v = strategy.next_counter()
        reuses += v in used
        used.add(v)
    return reuses


def test_ram_counter_repeats_after_outage():
    assert run(ns.RamCounter(), 1000, 100) > 0


def test_flash_per_message_never_repeats():
    s = ns.FlashPerMessage()
    assert run(s, 1000, 100) == 0
    assert s.flash.writes == 1000            # one write per message


def test_reserve_ahead_never_repeats_and_writes_less():
    s = ns.ReserveAhead(50)
    assert run(s, 1000, 77) == 0
    assert s.flash.writes < 1000 / 10


def test_random_nonce_never_repeats_in_practice():
    assert run(ns.RandomNonce(), 10000, 100) == 0


def test_b_rule():
    assert b_min(365) == 390                 # daily outages, 10,000 cycles, 20 years
    assert b_min(600) is None                # outages alone exceed the write budget