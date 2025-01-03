# concurrency/transaction.py
# concurrency/transaction.py

from typing import Set, Callable, Dict, Optional

class Transaction:
    """
    Each transaction can specify:
      - read_keys: accounts/keys that will be read
      - write_keys: accounts/keys that will be written
      - action_fn: a function that, given a dict of read_data, returns new {key: value} writes
      - memo: textual data used by the AI aggregator
      - fee: optional local fee structure
    """
    def __init__(
        self,
        tx_id: str,
        read_keys: Set[str],
        write_keys: Set[str],
        action_fn: Callable[[Dict], Dict],
        memo: Optional[str] = None,
        fee: float = 0.0
    ):
        self.tx_id = tx_id
        self.read_keys = read_keys
        self.write_keys = write_keys
        self.action_fn = action_fn
        self.memo = memo or ""
        self.fee = fee

    def __repr__(self):
        short_memo = self.memo[:30] + "..." if len(self.memo) > 30 else self.memo
        return (f"Tx({self.tx_id}, R={self.read_keys}, W={self.write_keys}, "
                f"fee={self.fee}, memo='{short_memo}')")
