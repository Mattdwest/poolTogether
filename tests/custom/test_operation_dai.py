# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")

import pytest

from brownie import Wei, accounts, Contract, config
from brownie import StrategyDAIPoolTogether


@pytest.mark.require_network("mainnet-fork")
def test_operation(pm, chain):
    dai_liquidity = accounts.at(
        "0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7", force=True
    )  # using curve pool (lots of dai)

    bonus_liquidity = accounts.at(
        "0x7587cAefc8096f5F40ACB83A09Df031a018C66ec", force=True
    )  # comp liquidity

    ticket_liquidity = accounts.at(
        "0x330e75E1F48b1Ee968197cc870511665A4A5a832", force=True
    )  # dai tickets

    rewards = accounts[2]
    gov = accounts[3]
    guardian = accounts[4]
    bob = accounts[5]
    alice = accounts[6]
    strategist = accounts[7]
    tinytim = accounts[8]

    dai = Contract("0x6b175474e89094c44da98b954eedeac495271d0f", owner=gov)  # DAI token

    dai.approve(dai_liquidity, Wei("1000000 ether"), {"from": dai_liquidity})
    dai.transferFrom(dai_liquidity, gov, Wei("300000 ether"), {"from": dai_liquidity})

    # config yvDAI vault.
    Vault = pm(config["dependencies"][0]).Vault
    yDAI = Vault.deploy({"from": gov})
    yDAI.initialize(dai, gov, rewards, "", "")
    yDAI.setDepositLimit(Wei("1000000 ether"))

    uni = Contract(
        "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", owner=gov
    )  # UNI router v2

    wantPool = Contract(
        "0xEBfb47A7ad0FD6e57323C8A42B2E5A6a4F68fc1a", owner=gov
    )  # dai pool

    poolToken = Contract(
        "0x0cec1a9154ff802e7934fc916ed7ca50bde6844e", owner=gov
    )  # POOL token

    bonus = Contract(
        "0xc00e94cb662c3520282e6f5717214004a7f26888", owner=gov
    )  # comp token

    faucet = Contract(
        "0xF362ce295F2A4eaE4348fFC8cDBCe8d729ccb8Eb", owner=gov
    )  # pool token faucet address

    ticket = Contract(
        "0x334cbb5858417aee161b53ee0d5349ccf54514cf", owner=gov
    )  # dai pooltogether ticket

    bonus.approve(bonus_liquidity, Wei("1000000 ether"), {"from": bonus_liquidity})
    bonus.transferFrom(
        bonus_liquidity, gov, Wei("300000 ether"), {"from": bonus_liquidity}
    )

    ticket.approve(ticket_liquidity, Wei("1000000 ether"), {"from": ticket_liquidity})
    ticket.transferFrom(
        ticket_liquidity, gov, Wei("300000 ether"), {"from": ticket_liquidity}
    )

    strategy = guardian.deploy(StrategyDAIPoolTogether, yDAI)
    strategy.initialize(wantPool, poolToken, uni, bonus, faucet, ticket)

    assert strategy.name() == "PoolTogether Dai Stablecoin"

    yDAI.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})

    dai.approve(gov, Wei("1000000 ether"), {"from": gov})
    dai.transferFrom(gov, bob, Wei("1000 ether"), {"from": gov})
    dai.transferFrom(gov, alice, Wei("4000 ether"), {"from": gov})
    dai.transferFrom(gov, tinytim, Wei("10 ether"), {"from": gov})
    dai.approve(yDAI, Wei("1000000 ether"), {"from": bob})
    dai.approve(yDAI, Wei("1000000 ether"), {"from": alice})
    dai.approve(yDAI, Wei("1000000 ether"), {"from": tinytim})

    bonus.approve(uni, Wei("1000000 ether"), {"from": strategy})
    bonus.approve(uni, Wei("1000000 ether"), {"from": gov})
    bonus.approve(gov, Wei("1000000 ether"), {"from": gov})

    poolToken.approve(uni, Wei("1000000 ether"), {"from": strategy})
    poolToken.approve(uni, Wei("1000000 ether"), {"from": gov})
    poolToken.approve(gov, Wei("1000000 ether"), {"from": gov})

    ticket.approve(uni, Wei("1000000 ether"), {"from": strategy})
    ticket.approve(uni, Wei("1000000 ether"), {"from": gov})
    ticket.approve(gov, Wei("1000000 ether"), {"from": gov})

    # depositing DAI to generate crv3 tokens.
    # crv3.approve(crv3_liquidity, Wei("1000000 ether"), {"from": crv3_liquidity})
    # threePool.add_liquidity([Wei("200000 ether"), 0, 0], 0, {"from": gov})
    # giving Gov some shares to mimic profit
    # yCRV3.depositAll({"from": gov})

    # users deposit to vault
    yDAI.deposit(Wei("1000 ether"), {"from": bob})
    yDAI.deposit(Wei("4000 ether"), {"from": alice})
    yDAI.deposit(Wei("10 ether"), {"from": tinytim})

    # a = yDAI.pricePerShare()

    chain.mine(1)

    strategy.harvest({"from": gov})

    assert ticket.balanceOf(strategy) > 0
    chain.sleep(3600 * 24 * 7)
    chain.mine(1)
    a = yDAI.pricePerShare()

    # small profit

    strategy.harvest({"from": gov})
    chain.mine(1)

    # 6 hours for pricepershare to go up
    chain.sleep(2400 * 6)
    chain.mine(1)

    b = yDAI.pricePerShare()

    assert b > a

    strategy.harvest({"from": gov})
    chain.mine(1)

    # 6 hours for pricepershare to go up
    chain.sleep(2400 * 6)
    chain.mine(1)

    c = yDAI.balanceOf(alice)

    yDAI.withdraw(c, alice, 75, {"from": alice})

    assert dai.balanceOf(alice) > 0
    assert dai.balanceOf(bob) == 0
    assert ticket.balanceOf(strategy) > 0

    d = yDAI.balanceOf(bob)
    yDAI.withdraw(d, bob, 75, {"from": bob})

    assert dai.balanceOf(bob) > 0
    assert dai.balanceOf(strategy) == 0

    e = yDAI.balanceOf(tinytim)
    yDAI.withdraw(e, tinytim, 75, {"from": tinytim})

    assert dai.balanceOf(tinytim) > 0
    assert dai.balanceOf(strategy) == 0

    # We should have made profit
    assert yDAI.pricePerShare() > 1e18

    pass

    ##crv3.transferFrom(gov, bob, Wei("100000 ether"), {"from": gov})
    ##crv3.transferFrom(gov, alice, Wei("788000 ether"), {"from": gov})

    # yUSDT.deposit(Wei("100000 ether"), {"from": bob})
    # yUSDT.deposit(Wei("788000 ether"), {"from": alice})

    # strategy.harvest()

    # assert dai.balanceOf(strategy) == 0
    # assert yUSDT3.balanceOf(strategy) > 0
    # assert ycrv3.balanceOf(strategy) > 0
