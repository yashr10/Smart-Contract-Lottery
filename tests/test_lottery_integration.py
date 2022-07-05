from asyncio import exceptions
from brownie import (
    Lottery,
    accounts,
    config,
    network,
    MockV3Aggregator,
    Contract,
    VRFCoordinatorMock,
    LinkToken,
    interface,
    exceptions,
)
from web3 import Web3
from scripts.deploy_lottery import deploy_lottery
from web3 import Web3
import pytest
import time


def test_can_pick_lottery():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_Account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    #   lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    #  lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_Link(lottery)
    lottery.endLottery({"from": account, "gasPrice": 10000})
    time.sleep(6)
    assert lottery.recentWinner() == account
    assert lottery.balance == 0


# scripts
def deploy_lottery():

    account = get_Account()
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )

    print("deployed")
    return lottery


FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]


def get_Account(index=None, id=None):

    if index:
        return accounts[index]

    if id:
        return accounts.load(id)

    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]
    return accounts.add(config["wallets"]["from_key"])


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_contract(contract_name):
    contract_type = contract_to_mock[contract_name]

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:
            deploy_mocks()
        contract = contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )

    return contract


DECIMAL = 8
INITIAL_VALUE = 200000000000


def deploy_mocks(decimals=DECIMAL, initial_value=INITIAL_VALUE):
    account = get_Account()
    mock_price_feed = MockV3Aggregator.deploy(
        decimals, initial_value, {"from": account}
    )
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})

    print("Deployed!")


def fund_with_Link(
    contract_address, account=None, link_token=None, amount=100000000000000000
):  # 0.1 Link

    account = account if account else get_Account
    link_token = link_token if link_token else get_contract("link_token")
    #  tx = link_token.transfer(contract_address,amount,{"from":account})

    #  link_token_contract = interface.LinkTokenInterface(link_token.address)
    tx = link_token.transfer(contract_address, {"from": account})

    tx.wait(1)
    return tx
