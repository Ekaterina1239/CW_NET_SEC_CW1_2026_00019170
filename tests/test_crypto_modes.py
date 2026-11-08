import pytest
from cryptography.exceptions import InvalidTag
import crypto_modes as cm
from telemetry import make_reading, to_bytes

PLAIN = to_bytes(make_reading(1, 720))


def test_key_is_256_bits():
    assert len(cm.new_key()) == 32


def test_nonce_is_96_bits():
    assert len(cm.make_nonce(1, 0)) == 12


def test_gcm_roundtrip():
    key, nonce = cm.new_key(), cm.make_nonce(1, 0)
    assert cm.gcm_decrypt(key, nonce, cm.gcm_encrypt(key, nonce, PLAIN)) == PLAIN


def test_ctr_roundtrip():
    key, nonce = cm.new_key(), cm.make_nonce(1, 0)
    assert cm.ctr_decrypt(key, nonce, cm.ctr_encrypt(key, nonce, PLAIN)) == PLAIN


def test_cbc_roundtrip():
    key = cm.new_key()
    assert cm.cbc_decrypt(key, cm.cbc_encrypt(key, PLAIN)) == PLAIN


def test_cbc_uses_fresh_iv():
    key = cm.new_key()
    assert cm.cbc_encrypt(key, PLAIN)[:16] != cm.cbc_encrypt(key, PLAIN)[:16]


def test_gcm_rejects_tampering():
    key, nonce = cm.new_key(), cm.make_nonce(1, 0)
    data = bytearray(cm.gcm_encrypt(key, nonce, PLAIN))
    data[0] ^= 1
    with pytest.raises(InvalidTag):
        cm.gcm_decrypt(key, nonce, bytes(data))


def test_different_counters_give_different_nonces():
    nonces = {cm.make_nonce(1, i) for i in range(10000)}
    assert len(nonces) == 10000