GAS_LIMIT=60000000
PROXY="https://devnet-gateway.multiversx.com"
CHAIN_ID="D"
BYTECODE="/Users/stefan/ssi-proiect/contracts/flchain_dummy/output/flchain_dummy.wasm"
WALLET_PEM="/Users/stefan/ssi-proiect/contracts/wallets/wallet2.pem"
PRIMUS_WALLET="/Users/stefan/ssi-proiect/contracts/wallets/primus_wallet.pem"
SECUNDUS_WALLET="/Users/stefan/ssi-proiect/contracts/wallets/secundus_wallet.pem"

WALLETS_DIR="/Users/stefan/ssi-proiect/contracts/flchain_dummy/wallets/"

set_wallet() {
    WALLET_PEM=$1
    echo "Wallet file location is: ${WALLET_PEM}"
}

set_contract() {
    CONTRACT_ADDR=$1
    echo "Smart contract address: ${CONTRACT_ADDR}"
}

set_bytecode() {
    BYTECODE=$1
}

build_contract() {
    mxpy contract build
}

setup_rust_nightly() {
    rustup default nightly-2023-12-11
    rustup target add wasm32-unknown-unknown
}

deploy_contract() {
    mxpy --verbose contract deploy --recall-nonce \
        --bytecode=${BYTECODE} \
        --pem=${WALLET_PEM} \
        --gas-limit=${GAS_LIMIT} \
        --proxy=${PROXY} --chain=${CHAIN_ID} \
        --outfile="deploy-devnet.interaction.json" --send || return

    TRANSACTION=$(mxpy data parse --file="deploy-devnet.interaction.json" --expression="data['emittedTransactionHash']")
    CONTRACT_ADDR=$(mxpy data parse --file="deploy-devnet.interaction.json" --expression="data['contractAddress']")

    mxpy data store --key=address-devnet --value=${CONTRACT_ADDR}
    mxpy data store --key=deployTransaction-devnet --value=${TRANSACTION}

    echo ""
    echo "Smart contract address: ${CONTRACT_ADDR}"
}

upgrade_contract() {
    mxpy --verbose contract upgrade ${CONTRACT_ADDR} --recall-nonce \
        --bytecode=${BYTECODE} \
        --pem=${WALLET_PEM} \
        --gas-limit=${GAS_LIMIT} \
        --proxy=${PROXY} --chain=${CHAIN_ID} \
        --send || return
}

query_contract_get_constant() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function get_constant
}

query_contract_get_deadline() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function getDeadline
}

call_contract_set_ipfs_address() {
    mxpy contract call ${CONTRACT_ADDR} --recall-nonce \
        --pem=${WALLET_PEM} \
        --gas-limit=${GAS_LIMIT} \
        --proxy=${PROXY} --chain=${CHAIN_ID} \
        --function set_ipfs_file --arguments $1 $2 \
        --send
}

query_contract_retrieve_client_id_by_address() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function retrieve_client_id_by_address --arguments $1
}

query_contract_retrieve_address_by_client_id() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function retrieve_address_by_client_id --arguments $1
}

query_genesis_address() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function get_genesis_address
}

query_contract_block_timestamp() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function get_timestamp
}

call_contract_signup_trainer() {
    mxpy contract call ${CONTRACT_ADDR} --recall-nonce \
        --pem=${PRIMUS_WALLET} \
        --gas-limit=${GAS_LIMIT} \
        --proxy=${PROXY} --chain=${CHAIN_ID} \
        --function signup_trainer --arguments $1 \
        --send
}

query_contract_trainers_count() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function trainers_count --arguments $1
}

query_contract_string_vector() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function get_string_vector
}

query_contract_get_boolean() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function get_boolean
}

query_contract_iterate_trainers() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function iterate_trainers --arguments $1
}

call_contract_remove_trainer() {
    mxpy contract call ${CONTRACT_ADDR} --recall-nonce \
        --pem=${PRIMUS_WALLET} \
        --gas-limit=${GAS_LIMIT} \
        --proxy=${PROXY} --chain=${CHAIN_ID} \
        --function remove_trainer --arguments $1 \
        --send
}

call_contract_set_genesis() {
    mxpy contract call ${CONTRACT_ADDR} --recall-nonce \
        --pem=${WALLET_PEM} \
        --gas-limit=${GAS_LIMIT} \
        --proxy=${PROXY} --chain=${CHAIN_ID} \
        --function set_genesis_address --arguments $1 \
        --send
}

create_wallet() {
    mxpy wallet new --format pem --outfile "${WALLETS_DIR}${1}.pem"
}

# Tests

query_is_session_active() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function is_session_active
}

query_get_active_session() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function get_active_session
}

query_is_training_open() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function is_training_open
}

query_is_signup_open() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function is_signup_open
}

query_is_aggregation_open() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function is_aggregation_open
}

query_get_proposer() {
    mxpy contract query ${CONTRACT_ADDR} \
        --proxy=${PROXY}\
        --function get_proposer
}

call_start_session() {
    mxpy contract call ${CONTRACT_ADDR} --recall-nonce \
        --pem=${WALLET_PEM} \
        --gas-limit=${GAS_LIMIT} \
        --proxy=${PROXY} --chain=${CHAIN_ID} \
        --function start_session --arguments $1 $2 $3 $4 \
        --send
}

call_end_session() {
    mxpy contract call ${CONTRACT_ADDR} --recall-nonce \
        --pem=${WALLET_PEM} \
        --gas-limit=${GAS_LIMIT} \
        --proxy=${PROXY} --chain=${CHAIN_ID} \
        --function end_session \
        --send
}