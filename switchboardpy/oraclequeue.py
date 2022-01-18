import anchorpy

from dataclasses import dataclass
from decimal import Decimal

from solana import system_program
from solana import keypair
from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.system_program import CreateAccountParams, create_account
from switchboardpy.common import SwitchboardDecimal

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
        if params.public_key is None and params.keypair is None:
            raise ValueError('User must provide either a publicKey or keypair for account use.')
        if params.keypair and params.public_key and params.keypair.public_key != params.public_key:
            raise ValueError('User must provide either a publicKey or keypair for account use.')
        self.program = params.program
        self.public_key = params.keypair.public_key if params.keypair else params.public_key
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

    """
    Create and initialize the OracleQueueAccount

    Args:
        program (anchor.Program)
        params (OracleQueueInitParams)

    Returns:
        OracleQueueAccount
    """
    @staticmethod
    async def create(program: anchorpy.Program, params: OracleQueueInitParams):
        oracle_queue_account = Keypair.generate()
        buffer = Keypair.generate()
        queue_size = params.queue_size or 500
        queue_size = queue_size * 32 + 8
        response = await program.provider.connection.get_minimum_balance_for_rent_exemption(queue_size)
        lamports = response["result"]
        await program.rpc["oracle_queue_init"](
            {
                "name": params.name or bytes([0] * 32),
                "metadata": params.metadata or bytes([0] * 128),
                "reward": params.reward or 0,
                "min_stake": params.min_stake or 0,
                "feed_probation_period": params.feed_probation_period or 0,
                "oracle_timeout": params.oracle_timeout or 180,
                "slashing_enabled": params.slashing_enabled or False,
                "variance_tolerance_multiplier": SwitchboardDecimal.from_decimal(params.variance_tolerance_multiplier or 2),
                "authority": params.authority,
                "consecutive_feed_failure_limit": params.consecutive_feed_failure_limit or 1000,
                "consecutive_oracle_failure_limit": params.consecutive_oracle_failure_limit or 1000,
                "minimum_delay_seconds": params.minimum_delay_seconds or 5,
                "queue_size": params.queue_size,
                "unpermissioned_feeds": params.unpermissioned_feeds or False
            },
            ctx=anchorpy.Context(
                accounts={
                    "oracle_queue": oracle_queue_account.public_key,
                    "authority": params.authority,
                    "buffer": buffer.public_key,
                    "system_program": system_program.SYS_PROGRAM_ID,
                    "payer": program.provider.wallet.public_key
                },
                signers=[oracle_queue_account, buffer],
                instructions=[
                    create_account(
                        CreateAccountParams(
                            from_pubkey=program.provider.wallet.public_key, 
                            new_account_pubkey=buffer.public_key,
                            lamports=lamports, 
                            space=queue_size, 
                            program_id=program.program_id
                        )
                    )
                ]
            )
        )
        return OracleQueueAccount(AccountParams(program=program, keypair=oracle_queue_account));
