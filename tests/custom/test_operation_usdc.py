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
    #dai = usdc for this test

    dai_liquidity = accounts.at(
        "0xa191e578a6736167326d05c119ce0c90849e84b7", force=True
    )  # using

    bonus_liquidity = accounts.at(
        "0x7587cAefc8096f5F40ACB83A09Df031a018C66ec", force=True
    )  # comp liquidity

    ticket_liquidity = accounts.at(
        "0x8a2971ec277ff9ca03ede81f9ae12dc08dcfdf56", force=True
    )  # usdc tickets

    rewards = accounts[2]
    gov = accounts[3]
    guardian = accounts[4]
    bob = accounts[5]
    alice = accounts[6]
    strategist = accounts[7]
    tinytim = accounts[8]

    dai = Contract("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", owner=gov)  # usdc token

    dai.approve(dai_liquidity, 1_000_000_000000, {"from": dai_liquidity})
    dai.transferFrom(dai_liquidity, gov, 300_000_000000, {"from": dai_liquidity})

    # config yvDAI vault.
    Vault = pm(config["dependencies"][0]).Vault
    yDAI = Vault.deploy({"from": gov})
    yDAI.initialize(dai, gov, rewards, "", "")
    yDAI.setDepositLimit(Wei("1000000 ether"))

    uni = Contract(
      "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", owner=gov
    )  # UNI router v2

    wantPool = Contract(
      "0xde9ec95d7708B8319CCca4b8BC92c0a3B70bf416", owner=gov
    )  # usdc pool

    poolToken = Contract(
      "0x0cec1a9154ff802e7934fc916ed7ca50bde6844e", owner=gov
    )  # POOL token

    bonus = Contract(
      "0xc00e94cb662c3520282e6f5717214004a7f26888", owner=gov
    )  # comp token

    faucet = Contract(
      "0xBD537257fAd96e977b9E545bE583bbF7028F30b9", owner=gov
    )  # usdc pool token faucet address

    ticket = Contract(
      "0xd81b1a8b1ad00baa2d6609e0bae28a38713872f7", owner=gov
    )  # usdc pooltogether ticket

    bonus.approve(bonus_liquidity, Wei("1000000 ether"), {"from": bonus_liquidity})
    bonus.transferFrom(bonus_liquidity, gov, Wei("300000 ether"), {"from": bonus_liquidity})

    ticket.approve(ticket_liquidity, 1_000_000_000000, {"from": ticket_liquidity})
    ticket.transferFrom(ticket_liquidity, gov, 300_000_000000, {"from": ticket_liquidity})

    strategy = guardian.deploy(StrategyDAIPoolTogether, yDAI, wantPool, poolToken, uni, bonus, faucet, ticket)
    strategy.setStrategist(strategist)

    yDAI.addStrategy(
        strategy, 10_000, 0,2**256-1, 0, {"from": gov}
    )

    dai.approve(gov, 1_000_000_000000, {"from": gov})
    dai.transferFrom(gov, bob, 1000_000000, {"from": gov})
    dai.transferFrom(gov, alice, 4000_000000, {"from": gov})
    dai.transferFrom(gov, tinytim, 10_000000, {"from":gov})
    dai.approve(yDAI, 1_000_000_000000, {"from": bob})
    dai.approve(yDAI, 1_000_000_000000, {"from": alice})
    dai.approve(yDAI, 1_000_000_000000, {"from": tinytim})

    bonus.approve(uni, Wei("1000000 ether"), {"from": strategy})
    bonus.approve(uni, Wei("1000000 ether"), {"from": gov})
    bonus.approve(gov, Wei("1000000 ether"), {"from": gov})

    poolToken.approve(uni, Wei("1000000 ether"), {"from": strategy})
    poolToken.approve(uni, Wei("1000000 ether"), {"from": gov})
    poolToken.approve(gov, Wei("1000000 ether"), {"from": gov})

    ticket.approve(uni, 1_000_000_000000, {"from": strategy})
    ticket.approve(uni, 1_000_000_000000, {"from": gov})
    ticket.approve(gov, 1_000_000_000000, {"from": gov})

    # depositing DAI to generate crv3 tokens.
    #crv3.approve(crv3_liquidity, Wei("1000000 ether"), {"from": crv3_liquidity})
    #threePool.add_liquidity([Wei("200000 ether"), 0, 0], 0, {"from": gov})
    #giving Gov some shares to mimic profit
    #yCRV3.depositAll({"from": gov})

    # users deposit to vault
    yDAI.deposit(1000_000000, {"from": bob})
    yDAI.deposit(4000_000000, {"from": alice})
    yDAI.deposit(10_000000, {"from": tinytim})

    #a = yDAI.pricePerShare()

    chain.mine(1)

    strategy.harvest({"from": gov})

    assert ticket.balanceOf(strategy) > 0
    chain.sleep(3600*24*7)
    chain.mine(1)
    a = yDAI.pricePerShare()

    # small profit

    strategy.harvest({"from": gov})
    chain.mine(1)

    # 6 hours for pricepershare to go up
    chain.sleep(2400*6)
    chain.mine(1)

    b = yDAI.pricePerShare()

    assert b > a

    strategy.harvest({"from": gov})
    chain.mine(1)

    # 6 hours for pricepershare to go up
    chain.sleep(2400*6)
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
    assert yDAI.pricePerShare() > 1e6

    pass

    ##crv3.transferFrom(gov, bob, Wei("100000 ether"), {"from": gov})
    ##crv3.transferFrom(gov, alice, Wei("788000 ether"), {"from": gov})

    # yUSDT.deposit(Wei("100000 ether"), {"from": bob})
    # yUSDT.deposit(Wei("788000 ether"), {"from": alice})

    # strategy.harvest()

    # assert dai.balanceOf(strategy) == 0
    # assert yUSDT3.balanceOf(strategy) > 0
    # assert ycrv3.balanceOf(strategy) > 0