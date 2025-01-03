# escrow/escrow_manager.py

class EscrowManager:
    """
    This might store & track the on-chain escrow. For now, we just keep a key in the global state: "ESCROW_POOL".
    The aggregator's reward transaction modifies that key to pay out nodes.
    """
    def __init__(self, account_state):
        self.account_state = account_state
        # Initialize the escrow pool if needed
        if "ESCROW_POOL" not in self.account_state.state_store:
            self.account_state.write("ESCROW_POOL", 1_000_000)
