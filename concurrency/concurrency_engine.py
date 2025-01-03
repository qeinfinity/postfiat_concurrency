# concurrency/concurrency_engine.py

import threading
from typing import List

class ConcurrencyEngine:
    """
    A simplistic approach to 'Sealevel-like' concurrency. We run transactions in parallel 
    if their write sets do not overlap. If there's overlap, we lock sequentially.
    """

    def __init__(self, account_state):
        self.account_state = account_state

    def execute_block_of_transactions(self, tx_list: List, use_multithreading=True):
        """
        We can chunk the tx_list by non-overlapping sets or attempt to run them in parallel threads.
        In practice, a schedule step is needed, but we'll show a naive approach.
        """
        results = {}
        # Naive approach: if use_multithreading, spawn threads for non-conflicting sets
        # We'll show an example of lock-based parallel

        # 1. Group transactions that do not conflict
        #    For demonstration, we'll just try to run them all in parallel 
        #    and lock as needed inside each transaction.
        threads = []
        for tx in tx_list:
            t = threading.Thread(
                target=self._run_single_tx, args=(tx, results)
            )
            t.start()
            threads.append(t)

        for thread in threads:
            thread.join()

        return results

    def _run_single_tx(self, tx, results):
        # Acquire write locks for each key in the transaction
        # Then read from state, call tx.action_fn, then write results.
        # Actually, for read-keys, we might not lock or might do a read lock. 
        # We'll do a simplistic approach with a single write lock per key.

        # Sort keys to avoid deadlocks in real code. For demonstration, no sorting.
        for wkey in tx.write_keys:
            self.account_state.ensure_lock_exists(wkey)

        # Acquire all locks
        locked_list = []
        try:
            for wkey in sorted(tx.write_keys):
                lock = self.account_state.locks[wkey]
                lock.acquire()
                locked_list.append(lock)

            # READ
            read_values = {}
            for rkey in tx.read_keys:
                read_values[rkey] = self.account_state.read(rkey)

            # ACTION
            updates = tx.action_fn(read_values)

            # WRITE
            for k, v in updates.items():
                self.account_state.write(k, v)

            results[tx.tx_id] = (True, updates)
        except Exception as e:
            results[tx.tx_id] = (False, str(e))
        finally:
            # release locks
            for lk in reversed(locked_list):
                lk.release()
