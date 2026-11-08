import secrets


class Flash:
    """Non-volatile memory: survives power loss, but every write wears it out."""

    def __init__(self):
        self.value = None
        self.writes = 0

    def read(self):
        return self.value

    def write(self, value):
        self.value = value
        self.writes += 1


class RamCounter:
    """Baseline (vulnerable): counter only in RAM, restarts at 0 after reboot."""
    name = "RAM counter"

    def __init__(self):
        self.flash = Flash()
        self.counter = 0

    def next_counter(self):
        c = self.counter
        self.counter += 1
        return c

    def power_loss(self):
        self.counter = 0


class FlashPerMessage:
    """Save counter+1 to flash BEFORE using the counter. Safe, but 1 write per message."""
    name = "Flash write per message"

    def __init__(self):
        self.flash = Flash()
        self.counter = 0

    def next_counter(self):
        c = self.counter
        self.flash.write(c + 1)        # write-ahead: saved before the nonce is used
        self.counter = c + 1
        return c

    def power_loss(self):
        self.counter = self.flash.read() or 0


class ReserveAhead:
    """Save an upper bound (counter + B) once per B messages.

    After a reboot the logger continues from the saved bound, so no value can
    repeat; the unused rest of the block is skipped (lost).
    """

    def __init__(self, block):
        self.block = block
        self.name = f"Reserve-ahead (B={block})"
        self.flash = Flash()
        self.skipped = 0
        self._boot()

    def _boot(self):
        start = self.flash.read() or 0
        self.counter = start
        self.limit = start + self.block
        self.flash.write(self.limit)   # reserve the block before using any value of it

    def next_counter(self):
        if self.counter >= self.limit:
            self.limit += self.block
            self.flash.write(self.limit)
        c = self.counter
        self.counter += 1
        return c

    def power_loss(self):
        self.skipped += self.limit - self.counter   # unused values of the block are lost
        self._boot()


class RandomNonce:
    """Fresh random 96-bit value from the CSPRNG for every message; nothing to remember."""
    name = "Random 96-bit nonce"

    def __init__(self):
        self.flash = Flash()

    def next_counter(self):
        return secrets.randbits(96)

    def power_loss(self):
        pass