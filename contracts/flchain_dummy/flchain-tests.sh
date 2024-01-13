#!/bin/bash

echo "Checking dependencies..."
command -v jq || { echo "jq not found. Installing jq using Homebrew..."; brew install jq; }

CONTRACT_ADDR="erd1qqqqqqqqqqqqqpgq5fqj294099nurngdz9rzgv7du0n6h4vedttshsdl08"

source "/Users/stefan/ssi-proiect/contracts/flchain_dummy/commands/devnet.snippets.sh"

set_contract ${CONTRACT_ADDR}

assess_condition() {
    [ "$1" == true ]
}

ends_with() {
    case $1 in
        *"$2") return 0;;  # String ends with the specified suffix
        *) return 1;;      # String does not end with the specified suffix
    esac
}

should_block_timestamp_increment() {
    first_timestamp=$(query_contract_block_timestamp | jq -r '.[0].number')
    sleep 6
    second_timestamp=$(query_contract_block_timestamp | jq -r '.[0].number')
    assess_condition "$((first_timestamp < second_timestamp))"
}

should_be_active_session_1() {
    error_message=$(query_get_active_session 2>&1 | tail -n 1)
    query_failed_part=$(echo "$error_message" | grep -o "Query failed:.*$")
    [ "$query_failed_part" == "Query failed: No training session available!" ]
}

should_be_signup_open_1() {
    error_message=$(query_is_signup_open 2>&1 | tail -n 1)
    query_failed_part=$(echo "$error_message" | grep -o "Query failed:.*$")
    [ "$query_failed_part" == "Query failed: No training session available!" ]
}

should_be_training_open_1() {
    error_message=$(query_is_training_open 2>&1 | tail -n 1)
    query_failed_part=$(echo "$error_message" | grep -o "Query failed:.*$")
    [ "$query_failed_part" == "Query failed: No training session available!" ]
}

should_be_aggregation_open_1() {
    error_message=$(query_is_aggregation_open 2>&1 | tail -n 1)
    query_failed_part=$(echo "$error_message" | grep -o "Query failed:.*$")
    [ "$query_failed_part" == "Query failed: No training session available!" ]
}



# should_block_timestamp_increment && echo "[✅] Test: should_block_timestamp_increment" || echo "[❌] Test: should_block_timestamp_increment"
should_be_active_session_1 && echo "[✅] Test: should_be_active_session_1" || echo "[❌] Test: should_be_active_session_1"
should_be_signup_open_1 && echo "[✅] Test: should_be_signup_open_1" || echo "[❌] Test: should_be_signup_open_1"
should_be_training_open_1 && echo "[✅] Test: should_be_training_open_1" || echo "[❌] Test: should_be_training_open_1"
should_be_aggregation_open_1 && echo "[✅] Test: should_be_aggregation_open_1" || echo "[❌] Test: should_be_aggregation_open_1"

# run_tests() {
#     successful_tests=0
#     failed_tests=0

#     # Run and count successful tests
#     test_function1 && ((successful_tests++)) || ((failed_tests++))
#     test_function2 && ((successful_tests++)) || ((failed_tests++))
#     test_function3 && ((successful_tests++)) || ((failed_tests++))

#     # Display results
#     echo "Total tests: $((successful_tests + failed_tests))"
#     echo "Successful tests: $successful_tests"

#     if [ "$failed_tests" -gt 0 ]; then
#         echo "Failed tests:"
#         test_function1 || echo "  - Test 1"
#         test_function2 || echo "  - Test 2"
#         test_function3 || echo "  - Test 3"
#     fi
# }