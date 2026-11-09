import struct

from cryptography.exceptions import InvalidTag

import crypto_modes as cm


def seal(mode, key, device_id, counter, plaintext):
    """Logger side: build a packet = header || encrypted body."""
    nonce = cm.make_nonce(device_id, counter)
    body = cm.gcm_encrypt(key, nonce, plaintext) if mode == "AES-GCM" else cm.ctr_encrypt(key, nonce, plaintext)
    return nonce + body


def preview(data):
    """Readable start of a plaintext, or a note that it is garbage."""
    try:
        text = data[:40].decode("utf-8")
        if text.isprintable():
            return text
    except UnicodeDecodeError:
        pass
    return "garbled data (no error raised)"


class TelemetryServer:
    def __init__(self, key, mode="AES-GCM", check_counter=True):
        self.key = key
        self.mode = mode
        self.check_counter = check_counter
        self.last_counter = {}        # device id -> highest counter accepted (must be persistent in a real server)
        self.log = []                 # (accepted?, reason)

    def receive(self, packet):
        header, body = packet[:12], packet[12:]
        device_id, counter = struct.unpack(">IQ", header)

        # 1) integrity: only AES-GCM can detect modification
        try:
            if self.mode == "AES-GCM":
                plaintext = cm.gcm_decrypt(self.key, header, body)
            else:
                plaintext = cm.ctr_decrypt(self.key, header, body)
        except InvalidTag:
            return self._result(False, "rejected: invalid tag (modified packet)")

        # 2) freshness: the counter must be strictly larger than any seen before
        last = self.last_counter.get(device_id)
        if self.check_counter and last is not None and counter <= last:
            if counter == last:
                return self._result(False, "rejected: replay (same counter seen before)")
            return self._result(False, "rejected + ALERT: counter went backwards (old packet injected, or logger reset -> nonce reuse)")

        self.last_counter[device_id] = counter if last is None else max(last, counter)
        return self._result(True, "accepted: " + preview(plaintext))

    def _result(self, accepted, reason):
        self.log.append((accepted, reason))
        return accepted, reason