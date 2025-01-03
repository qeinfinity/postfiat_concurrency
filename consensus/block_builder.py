# consensus/block_builder.py

from consensus.block import Block
from concurrency.daqc import compute_daqc

class BlockBuilder:
    """
    Takes a set of DAQCs from various batch proposers, references them in a new block,
    and uses PoH's latest hash plus Tower BFT for finality.
    """

    def __init__(self, poh_generator, tower_bft):
        self.poh = poh_generator
        self.tower = tower_bft
        self.block_counter = 0
        self.last_block_id = -1

    def build_block(self, daqc_list):
        # We produce a new block referencing the current poh, + previous block ID
        poh_ref = self.poh.get_current_poh()
        block = Block(
            block_id=self.block_counter,
            poh_ref=poh_ref,
            daqc_refs=daqc_list,
            prev_block_id=self.last_block_id,
            votes={}
        )
        self.block_counter += 1
        self.last_block_id = block.block_id
        return block

    def finalize_block(self, block):
        """
        A minimal Tower BFT 'vote'
        """
        self.tower.vote_on_block(block)
        return self.tower.is_finalized(block.block_id)
