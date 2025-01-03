# concurrency/transaction.py

from typing import Set, Callable, Dict

class Transaction:
    """
    Each transaction declares or infers read_keys and write_keys, plus an 'action' 
    function that modifies the state. 
    """
    def __init__(self, tx_id, read_keys: Set[str], write_keys: Set[str], action_fn: Callable):
        self.tx_id = tx_id
        self.read_keys = read_keys
        self.write_keys = write_keys
        self.action_fn = action_fn
        # Add an optional "fee" or "priority" field if you want local fee markets

    def __repr__(self):
        return f"Tx({self.tx_id}, R={self.read_keys}, W={self.write_keys})"
