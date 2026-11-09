import crypto_modes as cm
from server import TelemetryServer, seal
from telemetry import make_reading, to_bytes

PLAIN = to_bytes(make_reading(1, 720))


def fresh_server(check=True):
    key = cm.new_key()
    server = TelemetryServer(key, "AES-GCM", check_counter=check)
    for c in range(3):
        assert server.receive(seal("AES-GCM", key, 1, c, PLAIN))[0]
    return key, server


def test_replay_rejected_with_counter_check():
    key, server = fresh_server()
    assert not server.receive(seal("AES-GCM", key, 1, 2, PLAIN))[0]


def test_replay_accepted_without_counter_check():
    key, server = fresh_server(check=False)
    assert server.receive(seal("AES-GCM", key, 1, 2, PLAIN))[0]


def test_counter_reset_raises_alert():
    key, server = fresh_server()
    accepted, reason = server.receive(seal("AES-GCM", key, 1, 0, PLAIN))
    assert not accepted and "ALERT" in reason


def test_forward_jump_accepted():
    key, server = fresh_server()
    assert server.receive(seal("AES-GCM", key, 1, 1000, PLAIN))[0]


def test_forged_header_rejected_by_gcm():
    key, server = fresh_server()
    pkt = seal("AES-GCM", key, 1, 2, PLAIN)
    assert not server.receive(cm.make_nonce(1, 99) + pkt[12:])[0]