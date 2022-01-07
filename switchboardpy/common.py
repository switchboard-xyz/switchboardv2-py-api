import anchorpy

from dataclasses import dataclass
from typing import Any
from decimal import Decimal
from solana.publickey import PublicKey
from solana.keypair import Keypair

# Devnet Program ID.
SBV2_DEVNET_PID = PublicKey(
    '2TfB33aLaneQb5TNVwyDz3jSZXS6jdW2ARw1Dgf84XCG'
)

# Input parameters for constructing wrapped representations of Switchboard accounts. 
@dataclass
class AccountParams:

    """program referencing the Switchboard program and IDL."""
    program: anchorpy.Program

    """
    Public key of the account being referenced. This will always be populated
    within the account wrapper.
    """
    public_key: PublicKey = None

    """Keypair of the account being referenced. This may not always be populated."""
    keypair: Keypair = None

@dataclass
class SwitchboardDecimal:
    mantissa: int
    scale: int

    """
    Convert BN.js style num and return SwitchboardDecimal

    Args:
        obj (Any): Object with integer fields scale and mantissa (hex val)

    Returns:
        sbd (SwitchboardDecimal): SwitchboardDecimal
    """
    @staticmethod
    def fromObj(obj: Any):
        return SwitchboardDecimal(
            mantissa=obj.mantissa,
            scale=obj.scale
        )
    
    def to_decimal(self, sbd: object):
        mantissa = Decimal(sbd.mantissa)
        scale = sbd.scale
        return mantissa / Decimal(10 ** scale)

    @staticmethod
    def from_decimal(dec: Decimal):
        pass

    # convert any switchboard-decimal-like object to a decimal
    @staticmethod
    def sbd_to_decimal(sbd: object) -> Decimal:
        mantissa = Decimal(sbd.mantissa)
        scale = sbd.scale
        return mantissa / Decimal(10 ** scale)

    def __eq__(self, __o: object) -> bool:
        if not (hasattr(__o, 'mantissa') and hasattr(__o, 'scale')):
            return False
        return self.mantissa == __o.mantissa and self.scale == __o.scale
