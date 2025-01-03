# consensus/poh.py

import time
import hashlib

class PoHGenerator:
    """
    A simple mock for Proof of History. In real usage, you'd have continuous hashing, 
    each 'tick' referencing the prior hash to produce a verifiable sequence of events.
    """

    def __init__(self):
        self.current_hash = b'GENESIS'
        self.ticks = 0

    def record_event(self, data: bytes):
        """
        Hash the current state plus new data to produce a new PoH tick.
        """
        to_hash = self.current_hash + data + self.ticks.to_bytes(8, 'big')
        new_hash = hashlib.sha256(to_hash).digest()
        self.current_hash = new_hash
        self.ticks += 1
        return new_hash

    def get_current_poh(self):
        """
        Returns the latest PoH reference.
        """
        return self.current_hash
