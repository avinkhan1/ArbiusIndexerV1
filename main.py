import os
import time
import logging.config

from dotenv import load_dotenv
from config.log_config import LOG_CONFIG

from tx_utils import (
    get_transactions,
    get_task_id,
    claim_solution
)
from io_utils import (
    save_task_ids,
    load_task_ids,
    save_unclaimed_solutions,
    load_block_slots_from_file,
    initialize_block_slots,
    save_block_slots_to_file,
    load_unclaimed_solutions,
    update_block_slots_with_new_range,
)


load_dotenv('.env.nova')

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger()

# Constants
START_BLOCK = int(os.environ.get('START_BLOCK'))
END_BLOCK = int(os.environ.get('END_BLOCK'))
SLOT_SIZE = int(os.environ.get('SLOT_SIZE'))
BLOCK_SLOTS_FILE = 'block_slots.json'

VALIDATOR_ADDRESS = os.environ.get('VALIDATOR_ADDRESS')
PAGE = 1
OFFSET = 10000  # Max value
SORT = "asc"


def manage_blocks_into_slots():
    # Try to load existing block slots data
    block_slots_data = load_block_slots_from_file(BLOCK_SLOTS_FILE)

    # If file doesn't exist, initialize block slots and save to file
    if block_slots_data is None:
        block_slots_data = initialize_block_slots(START_BLOCK, END_BLOCK, SLOT_SIZE)
        save_block_slots_to_file(block_slots_data, BLOCK_SLOTS_FILE)
    else:
        logger.info("Block slots data loaded from file.")
        # Check if the new START_BLOCK and END_BLOCK are within the range
        if START_BLOCK < block_slots_data['start_block'] or END_BLOCK > block_slots_data['end_block']:
            update_block_slots_with_new_range(block_slots_data, START_BLOCK, END_BLOCK, SLOT_SIZE)
            save_block_slots_to_file(block_slots_data, BLOCK_SLOTS_FILE)
            logger.info("Block slots data updated with new range.")

    return block_slots_data


def divide_and_update_slot(block_slots_data, slot_index, slot_size):
    """
    Divide the slot at slot_index into smaller slots if it has too many transactions.
    """
    new_slot_size = slot_size//2
    slot = block_slots_data['slots'][slot_index]
    start_block = slot['first_block']
    end_block = slot['last_block']

    # Remove the original slot
    del block_slots_data['slots'][slot_index]

    # Calculate new slots
    new_slots = []
    for new_start in range(start_block, end_block + 1, new_slot_size):
        new_end = min(new_start + new_slot_size - 1, end_block)
        new_slots.append({
            'slot': len(block_slots_data['slots']) + len(new_slots) + 1,  # Update slot numbers accordingly
            'first_block': new_start,
            'last_block': new_end,
            'status': 'initiated',
            'transactions': 0
        })

    # Insert new slots back into the list
    block_slots_data['slots'][slot_index:slot_index] = new_slots

    # Update slot numbers for all slots
    for i, slot in enumerate(block_slots_data['slots'], start=1):
        slot['slot'] = i

    return new_slot_size


def process_block_slots(block_slots_file='block_slots.json', max_transactions=9900, slot_size=3000):
    try:
        # Load existing block slots and task IDs data
        block_slots_data = load_block_slots_from_file(block_slots_file)

        # Load existing task IDs from file
        task_ids = load_task_ids()
        slots_updated = False

        call_count = 0

        for i, slot in enumerate(block_slots_data.get("slots", [])):
            if slot.get("status") == "initiated":

                START_BLOCK = slot.get("first_block")
                END_BLOCK = slot.get("last_block")

                # Ensure not to exceed the rate limit
                if call_count >= 4:
                    time.sleep(1)  # Wait for 1 second after every 5 calls
                    call_count = 0  # Reset the call count

                # Get the list of transactions
                transactions = get_transactions("txlist", VALIDATOR_ADDRESS, START_BLOCK, END_BLOCK, PAGE, OFFSET, SORT)
                call_count += 1  # Increment the call count

                if len(transactions) > max_transactions:
                    logger.info(f"Slot {slot['slot']} has more than {max_transactions} transactions. Dividing the slot.")
                    new_slot_size = divide_and_update_slot(block_slots_data, i, slot_size)
                    save_block_slots_to_file(block_slots_data, block_slots_file)
                    process_block_slots(block_slots_file, max_transactions, new_slot_size)  # Recursively process the updated slots
                    return  # Exit the current processing as the slots have been updated

                # Process transactions for the current slot
                for tx in transactions:
                    if "submitSolution" in tx.get("functionName") and tx.get("isError") == "0":
                        input_data = tx.get("input")
                        task_id_hex = get_task_id(input_data)
                        if task_id_hex:
                            task_ids['submit_solution'].add(task_id_hex)  # Add new task ID to the submit_solution set
                    elif "claimSolution" in tx.get("functionName") and tx.get("isError") == "0":
                        input_data = tx.get("input")
                        task_id_hex = get_task_id(input_data)
                        if task_id_hex:
                            task_ids['claim_solution'].add(task_id_hex)  # Add new task ID to the claim_solution set

                # Update the slot status to 'processed'
                slot['transactions'] = len(transactions)
                slot['status'] = 'processed'
                slots_updated = True

        # Save the updated dictionary back to the file
        save_task_ids(task_ids)

        # Save the updated block slots data if any slot's status was updated
        if slots_updated:
            save_block_slots_to_file(block_slots_data, block_slots_file)

        logger.info("Updated 'task_ids.json' and 'block_slots.json' with new task IDs and slot statuses.")
    except Exception as e:
        logger.error(f"Error: {e}")


def fetch_unclaimed_solution():
    task_ids = load_task_ids()
    unclaimed_solutions = task_ids['submit_solution'].difference(task_ids['claim_solution'])
    save_unclaimed_solutions(unclaimed_solutions)

    logger.info(f"Updated unclaimed solutions in 'unclaimed_solution.json'.")


def process_task_ids():
    task_ids = load_unclaimed_solutions()  # Load your list of task IDs from the JSON file

    for task_id in list(task_ids):  # Use list() to create a copy of the list for safe iteration
        try:
            success, txn_hash = claim_solution(task_id)

            if success:
                logger.info(f"Successfully processed task ID {task_id} with transaction hash {txn_hash}")
            else:
                logger.info(f"Skipping task ID {task_id} due to an error")

            time.sleep(1)  # Wait for 1 second to update nonce

        except Exception as e:
            logger.error(f"Error claiming solution for task ID {task_id}: {e}")


def main():
    manage_blocks_into_slots()
    process_block_slots()
    fetch_unclaimed_solution()
    process_task_ids()


if __name__ == "__main__":
    main()
