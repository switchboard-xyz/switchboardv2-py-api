import asyncio
from pytest import fixture, mark

from switchboardpy import (
  SBV2_DEVNET_PID,
  AggregatorOpenRoundParams,
  AggregatorInitParams,
  AggregatorHistoryRow,
  AggregatorAccount,
  AccountParams,
  AggregatorSaveResultParams,
  AggregatorSetHistoryBufferParams,
)

from contextlib import contextmanager
from decimal import Decimal
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from anchorpy import Program, Provider, Wallet

class SwitchboardProgram(object):

    async def __aenter__(self):
      client = AsyncClient("https://api.devnet.solana.com/")
      provider = Provider(client, Wallet(Keypair()))
      self.program = await Program.at(
          SBV2_DEVNET_PID, provider
      )
      return self.program
    
    async def __aexit__(self, exc_t, exc_v, exc_tb):
        await self.program.close()

@mark.asyncio
async def test_load_data():
    async with SwitchboardProgram() as program:
    
        agg = AggregatorAccount(AccountParams(program=program, public_key=PublicKey("88FX4tBstuwBPNhQU4EEBoPX35neSu4Le9zDSwtPRRQz")))

        # getting aggregator data
        data = await agg.load_data()

        assert data.min_oracle_results == 3
        assert data.oracle_request_batch_size == 6
        assert data.min_job_results == 2
        print(data)

@mark.asyncio
async def test_get_latest_value():
    async with SwitchboardProgram() as program:
        agg = AggregatorAccount(AccountParams(program=program, public_key=PublicKey("88FX4tBstuwBPNhQU4EEBoPX35neSu4Le9zDSwtPRRQz")))

        # getting most recent value
        val = await agg.get_latest_value()

        assert Decimal('180.12115') == val

        print('LATEST VALUE:')
        print(val)
