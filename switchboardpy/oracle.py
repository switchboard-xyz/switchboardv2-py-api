import anchorpy

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from solana.keypair import Keypair
from solana.publickey import PublicKey

from switchboardpy.common import AccountParams
from switchboardpy.oraclequeue import OracleQueueAccount


# Parameters for an OracleInit request
@dataclass
class OracleInitParams:
    
    """Specifies the oracle queue to associate with this OracleAccount."""
    queue_account: OracleQueueAccount

    """Buffer specifying orace name"""
    name: bytes = None

    """Buffer specifying oralce metadata"""
    metadata: bytes = None

# Parameters for an OracleWithdraw request.
@dataclass
class OracleWithdrawParams:
    
    """Amount to withdraw"""
    amount: Decimal

    """Token Account to withdraw to"""
    withdraw_account: PublicKey

    """Oracle authority keypair"""
    oracle_authority: Keypair
    
class OracleAccount:
    """ A Switchboard account representing an oracle account and its associated queue
    and escrow account.

    Attributes:
        program (anchor.Program): The anchor program ref
        public_key (PublicKey | None): This aggregator's public key
        keypair (Keypair | None): this aggregator's keypair
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
    Get the size of an OracleAccount on chain

    Args:

    Returns:
        int: size of the OracleAccount type on chain
    """
    def size(self):
        return self.program.account["OracleAccountData"].size

    """
    Load and parse OracleAccount data based on the program IDL

    Args:
    
    Returns:
        OracleAccount

    Raises:
        AccountDoesNotExistError: If the account doesn't exist.
        AccountInvalidDiscriminator: If the discriminator doesn't match the IDL.
    """
    async def load_data(self):
        oracle = await self.program.account["OracleAccountData"].fetch(self.public_key)
        oracle.ebuf = None
        return oracle

    """
    Loads a OracleAccount from the expected PDA seed format

    Args:
        program (anchorpy.Program)
        queue_account (OracleQueueAccount)
        wallet (PublicKey)

    Returns:
        Tuple[OracleAccount, int]: OracleAccount and PDA bump
    """
    @staticmethod
    def from_seed(program: anchorpy.Program, queue_account: OracleQueueAccount, wallet: PublicKey):
        oracle_pubkey, bump = PublicKey.find_program_address(
            [
                bytes('OracleAccountData'), 
                bytes(queue_account.public_key),
                bytes(wallet),
            ],
            program.program_id
        )
    
        return OracleAccount(AccountParams(program=program, public_key=oracle_pubkey)), bump

    """
    Create and initialize the OracleAccount.

    Args:
        program (anchor.Program): Switchboard program representation holding connection and IDL.
        params (OracleInitParams)
    
    Returns:
        OracleAccount

    """
    # TODO: imlement fn
    async def create(program: anchorpy.Program, params: Any):
        pass

    """
    Inititates a heartbeat for an OracleAccount, signifying oracle is still healthy.

    Args:
    
    Returns:
        TransactionSignature

    Raises:
        AccountDoesNotExistError: If the account doesn't exist.
        AccountInvalidDiscriminator: If the discriminator doesn't match the IDL.
    """
    # TODO: imlement fn
    async def heartbeat():
        pass

    """
    Withdraw stake and/or rewards from an OracleAccount.

    Args:
        params (OracleWithdrawParams)
    
    Returns:
        TransactionSignature

    Raises:
        AccountDoesNotExistError: If the account doesn't exist.
        AccountInvalidDiscriminator: If the discriminator doesn't match the IDL.
    """
    # TODO: imlement fn
    async def withdraw(params: Any):
        pass