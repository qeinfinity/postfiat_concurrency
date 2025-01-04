# aggregator/synergy_ai.py

import time
import os
from openai import OpenAI
import json
from typing import Dict, List

# Deterministic LLM usage
#openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)

class AINodeAggregator:
    """
    A synergy aggregator that:
      1) Reads final blocks & transaction memos
      2) Calls OpenAI with temperature=0 for deterministic synergy alignment
      3) Accumulates synergy scores for node_id
      4) Periodically issues a synergy-based reward transaction
      5) Optionally can reorder tasks prior to block finalization (not fully implemented by default)
    """

    def __init__(self, node_profiles: Dict[str, str] = None, monthly_cycle: float = 30.0):
        """
        :param node_profiles: e.g. { "NodeA": "Focus: DeFi / NFT", ... }
        :param monthly_cycle: how often (seconds) we do synergy-based payouts
        """
        self.node_scores = {}   # node_id -> float
        self.node_profiles = node_profiles or {}
        self.monthly_cycle = monthly_cycle
        self.last_run = time.time()

    def process_final_block(
        self,
        block,
        node_activity: Dict[str, float],
        block_memos: List[str]
    ):
        """
        :param block_memos: collected from the transaction memos in the block
        :param node_activity: e.g. which node proposed the batch or was credited
                              for including tasks, mapped to a base numeric value
        """
        if not block_memos and not node_activity:
            return

        synergy_score_map = self._analyze_memos_with_llm(block_memos, node_activity)
        # Merge synergy + node_activity into node_scores
        for node_id, base_score in node_activity.items():
            synergy_bonus = synergy_score_map.get(node_id, 0.0)
            old_score = self.node_scores.get(node_id, 0.0)
            new_score = old_score + base_score + synergy_bonus
            self.node_scores[node_id] = new_score

    def _analyze_memos_with_llm(self, memos: List[str], node_activity: Dict[str, float]) -> Dict[str, float]:
        """
        Call openai with temperature=0 for near-deterministic synergy calculation
        Return: { node_id: synergy_bonus, ... }
        """
        if not memos:
            return {}

        big_memo_text = "\n".join([f"- {m}" for m in memos])
        profile_text = "\n".join([f"{nid} => {desc}" for nid, desc in self.node_profiles.items()])
        node_list = list(node_activity.keys())

        prompt = f"""
We have a set of transaction memos in a block, plus node profiles.

Node Profiles:
{profile_text}

Block Memos:
{big_memo_text}

Nodes that contributed to this block: {node_list}

We want an integer synergy bonus from 0..5 for each node, based on:
- Does the block's content (memos) align with that node's declared focus?
- Are the memos thematically relevant to the node's domain?

Return a JSON object of synergy scores like:
{{"NodeA": 3, "NodeB": 5, ...}}
        """

        # Deterministic call
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=200,
            )
            content = response.choices[0].message.content.strip()
        except Exception as e:
            print("[AI Aggregator] OpenAI call failed:", e)
            return {}

        synergy_map = {}
        try:
            parsed = json.loads(content)
            # Only keep keys that exist in node_activity
            for node_id, synergy_str in parsed.items():
                if node_id in node_activity:
                    synergy_val = float(synergy_str)
                    synergy_map[node_id] = synergy_val
        except json.JSONDecodeError:
            # fallback
            pass

        return synergy_map

    def maybe_run_monthly(self):
        now = time.time()
        if now - self.last_run >= self.monthly_cycle:
            synergy_tx = self._generate_synergy_reward_tx()
            self.last_run = now
            return synergy_tx
        return None

    def _generate_synergy_reward_tx(self):
        total_score = sum(self.node_scores.values())
        if total_score == 0:
            return None

        pft_pool = 100000
        payouts = {}
        for node_id, sc in self.node_scores.items():
            frac = sc / total_score
            payouts[node_id] = frac * pft_pool

        self.node_scores.clear()

        from concurrency.transaction import Transaction
        write_set = set([f"BAL_{nid}" for nid in payouts.keys()] + ["ESCROW_POOL"])

        def payout_action(read_data):
            updates = {}
            old_escrow = read_data.get("ESCROW_POOL", 1_000_000)
            updates["ESCROW_POOL"] = old_escrow - pft_pool
            for n_id, amt in payouts.items():
                bal_key = f"BAL_{n_id}"
                old_bal = read_data.get(bal_key, 0)
                updates[bal_key] = old_bal + amt
            return updates

        tx = Transaction(
            tx_id=f"AI_REWARD_{int(time.time())}",
            read_keys=set(["ESCROW_POOL"] + [f"BAL_{n}" for n in payouts.keys()]),
            write_keys=write_set,
            action_fn=payout_action,
            memo="Monthly synergy distribution from AI aggregator"
        )
        return tx

    # Optional: For daily synergy scheduling or reordering
    def propose_ordering_for_block(self, pending_txs, node_id) -> List:
        """
        Suggest an ordering for the node's pending transactions, 
        awarding synergy for transactions whose memos match node's focus.
        """
        def synergy_priority(tx):
            score = 0
            profile = self.node_profiles.get(node_id, "")
            # Basic rule: If profile has 'DeFi' and tx memo includes 'DeFi', big synergy
            if "DeFi" in profile and "DeFi" in tx.memo:
                score += 5
            if "NFT" in profile and "NFT" in tx.memo:
                score += 3
            # negative so higher synergy sorts first
            return -score

        sorted_list = sorted(pending_txs, key=synergy_priority)
        return sorted_list

    def record_censorship_flags(self, suspicious_node: str, reason: str):
        """
        If we detect a node is refusing tasks or found malicious,
        we penalize them to reduce their monthly synergy payout.
        """
        penalty_points = 10
        old_score = self.node_scores.get(suspicious_node, 0)
        self.node_scores[suspicious_node] = old_score - penalty_points
        print(f"[AI Aggregator] Node {suspicious_node} penalized: {reason}")

