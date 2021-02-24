import pytest
from brownie import config, Contract


@pytest.fixture
def gov(accounts):
    yield accounts[0]


@pytest.fixture
def rewards(accounts):
    yield accounts[1]


@pytest.fixture
def guardian(accounts):
    yield accounts[2]


@pytest.fixture
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts[4]


@pytest.fixture
def keeper(accounts):
    yield accounts[5]


@pytest.fixture
def alice(accounts):
    yield accounts[6]


@pytest.fixture
def bob(accounts):
    yield accounts[7]


@pytest.fixture
def tinytim(accounts):
    yield accounts[8]


@pytest.fixture
def comp_liquidity(accounts):
    yield accounts.at("0x7587cAefc8096f5F40ACB83A09Df031a018C66ec", force=True)


@pytest.fixture
def comp():
    token_address = "0xc00e94cb662c3520282e6f5717214004a7f26888"
    yield Contract(token_address)


@pytest.fixture
def vault(pm, gov, rewards, guardian, management, comp):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(comp, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    yield vault


@pytest.fixture
def strategy(
    strategist,
    guardian,
    keeper,
    vault,
    StrategyDAIPoolTogether,
    gov,
    want_pool,
    pool_token,
    uni,
    bonus,
    faucet,
    ticket,
):
    strategy = guardian.deploy(StrategyDAIPoolTogether, vault)
    strategy.initialize(want_pool, pool_token, uni, bonus, faucet, ticket)
    strategy.setKeeper(keeper)
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    yield strategy


@pytest.fixture
def uni():
    yield Contract("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")


@pytest.fixture
def want_pool():
    yield Contract("0xBC82221e131c082336cf698F0cA3EBd18aFd4ce7")


@pytest.fixture
def pool_token():
    yield Contract("0x0cec1a9154ff802e7934fc916ed7ca50bde6844e")


@pytest.fixture
def bonus():  # making uni the bonus for this test, since comp is the want
    yield Contract("0x1f9840a85d5af5bf1d1762f925bdaddc4201f984")


@pytest.fixture
def faucet():
    yield Contract("0x72F06a78bbAac0489067A1973B0Cef61841D58BC")


@pytest.fixture
def ticket():
    yield Contract("0x27b85f596feb14e4b5faa9671720a556a7608c69")


@pytest.fixture
def newstrategy(
    strategist,
    guardian,
    keeper,
    vault,
    StrategyDAIPoolTogether,
    gov,
    want_pool,
    pool_token,
    uni,
    bonus,
    faucet,
    ticket,
):
    newstrategy = guardian.deploy(StrategyDAIPoolTogether, vault)
    newstrategy.initialize(want_pool, pool_token, uni, bonus, faucet, ticket)
    newstrategy.setKeeper(keeper)
    yield newstrategy


@pytest.fixture
def ticket_liquidity(accounts):
    yield accounts.at("0x984aaf814012cf15b4b47e9d4d9994092c6c0edc", force=True)


@pytest.fixture
def bonus_liquidity(accounts):  # UNI liquidity
    yield accounts.at("0x5c72ab1005be6452c0417cc0b0c4d549fb7ae6e1", force=True)
