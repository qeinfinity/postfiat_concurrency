# main.py

import time
import os

from concurrency.account_state import AccountState
from concurrency.concurrency_engine import ConcurrencyEngine
from concurrency.daqc import compute_daqc
from concurrency.transaction import Transaction
from concurrency.batch_proposer import BatchProposer
from concurrency.epoch_manager import EpochManager

from consensus.poh import PoHGenerator
from consensus.tower_bft import TowerBFT
from consensus.block_builder import BlockBuilder

from aggregator.synergy_ai import AINodeAggregator
from escrow.escrow_manager import EscrowManager

# Import sample transactions for demonstration
from samples.sample_transactions import get_demo_transactions

def main():
    # 1) Initialize ledger & concurrency
    account_state = AccountState()
    concurrency_engine = ConcurrencyEngine(account_state)
    escrow_mgr = EscrowManager(account_state)  # ensures ESCROW_POOL is in place

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
    # We'll let the aggregator produce synergy-based payouts every 15 seconds for this demo
    aggregator = AINodeAggregator(node_profiles=node_profiles, monthly_cycle=15.0)

    # 3a) Epoch Manager for Node Reassignments (optional)
    node_list = ["NodeA", "NodeB", "NodeC"]
    epoch_mgr = EpochManager(node_list)
    epoch_mgr.start_new_epoch(clan_size=2)  # just for demonstration

    # 4) Create some batch proposers (assume NodeA & NodeB, NodeC is idle)
    proposerA = BatchProposer("NodeA")
    proposerB = BatchProposer("NodeB")

    # 4a) Load sample transactions
    demo_txs = get_demo_transactions()
    # Let's say NodeA picks the first two, NodeB picks the last one
    proposerA.add_to_primary(demo_txs[0])
    proposerA.add_to_primary(demo_txs[1])
    proposerB.add_to_primary(demo_txs[2])

    # 5) Optionally let aggregator reorder tasks for synergy if desired
    new_batchA = aggregator.propose_ordering_for_block(proposerA.primary_bucket, "NodeA")
    new_batchB = aggregator.propose_ordering_for_block(proposerB.primary_bucket, "NodeB")
    # Then replace the proposers' buckets
    proposerA.primary_bucket = new_batchA
    proposerB.primary_bucket = new_batchB

    # 6) Form batch from each
    batchA = proposerA.form_batch()
    batchB = proposerB.form_batch()

    # Produce data availability certificates
    daqcA = compute_daqc(batchA)
    daqcB = compute_daqc(batchB)

    # 7) Build + finalize block
    poh.record_event(b"block1")
    block1 = block_builder.build_block([daqcA, daqcB])
    finalized = block_builder.finalize_block(block1)

    if finalized:
        all_txs = batchA + batchB
        concurrency_results = concurrency_engine.execute_block_of_transactions(all_txs)

        # aggregator: gather memos + node activity
        block_memos = [tx.memo for tx in all_txs]
        # NodeA, NodeB each get a base of 5 points for participating
        aggregator.process_final_block(
            block=block1,
            node_activity={"NodeA": 5, "NodeB": 5},
            block_memos=block_memos
        )

        print("\n== Block1 Finalized, concurrency results:", concurrency_results)
        print("Ledger State now:", account_state.state_store)

    # 8) Sleep & see if aggregator triggers monthly synergy
    print("\nSleeping for aggregator cycle...\n")
    time.sleep(3)

    synergy_tx = aggregator.maybe_run_monthly()
    if synergy_tx:
        poh.record_event(b"block2")
        daqcReward = compute_daqc([synergy_tx])
        block2 = block_builder.build_block([daqcReward])
        block_builder.finalize_block(block2)
        concurrency_engine.execute_block_of_transactions([synergy_tx])
        print("== AI Reward TX executed. Ledger State now:", account_state.state_store)


if __name__ == "__main__":
    # Make sure to set OPENAI_API_KEY in environment if you want synergy AI calls
    main()
