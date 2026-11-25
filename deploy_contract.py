from web3 import Web3
from solcx import compile_source, install_solc

install_solc('0.8.0')

compiled = compile_source(
    open("DatasetProvenance.sol").read(),
    output_values=['abi', 'bin'],
    solc_version='0.8.0'
)
contract_id, contract_interface = compiled.popitem()
abi, bytecode = contract_interface['abi'], contract_interface['bin']

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
account = w3.eth.accounts[0]

Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = Contract.constructor().transact({'from': account})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print("\n✅ 合約部署成功！")
print(f'CONTRACT_ADDRESS = "{tx_receipt.contractAddress}"')
print(f"\nABI = {abi}\n")