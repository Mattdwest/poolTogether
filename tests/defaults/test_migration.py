# TODO: Add tests that show proper migration of the strategy to a newer one
#       Use another copy of the strategy to simulate the migration
#       Show that nothing is lost!


def test_migration(token, vault, strategy, amount, strategist, gov, ticket):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": gov})
    vault.deposit(amount, {"from": gov})
    strategy.harvest({"from": gov})
    assert token.balanceOf(strategy.address) == amount

    # migrate to a new strategy
    new_strategy = strategist.deploy(Strategy, vault)
    strategy.migrate(new_strategy.address, {"from": gov})
    assert token.balanceOf(new_strategy.address) == amount
