# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")

import pytest

from brownie import Wei, accounts, Contract, config
from brownie import StrategyPoolTogether


@pytest.mark.require_network("mainnet-fork")
def test_operation(
    chain,
    vault,
    liveStrategy,
    ticket,
    unitoken,
    uni_liquidity,
    gov,
    rewards,
    guardian,
    strategist,
    alice,
    bob,
    tinytim,
    newstrategy,
):

    unitoken.approve(uni_liquidity, Wei("1000000 ether"), {"from": uni_liquidity})
    unitoken.transferFrom(
        uni_liquidity, gov, Wei("300000 ether"), {"from": uni_liquidity}
    )
    unitoken.approve(gov, Wei("1000000 ether"), {"from": gov})
    unitoken.transferFrom(gov, bob, Wei("1000 ether"), {"from": gov})
    unitoken.transferFrom(gov, alice, Wei("4000 ether"), {"from": gov})
    unitoken.transferFrom(gov, tinytim, Wei("10 ether"), {"from": gov})
    unitoken.approve(vault, Wei("1000000 ether"), {"from": bob})
    unitoken.approve(vault, Wei("1000000 ether"), {"from": alice})
    unitoken.approve(vault, Wei("1000000 ether"), {"from": tinytim})

    newstrategy.setStrategist(strategist)
    vault.migrateStrategy(liveStrategy, newstrategy, {"from": gov})

    assert ticket.balanceOf(liveStrategy) == 0
    assert ticket.balanceOf(newstrategy) > 0
