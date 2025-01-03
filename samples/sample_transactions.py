# samples/sample_transactions.py

from typing import List
from concurrency.transaction import Transaction

def get_demo_transactions():
    """
    Returns a small set of example transactions with a variety of memos, read/write sets,
    and optional fees (if you want to test local fee markets).
    """
    def incA_action(read_data):
        old_val = read_data.get("A", 0)
        return {"A": old_val + 100}

    def incB_action(read_data):
        old_val = read_data.get("B", 0)
        return {"B": old_val + 5}

    def cross_action(read_data):
        # This might read from A and B, then set both
        a_val = read_data.get("A", 0)
        b_val = read_data.get("B", 0)
        return {"A": a_val + 10, "B": b_val + 10}

    txs = []

    txs.append(Transaction(
        tx_id="demo1",
        read_keys={"A"},
        write_keys={"A"},
        action_fn=incA_action,
        memo="Deposit transaction in DeFi, user1",
        fee=0.1
    ))

    txs.append(Transaction(
        tx_id="demo2",
        read_keys={"B"},
        write_keys={"B"},
        action_fn=incB_action,
        memo="An NFT mint for user2, synergy with NodeB",
        fee=0.2
    ))

    txs.append(Transaction(
        tx_id="demo3",
        read_keys={"A","B"},
        write_keys={"A","B"},
        action_fn=cross_action,
        memo="A cross-later transaction referencing bridging or synergy",
        fee=0.05
    ))

    return txs
