import pytest
from brownie import Wei, accounts, Contract, config
from brownie import StrategyDAIPoolTogether


@pytest.mark.require_network("mainnet-fork")
def test_clone(
    chain,
    gov,
    unitoken,
    comp_strategy,
    uni_vault,
    uni_want_pool,
    pool_token,
    uni,
    uni_bonus,
    uni_faucet,
    uni_ticket,
    uni_liquidity,
    alice,
):

    # Clone the strategy
    tx = comp_strategy.clone(
        uni_vault,
        gov,
        gov,
        gov,
        uni_want_pool,
        pool_token,
        uni,
        uni_bonus,
        uni_faucet,
        uni_ticket,
    )
    uni_strategy = StrategyDAIPoolTogether.at(tx.return_value)
    uni_vault.addStrategy(uni_strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})

    # Try a deposit and harvest
    unitoken.transfer(alice, Wei("100 ether"), {"from": uni_liquidity})
    unitoken.approve(uni_vault, 2 ** 256 - 1, {"from": alice})
    uni_vault.deposit({"from": alice})

    # Invest!
    uni_strategy.harvest({"from": gov})

    # Wait one week
    chain.sleep(604801)
    chain.mine()

    # Get profits and withdraw
    uni_strategy.harvest({"from": gov})

    # Wait one more week just in case
    chain.sleep(604801)
    chain.mine()

    uni_vault.withdraw({"from": alice})
    assert unitoken.balanceOf(alice) > Wei("100 ether")
