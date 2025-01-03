# consensus/block.py

from dataclasses import dataclass
from typing import List

@dataclass
class Block:
    block_id: int
    poh_ref: bytes            # hash from PoH
    daqc_refs: List[bytes]    # references to data availability certificates
    prev_block_id: int
    votes: dict               # Tower BFT votes
    # In a real system, we'd store more metadata (leader ID, version, etc.)

    def __repr__(self):
        return f"<Block {self.block_id}, poh={self.poh_ref.hex()[:6]}...>"
