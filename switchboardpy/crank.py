import anchorpy

from dataclasses import dataclass
from typing import Any

from solana.publickey import PublicKey
from switchboardpy.common import AccountParams
from switchboardpy.oraclequeue import OracleQueueAccount
from switchboardpy.aggregator import AggregatorAccount

# Parameters for initializing a CrankAccount
@dataclass
class CrankInitParams:

    """OracleQueueAccount for which this crank is associated"""
    queue_account: OracleQueueAccount

    """Buffer specifying crank name"""
    names: bytes = None

    """Buffer specifying crank metadata"""
    metadata: bytes = None

    """Optional max number of rows"""
    max_rows: int = None

# Parameters for popping an element from a CrankAccount
@dataclass
class CrankPopParams:

    """Specifies the wallet to reward for turning the crank."""
    payout_wallet: PublicKey

    """The pubkey of the linked oracle queue."""
    queue_pubkey: PublicKey

    """The pubkey of the linked oracle queue authority."""
    queue_authority: PublicKey

    """CrankAccount data"""
    crank: Any

    """QueueAccount data"""
    queue: Any

    """Token mint pubkey"""
    token_mint: PublicKey

    """
    Array of pubkeys to attempt to pop. If discluded, this will be loaded
    from the crank upon calling.
    """
    ready_pubkeys: list[PublicKey] = None

    """Nonce to allow consecutive crank pops with the same blockhash."""
    nonce: int = None
    fail_open_on_mismatch: bool = None

# Parameters for pushing an element into a CrankAccount
@dataclass
class CrankPushParams:
    aggregator_account: AggregatorAccount

# Row structure of elements in the crank
@dataclass
class CrankRow:

    """Aggregator account pubkey"""
    pubkey: PublicKey

    """Next aggregator update timestamp to order the crank by"""
    next_timestamp: int

    @staticmethod
    def from_bytes(buf: bytes):
        pass

class CrankAccount:
    """ A Switchboard account representing a crank of aggregators ordered by next update time.

    Attributes:
        program (anchor.Program): The anchor program ref
        public_key (PublicKey | None): This crank's public key
        keypair (Keypair | None): this crank's keypair
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
    Get the size of an CrankAccount on chain

    Args:

    Returns:
        int: size of the CrankAccount type on chain
    """
    def size(self):
        return self.program.account["CrankAccountData"].size

    """
    Load and parse CrankAccount data based on the program IDL

    Args:
    
    Returns:
        CrankAccount

    Raises:
        AccountDoesNotExistError: If the account doesn't exist.
        AccountInvalidDiscriminator: If the discriminator doesn't match the IDL.
    """
    async def load_data(self):
        crank = await self.program.account["CrankAccountData"].fetch(self.public_key)
        crank.ebuf = None
        return crank

    """
    Create and initialize the CrankAccount.

    Args:
        program (anchor.Program): Switchboard program representation holding connection and IDL.
        params (CrankInitParams)
    
    Returns:
        CrankAccount
    """
    # TODO: imlement fn
    async def create(program: anchorpy.Program, params: Any):
        pass

    """
    Pushes a new aggregator onto the crank
    
    Args:
        aggregator (CrankPushParams)
    
    Returns:
        TransactionSignature
    """
    async def push(params: Any):
        pass
    
    """
    Pops a tx from the crank.

    Args:
        params (CrankPopParams)

    Returns:
        TransactionSignature    
    """
    async def pop_txn(params: Any):
        pass

    """
    Pops an aggregator from the crank

    Args:
        params (CrankPopParams)
    
    Returns:
        TransactionSignature
    """
    async def pop(params: Any):
        pass
    
    """
    Get an array of the next aggregator pubkeys to be popped from the crank, limited by n

    Args:
        n (int): limit of pubkeys to return

    Returns:
        list[CrankRow]: Pubkey list of Aggregators and next timestamp to be popped, ordered by timestamp
    """
    async def peak_next_with_time(n: int):
        pass

    """
    Get an array of the next readily updateable aggregator pubkeys to be popped
    from the crank, limited by n

    Args:
        n (Optional[int]): limit of pubkeys to return

    Returns:
        list[PublicKey]: Pubkey list of Aggregators and next timestamp to be popped, ordered by timestamp
    """
    async def peak_next_ready(n: int):
        pass

    """
    Get an array of the next aggregator pubkeys to be popped from the crank, limited by n

    Args:
        n (int): limit of pubkeys to return

    Returns:
        list[PublicKey]: Pubkey list of Aggregators and next timestamp to be popped, ordered by timestamp
    """
    async def peak_next(n: int):
        pass

