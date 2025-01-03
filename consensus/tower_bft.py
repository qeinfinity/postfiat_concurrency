# consensus/tower_bft.py

class TowerBFT:
    """
    A simplified Tower BFT stub. Real Tower BFT includes vote locking,
    chain selection, etc. We show minimal structure here:
    """
    def __init__(self):
        self.lockouts = {}  # track how many times we've voted on a particular branch
        self.finalized_blocks = {}

    def vote_on_block(self, block):
        """
        In real Tower BFT, you'd broadcast a 'vote' referencing the PoH height,
        then lock out alternative branches if you keep voting on the same chain.
        """
        # For demonstration, we just store a vote
        self.finalized_blocks[block.block_id] = block
        return True

    def is_finalized(self, block_id):
        return block_id in self.finalized_blocks
