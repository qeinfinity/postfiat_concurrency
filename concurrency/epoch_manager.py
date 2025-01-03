# concurrency/epoch_manager.py

import random

class EpochManager:
    """
    Demonstrates how you might shuffle nodes into subcommittees each epoch.
    For a large system, you might have 50+ nodes or more, dividing them into 'clans' or 'shards.'
    """

    def __init__(self, all_nodes):
        self.all_nodes = all_nodes[:]  # copy
        self.current_epoch = 0
        self.clans_by_epoch = {}

    def start_new_epoch(self, clan_size=3):
        """
        Increments the epoch, randomizes 'all_nodes', splits them into clans of clan_size.
        """
        self.current_epoch += 1
        random.shuffle(self.all_nodes)
        # chunk into groups
        new_clans = []
        for i in range(0, len(self.all_nodes), clan_size):
            chunk = self.all_nodes[i:i+clan_size]
            new_clans.append(chunk)
        self.clans_by_epoch[self.current_epoch] = new_clans
        print(f"[EpochManager] Starting epoch {self.current_epoch}, clans: {new_clans}")

    def get_current_clans(self):
        return self.clans_by_epoch.get(self.current_epoch, [])
