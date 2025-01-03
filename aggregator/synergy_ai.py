# aggregator/synergy_ai.py

import time
import os
import openai
from typing import Dict, List

# Ensure you set: export OPENAI_API_KEY="your_key_here"
openai.api_key = os.getenv("OPENAI_API_KEY")

class AINodeAggregator:
    """
    A synergy aggregator that:
      1) Reads final blocks & transaction memos
      2) Calls OpenAI to parse synergy, alignment with node roles
      3) Assigns synergy scores to each node
      4) Periodically issues a synergy-based reward transaction
    """

    def __init__(self, node_profiles: Dict[str, str] = None, monthly_cycle: float = 30.0):
        """
        node_profiles: e.g. { "NodeA": "Focus: DeFi / NFT", ... }
        monthly_cycle: how often (seconds) we do synergy-based payouts
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
        block_memos: collected from the transaction memos in the block
        node_activity: e.g. which node proposed the batch or was credited
                       for including tasks
        """
        # 1) Summarize the block memos with LLM
        synergy_score_map = self._analyze_memos_with_llm(block_memos, node_activity)
        # 2) Add synergy + node_activity points into node_scores
        for node_id, base_score in node_activity.items():
            synergy_bonus = synergy_score_map.get(node_id, 0)
            self.node_scores[node_id] = self.node_scores.get(node_id, 0) + base_score + synergy_bonus

    def _analyze_memos_with_llm(self, memos: List[str], node_activity: Dict[str, float]) -> Dict[str, float]:
        """
        Make a real call to OpenAI, interpret synergy. We'll do 1 call for the entire block's memos,
        referencing each node's declared profile and the memos themselves.
        We'll produce synergy scores for each node.
        """
        if not memos:
            return {}

        # We'll create a single prompt that lumps together all memos plus node profiles.
        # In a real system, you might chunk data or do multiple calls.
        big_memo_text = "\n".join([f"Memo: {m}" for m in memos])
        profile_text = "\n".join([f"{nid} => {desc}" for nid, desc in self.node_profiles.items()])

        prompt = f"""
We have a set of transaction memos in a block, and certain nodes that included them.
We also have node profiles describing each node's declared specialties or focuses.
We want to assign each node a synergy bonus from 0 to 5, based on how well the block memos 
align with that node's declared focus and how cooperative the memos appear.

Node Profiles:
{profile_text}

Block Memos:
{big_memo_text}

Nodes that contributed to this block: {list(node_activity.keys())}

For each node that contributed to this block, produce an integer synergy bonus from 0 to 5, 
based purely on alignment between these memos and that node's declared focus. 
Return the results as a simple JSON object: 
  {{"node_id": synergy_score, ...}}
        """

        # We'll call openai ChatCompletion for example
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            content = response["choices"][0]["message"]["content"]
        except Exception as e:
            print("OpenAI call failed:", e)
            # fallback: no synergy
            return {}

        # Attempt to parse the returned JSON
        synergy_map = {}
        import json
        try:
            synergy_map = json.loads(content)
            # synergy_map should look like: {"NodeA": 3, "NodeB": 2, ...}
        except json.JSONDecodeError:
            # If the LLM didn't respond with valid JSON, fallback to zero synergy
            synergy_map = {}

        # Convert all synergy to float, in case we do further math
        synergy_map = {k: float(v) for k, v in synergy_map.items() if k in node_activity}
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
            fraction = sc / total_score
            payouts[node_id] = fraction * pft_pool

        self.node_scores.clear()

        def payout_action(read_data):
            updates = {}
            for n_id, amt in payouts.items():
                key = f"BAL_{n_id}"
                old_bal = read_data.get(key, 0)
                updates[key] = old_bal + amt
            old_escrow = read_data.get("ESCROW_POOL", 1000000)
            updates["ESCROW_POOL"] = old_escrow - pft_pool
            return updates

        from concurrency.transaction import Transaction
        write_keys = set([f"BAL_{nid}" for nid in payouts.keys()] + ["ESCROW_POOL"])
        tx = Transaction(
            tx_id=f"AI_REWARD_{int(time.time())}",
            read_keys=set(["ESCROW_POOL"] + [f"BAL_{nid}" for nid in payouts.keys()]),
            write_keys=write_keys,
            action_fn=payout_action,
            memo="Monthly synergy distribution from AI aggregator."
        )
        return tx
