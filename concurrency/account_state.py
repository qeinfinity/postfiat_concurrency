# concurrency/account_state.py

import threading

class AccountState:
    """
    A global ledger dictionary with a lock manager for concurrency.
    In a real design, you'd do more fine-grained locking on each account/object.
    """
    def __init__(self):
        self.state_store = {}
        self.locks = {}  # map key -> threading.Lock()

    def ensure_lock_exists(self, key: str):
        if key not in self.locks:
            self.locks[key] = threading.Lock()

    def read(self, key: str):
        return self.state_store.get(key, 0)

    def write(self, key: str, value):
        self.state_store[key] = value
