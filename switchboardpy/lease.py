from __future__ import annotations

import anchorpy

from typing import TYPE_CHECKING
from dataclasses import dataclass

from decimal import Decimal
from solana import publickey
from solana.keypair import Keypair
from solana.publickey import PublicKey

from switchboardpy.oraclequeue import OracleQueueAccount
from switchboardpy.common import AccountParams


if TYPE_CHECKING:
    from switchboardpy.aggregator import AggregatorAccount

# Parameters for initializing a LeaseAccount
@dataclass
class LeaseInitParams:

    """Token amount to load into the lease escrow"""
    load_amount: Decimal

    """The funding wallet of the lease"""
    funder: PublicKey

    """The authority of the funding wallet"""
    funder_authority: Keypair

    """The target to which this lease is applied"""
    oracle_queue_account: OracleQueueAccount

    """The feed which the lease grants permission"""
    aggregator_account: AggregatorAccount

    """This authority will be permitted to withdraw funds from this lease"""
    withdraw_authority: PublicKey = None

# Parameters for extending a LeaseAccount
@dataclass
class LeaseExtendParams:

    """Token amount to load into the lease escrow"""
    load_amount: Decimal

    """The funding wallet of the lease"""
    funder: PublicKey

    """The authority of the funding wallet"""
    funder_authority: Keypair

# Parameters for withdrawing from a LeaseAccount
@dataclass
class LeaseWithdrawParams:

    """Token amount to withdraw from the lease escrow"""
    amount: Decimal

    """The wallet of to withdraw to"""
    withdraw_wallet: PublicKey

    """The withdraw authority of the lease"""
    withdraw_authority: Keypair


class LeaseAccount:
    """ A Switchboard account representing a lease for managing funds for oracle payouts
    for fulfilling feed updates.

    Attributes:
        program (anchor.Program): The anchor program ref
        public_key (PublicKey | None): This lease's public key
        keypair (Keypair | None): this lease's keypair
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
    Get the size of an LeaseAccount on chain

    Args:

    Returns:
        int: size of the LeaseAccount type on chain
    """
    def size(self):
        return self.program.account["LeaseAccountData"].size

    """
    Load and parse LeaseAccount data based on the program IDL

    Args:
    
    Returns:
        LeaseAccount

    Raises:
        AccountDoesNotExistError: If the account doesn't exist.
        AccountInvalidDiscriminator: If the discriminator doesn't match the IDL.
    """
    async def load_data(self):
        lease = await self.program.account["LeaseAccountData"].fetch(self.public_key)
        lease.ebuf = None
        return lease

    """
    Loads a LeaseAccount from the expected PDA seed format

    Args:
        program (anchorpy.Program)
        queue_account (OracleQueueAccount)
        aggregator_account (AggregatorAccount)

    Returns:
        Tuple[LeaseAccount, int]: LeaseAccount and PDA bump
    """
    @staticmethod
    def from_seed(program: anchorpy.Program, queue_account: OracleQueueAccount, aggregator_account: AggregatorAccount):
        pubkey, bump = publickey.PublicKey.find_program_address(
            [
                bytes('LeaseAccountData'), 
                bytes(queue_account.public_key),
                bytes(aggregator_account.public_key),
            ],
            program.program_id
        )
    
        return LeaseAccount(AccountParams(program=program, public_key=pubkey)), bump
