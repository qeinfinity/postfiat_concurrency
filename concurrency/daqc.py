# concurrency/daqc.py

import hashlib

def compute_daqc(transactions):
    """
    A stub for an erasure-coded RBC. We'll just hash them all for demonstration.
    Real RBC would split them into coded shards & gather partial signatures.
    """
    m = hashlib.sha256()
    for tx in transactions:
        m.update(str(tx).encode('utf-8'))
    # This hash is the 'batch cert' in simplified form
    return m.digest()
