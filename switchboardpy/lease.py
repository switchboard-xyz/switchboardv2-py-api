from __future__ import annotations

import anchorpy

from typing import TYPE_CHECKING
from dataclasses import dataclass

from decimal import Decimal
from solana import publickey, system_program
from solana.keypair import Keypair
from solana.publickey import PublicKey
from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address

from switchboardpy.oraclequeue import OracleQueueAccount
from switchboardpy.common import AccountParams

if TYPE_CHECKING:
    from switchboardpy.aggregator import AggregatorAccount
    from switchboardpy.program import ProgramStateAccount


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
        if params.public_key is None and params.keypair is None:
            raise ValueError('User must provide either a publicKey or keypair for account use.')
        if params.keypair and params.public_key and params.keypair.public_key != params.public_key:
            raise ValueError('User must provide either a publicKey or keypair for account use.')
        self.program = params.program
        self.public_key = params.keypair.public_key if params.keypair else params.public_key
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

    """
    Create and initialize the LeaseAccount.

    Args:
        program (anchor.Program): Switchboard program representation holding connection and IDL.
        params (LeaseInitParams)
    
    Returns:
        LeaseAccount
    """
    @staticmethod
    async def create(program: anchorpy.Program, params: LeaseInitParams):
        program_state_account, state_bump = ProgramStateAccount.from_seed(program)
        switch_token_mint = await program_state_account.get_token_mint()
        lease_account, lease_bump = LeaseAccount.from_seed(
            program,
            params.oracle_queue_account,
            params.aggregator_account
        )
        escrow = get_associated_token_address(
            lease_account.public_key,
            switch_token_mint.program_id
        )

        try:
            await switch_token_mint.create_associated_token_account(lease_account.public_key)
        except Exception:
            pass
        await program.rpc["lease_init"](
            {
                "load_amount": params.load_amount,
                "state_bump": state_bump,
                "lease_bump": lease_bump,
                "withdraw_authority": params.withdraw_authority or PublicKey('11111111111111111111111111111111')
            },
            ctx=anchorpy.Context(
                accounts={
                    "program_state": program_state_account.public_key,
                    "lease": lease_account.public_key,
                    "queue": params.oracle_queue_account.public_key,
                    "aggregator": params.aggregator_account.public_key,
                    "system_program": system_program.SYS_PROGRAM_ID,
                    "funder": params.funder,
                    "payer": program.provider.wallet.public_key,
                    "token_program": TOKEN_PROGRAM_ID,
                    "escrow": escrow,
                    "owner": params.funder_authority.public_key,
                },
                signers=[params.funder_authority]
            )
        )
        return LeaseAccount(AccountParams(program=program, public_key=lease_account.public_key))

    """
    Adds fund to a LeaseAccount. Note that funds can always be withdrawn by
    the withdraw authority if one was set on lease initialization.

    Args:
        program (anchor.Program): Switchboard program representation holding connection and IDL.
        params (LeaseExtendParams)
    
    Returns:
        TransactionSignature
    """
    async def extend(self, params: LeaseExtendParams):
        program = self.program
        lease = await self.load_data()
        escrow = lease.escrow
        queue = lease.queue
        aggregator = lease.aggregator
        program_state_account, state_bump = ProgramStateAccount.from_seed(program)
        switch_token_mint = await program_state_account.get_token_mint()
        lease_account, lease_bump = LeaseAccount.from_seed(
            program,
            OracleQueueAccount(AccountParams(program=program, public_key=queue)),
            AggregatorAccount(AccountParams(program=program, public_key=aggregator))
        )
        return await program.rpc["lease_extend"](
            {
                "load_amount": params.load_amount,
                "state_bump": state_bump,
                "lease_bump": lease_bump
            },
            ctx=anchorpy.Context(
                accounts={
                    "lease": lease_account.public_key,
                    "aggregator": aggregator,
                    "queue": queue,
                    "funder": params.funder,
                    "owner": params.funder_authority.public_key,
                    "token_program": TOKEN_PROGRAM_ID,
                    "escrow": escrow,
                    "program_state": program_state_account.public_key
                },
                signers=[params.funder_authority]
            )
        )
 
    """
    Withdraw stake and/or rewards from a LeaseAccount.

    Args:
        params (LeaseWithdrawParams)
    
    Returns:
        TransactionSignature

    Raises:
        AccountDoesNotExistError: If the account doesn't exist.
        AccountInvalidDiscriminator: If the discriminator doesn't match the IDL.
    """
    async def withdraw(self, params: LeaseWithdrawParams):
        program = self.program
        lease = await self.load_data()
        escrow = lease.escrow
        queue = lease.queue
        aggregator = lease.aggregator
        program_state_account, state_bump = ProgramStateAccount.from_seed(program)
        lease_account, lease_bump = LeaseAccount.from_seed(
            program,
            OracleQueueAccount(AccountParams(program=program, public_key=queue)),
            AggregatorAccount(AccountParams(program=program, public_key=aggregator))
        )
        return await self.program.rpc["lease_withdraw"](
            {
                "amount": params.amount,
                "state_bump": state_bump,
                "lease_bump": lease_bump
            },
            ctx=anchorpy.Context(
                accounts={
                    "lease": lease_account.public_key,
                    "escrow": escrow,
                    "aggregator": aggregator,
                    "queue": queue,
                    "withdraw_authority": params.withdraw_authority.public_key,
                    "withdraw_account": params.withdraw_wallet,
                    "token_program": TOKEN_PROGRAM_ID,
                    "program_state": program_state_account.public_key,
                },
                signers=[params.withdraw_authority]
            )
        )
