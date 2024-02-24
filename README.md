# Aius Indexer Project

## Description

This project is designed to process blockchain transactions, specifically focusing on managing and identifying unclaimed solutions within the Aius ecosystem. It divides transactions into manageable slots, processes each slot to extract task IDs, and identifies unclaimed solutions.
Basically after running the program successfully which takes a couple minuted, the list of unclaimed solution will be populated in unclaimed_solution.json
## Setup

### Prerequisites

- Python 3.11, maybe lower version will work fine as well
- create virtual environment (`aius_indexer`) 

### Installation

1. Clone the repository:
git clone https://yourrepositorylink.git
cd aius_indexer_project


2. create virtual environment
python3 -m venv aius_indexer
source aius_indexer/bin/activate


3. Install python libraries
pip install -r requirements.txt


4. Create .env.nova if it doesnt exist and add the below environment variables

NOVA_SCAN_API_KEY={your_nova_scan_api_key}

VALIDATOR_ADDRESS={your_validator_address}

NOVA_API_URL=https://api-nova.arbiscan.io/api

ARBIUS_V1_CA=0xadcabea4DFF651F7F87534B617AC77Ab8a0E307c

RPC_URL={your_rpc_url}

START_BLOCK=48538813

END_BLOCK=49826855

SLOT_SIZE=3000


5. run indexer
./run_aius_indexer.sh
