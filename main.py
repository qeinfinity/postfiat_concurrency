# main.py

import time
from concurrency.account_state import AccountState
from concurrency.concurrency_engine import ConcurrencyEngine
from consensus.poh import PoHGenerator
from consensus.tower_bft import TowerBFT
from consensus.block_builder import BlockBuilder
from aggregator.synergy_ai import AINodeAggregator
from concurrency.daqc import compute_daqc
from concurrency.transaction import Transaction
from concurrency.batch_proposer import BatchProposer
from escrow.escrow_manager import EscrowManager

def main():
    # 1) Initialize ledger & concurrency
    account_state = AccountState()
    concurrency_engine = ConcurrencyEngine(account_state)
    escrow_mgr = EscrowManager(account_state)  # ensures ESCROW_POOL

    # 2) Initialize consensus (PoH + Tower BFT)
    poh = PoHGenerator()
    tower_bft = TowerBFT()
    block_builder = BlockBuilder(poh, tower_bft)

    # 3) Node profiles + aggregator
    node_profiles = {
        "NodeA": "Focus: DeFi, financial AI",
        "NodeB": "Focus: NFTs, gaming synergy",
        "NodeC": "Focus: cross-chain bridging"
    }
    aggregator = AINodeAggregator(node_profiles=node_profiles, monthly_cycle=15.0) 
    # For demo, monthly is 15 secs

    # 4) Create some batch proposers
    proposerA = BatchProposer("NodeA")
    proposerB = BatchProposer("NodeB")

    # 4a) Add transactions with memos
    def inc_action(read_data):
        old_val = read_data.get("A", 0)
        return {"A": old_val + 10}

    tx1 = Transaction(
        tx_id="tx1",
        read_keys={"A"}, 
        write_keys={"A"},
        action_fn=inc_action,
        memo="Hello from user1. This is a DeFi deposit task."
    )
    proposerA.add_to_primary(tx1)

    def incB_action(read_data):
        old_val = read_data.get("B", 0)
        return {"B": old_val + 5}

    tx2 = Transaction(
        tx_id="tx2",
        read_keys={"B"}, 
        write_keys={"B"},
        action_fn=incB_action,
        memo="User2 minted an NFT. Possibly synergy with NodeB's NFT focus."
    )
    proposerB.add_to_primary(tx2)

    # Form batch from each
    batchA = proposerA.form_batch()
    batchB = proposerB.form_batch()
    daqcA = compute_daqc(batchA)
    daqcB = compute_daqc(batchB)

    # Build + finalize block
    poh.record_event(b"block1")
    block1 = block_builder.build_block([daqcA, daqcB])
    finalized = block_builder.finalize_block(block1)
    if finalized:
        # Execute concurrency
        all_txs = batchA + batchB
        concurrency_results = concurrency_engine.execute_block_of_transactions(all_txs)

        # aggregator: gather block memos + node activity 
        # node_activity might say NodeA had activity=5, NodeB=5, etc.
        block_memos = [tx.memo for tx in all_txs]
        aggregator.process_final_block(
            block=block1,
            node_activity={"NodeA": 5, "NodeB": 5},  
            block_memos=block_memos
        )

        print("== Block1 Finalized, concurrency results:", concurrency_results)
        print("State now:", account_state.state_store)

    # Sleep a bit, then see if aggregator triggers monthly synergy
    time.sleep(2)

    synergy_tx = aggregator.maybe_run_monthly()
    if synergy_tx:
        poh.record_event(b"block2")
        daqcReward = compute_daqc([synergy_tx])
        block2 = block_builder.build_block([daqcReward])
        block_builder.finalize_block(block2)
        # run concurrency
        concurrency_engine.execute_block_of_transactions([synergy_tx])
        print("== AI Reward TX executed. State now:", account_state.state_store)

if __name__ == "__main__":
    main()
