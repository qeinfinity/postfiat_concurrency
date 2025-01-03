# concurrency/batch_proposer.py

import time
import random
from concurrency.transaction import Transaction

class BatchProposer:
    """
    Each BatchProposer has a primary bucket (trans) and a secondary bucket (backups).
    In practice, you'd determine which transactions you 'own' (primary) by hashing the Tx ID or so.
    """

    def __init__(self, proposer_id):
        self.proposer_id = proposer_id
        self.primary_bucket = []
        self.secondary_bucket = []

    def add_to_primary(self, tx: Transaction):
        self.primary_bucket.append(tx)

    def add_to_secondary(self, tx: Transaction):
        self.secondary_bucket.append(tx)

    def form_batch(self, fallback=False):
        """
        If fallback==False, use primary bucket, else use secondary's timed-out or unfinalized txs
        """
        if fallback:
            chosen = list(self.secondary_bucket)
            self.secondary_bucket.clear()
        else:
            chosen = list(self.primary_bucket)
            self.primary_bucket.clear()

        # In a real system, you'd also remove duplicates or check if they've already been included
        return chosen
