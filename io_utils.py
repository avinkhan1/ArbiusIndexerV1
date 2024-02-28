import json
import os


def initialize_block_slots(start_block, end_block, slot_size):
    slots = []
    total_slots = (end_block - start_block) // slot_size + (1 if (end_block - start_block) % slot_size else 0)

    for slot in range(total_slots):
        first_block = start_block + slot * slot_size
        last_block = min(first_block + slot_size - 1, end_block)
        slots.append({
            'slot': slot + 1,
            'first_block': first_block,
            'last_block': last_block,
            'status': 'initiated',
            'transactions': 0
        })

    block_slots_data = {
        'start_block': start_block,
        'end_block': end_block,
        'slots': slots
    }

    return block_slots_data


def save_block_slots_to_file(block_slots_data, file_path='block_slots.json'):
    with open(file_path, 'w') as file:
        json.dump(block_slots_data, file, indent=4)


def load_block_slots_from_file(file_path='block_slots.json'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        print(f"No existing block slots file found at {file_path}.")
        return None


def update_block_slots_with_new_range(block_slots_data, new_start_block, new_end_block, slot_size):
    existing_start_block = block_slots_data['start_block']
    existing_end_block = block_slots_data['end_block']

    # Update start_block if new_start_block is lower
    if new_start_block < existing_start_block:
        additional_slots_before = initialize_block_slots(new_start_block, existing_start_block - 1, slot_size)['slots']
        block_slots_data['slots'] = additional_slots_before + block_slots_data['slots']
        block_slots_data['start_block'] = new_start_block

    # Update end_block if new_end_block is higher
    if new_end_block > existing_end_block:
        additional_slots_after = initialize_block_slots(existing_end_block + 1, new_end_block, slot_size)['slots']
        block_slots_data['slots'] += additional_slots_after
        block_slots_data['end_block'] = new_end_block

    # Update slot numbers
    for i, slot in enumerate(block_slots_data['slots'], start=1):
        slot['slot'] = i


def load_task_ids(file_path='task_ids.json'):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)
                # Ensure both keys exist and convert their lists back to sets
                data['submit_solution'] = set(data.get('submit_solution', []))
                data['claim_solution'] = set(data.get('claim_solution', []))
                return data
        # Return a dictionary with empty sets if file doesn't exist or is empty
        return {'submit_solution': set(), 'claim_solution': set()}
    except json.JSONDecodeError:
        # Return a dictionary with empty sets if file is empty or invalid
        return {'submit_solution': set(), 'claim_solution': set()}


def save_task_ids(task_ids, file_path='task_ids.json'):
    with open(file_path, 'w') as file:
        # Convert sets to lists for JSON serialization
        data = {
            'submit_solution': list(task_ids['submit_solution']),
            'claim_solution': list(task_ids['claim_solution'])
        }
        json.dump(data, file)


def save_unclaimed_solutions(new_unclaimed_solutions, file_path='unclaimed_solution.json'):
    # Check if the file exists and load existing unclaimed solutions
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                existing_unclaimed_solutions = set(json.load(file))
            except json.JSONDecodeError:
                existing_unclaimed_solutions = set()
    else:
        existing_unclaimed_solutions = set()

    # Update the set with new unclaimed solutions
    updated_unclaimed_solutions = existing_unclaimed_solutions.union(new_unclaimed_solutions)

    # Save the updated set back to the file
    with open(file_path, 'w') as file:
        json.dump(list(updated_unclaimed_solutions), file, indent=4)


def load_unclaimed_solutions():
    # Implement loading logic from your JSON file
    with open('unclaimed_solution.json', 'r') as file:
        return json.load(file)
