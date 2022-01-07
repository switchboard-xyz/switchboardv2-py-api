from dataclasses import dataclass
from decimal import Decimal
from solana.publickey import PublicKey

from switchboardpy.common import AccountParams

# Parameters for initializing OracleQueueAccount
@dataclass
class OracleQueueInitParams:

    """Rewards to provide oracles and round openers on this queue."""
    reward: Decimal

    """The minimum amount of stake oracles must present to remain on the queue."""
    min_stake: Decimal

    """
    The account to delegate authority to for creating permissions targeted
    at the queue.
    """
    authority: PublicKey 

    """Time period we should remove an oracle after if no response."""
    oracle_timeout: int = None

    """
    The tolerated variance amount oracle results can have from the
    accepted round result before being slashed.
    slashBound = varianceToleranceMultiplier * stdDeviation
    Default: 2
    """
    variance_tolerance_multiplier: float = None

    """Consecutive failure limit for a feed before feed permission is revoked."""
    consecutive_feed_failure_limit: int = None

    """
    TODO: implement
    Consecutive failure limit for an oracle before oracle permission is revoked.
    """
    consecutive_oracle_failure_limit: int = None

    """the minimum update delay time for Aggregators"""
    minimum_delay_seconds: int = None

    """Optionally set the size of the queue."""
    queue_size: int = None

    """
    Enabling this setting means data feeds do not need explicit permission
    to join the queue.
    """
    unpermissioned_feeds: bool = None

    """Whether slashing is enabled on this queue"""
    slashing_enabled: bool = None

    """
    After a feed lease is funded or re-funded, it must consecutively succeed
    N amount of times or its authorization to use the queue is auto-revoked.
    """
    feed_probation_period: int = None

    """A name to assign to this OracleQueue."""
    name: bytes = None

    """Buffer for queue metadata."""
    metadata: bytes = None

class OracleQueueAccount:
    """A Switchboard account representing a queue for distributing oracles to
    permitted data feeds.

    Attributes:
        program (anchor.Program): The anchor program ref
        public_key (PublicKey | None): This OracleQueueAccount's public key
        keypair (Keypair | None): this OracleQueueAccount's keypair
    """

    def __init__(self, params: AccountParams):
        if params.pubkey is None and params.keypair is None:
            raise ValueError('User must provide either a publicKey or keypair for account use.')
        if params.keypair and params.pubkey and params.keypair.public_key != params.pubkey:
            raise ValueError('User must provide either a publicKey or keypair for account use.')
        self.program = params.program
        self.public_key = params.keypair.public_key if params.keypair else params.pubkey
        self.keypair = params.keypair

    """
    Get the size of an OracleQueueAccount on chain

    Args:

    Returns:
        int: size of the OracleQueueAccount type on chain
    """
    def size(self):
        return self.program.account["OracleQueueAccountData"].size

    """
    Load and parse OracleQueueAccount data based on the program IDL

    Args:
    
    Returns:
        OracleQueueAccount

    Raises:
        AccountDoesNotExistError: If the account doesn't exist.
        AccountInvalidDiscriminator: If the discriminator doesn't match the IDL.
    """
    async def load_data(self):
        queue = await self.program.account["OracleQueueAccountData"].fetch(self.public_key)
        queue.ebuf = None
        return queue