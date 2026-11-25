# COMP4330SEF Group project  
Project group infomation  
Project name: Blockchain for AI prevent data tampering  
Group no: P02_Group03  
Group member:  
Wang Chen Xi 13485478  
Chen Cheuk Ngai 13822291  
HO Yiu Cho Jan 14112868  
Chan Ka Him 14137250  
Ng Man Yau Ian 13170500  
Leung Siu Lei 14196090  

# Project introduction:
This project is going to build a system which uses blockchain to be the security gateway to prevent data tampering and poisoning, only authorized users able to submit, update, remove and delete dataset for model training. To explore the feasibility and effectiveness of using blockchain to enhance AI models' security level.  

Project file intro:  
Data Layer  
-train_data.jsonl: This is the raw data used for fine-tuning the Llama model. It is in JSONL format (where each line is a separate JSON object) and contains an "instruction" (question) and an "output" (answer)  
-hash_dataset.py: Read "train_data.jsonl", calculate a unique hash value (e.g., `0xb69756...`) using the SHA-256 algorithm, and package this hash value along with information such as the contributor ID and dataset version into a file named "dataset_metadata.json".  
-dataset_metadata.json(Auto generate): This is the file generated after running "hash_dataset.py". It contains metadata such as "dataset_hash", "contributor_id", and "version". 

Blockchain Layer  
-DatasetProvenance.sol:This is a snippet of Solidity code. It defines a data structure called "Record" and provides two main functions:  
"recordDataset()": Writes a dataset's hash and metadata to the blockchain (this can be done only once, preventing overwrites).  
"verify()": Allows anyone to check whether a specific hash has already been registered on the blockchain.  
-deploy_contract.py: Compile the ".sol" file using "py-solc-x", then use "web3.py" to connect to a local Anvil blockchain and send a transaction to deploy the contract.  

Integration Layer:  
-train_with_provenance.py: This is the complete workflow, executed in the following sequence:  
1.Anti-Tampering Check: The hash of `train_data.jsonl` is recalculated and compared against the value in `dataset_metadata.json`. If they differ, the program immediately throws an error and terminates (to prevent data poisoning).  
2.Blockchain Interaction: The system connects to Anvil and calls `verify()` to check if the data has already been recorded on the blockchain. If not, it calls `recordDataset()` to commit the hash to the blockchain. The time required for this blockchain operation (overhead) is also measured.  
3.Model Loading: The `unsloth/Llama-3.1-8B-Instruct` model is downloaded from Hugging Face and loaded using 4-bit quantization.  
4.QLoRA Configuration: LoRA parameters are configured; most model weights are frozen, and only a minimal subset of parameters is trained, saving 11 GB of VRAM.  
5.Fine-tuning: The prepared dataset is fed into the model for training, after which the final model is saved.  

# Operation guides  
Hardware and System Requirements:  
GPU: NVIDIA RTX 2080 Ti (11GB VRAM) or higher.(The more VRAM, the better）   
Operating System: Windows 10/11.  
Hugging Face Account: Must be logged in; an Access Token is required.  

Software and Package Installation in terminal  
1. Install PyTorch (Support CUDA 12.4)  
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124  

2. Install AI Training and Blockchain Packages  
pip install transformers datasets peft accelerate bitsandbytes  
pip install web3 py-solc-x  

3. Login Hugging Face  
pip install huggingface_hub  
hf auth login  

Preparing the Blockchain Node (Anvil):  
Please follow the link:https://github.com/foundry-rs/foundry/releases to download the Windows version of Foundry and extract it to obtain "anvil.exe".  
*Click v1.10.0*  
*Choose: foundry_v1.10.0_win32_amd64.zip to download*  

Please ensure that your project folder contains the following 5 core files:    
-DatasetProvenance.sol  
-deploy_contract.py  
-train_data.jsonl  
-hash_dataset.py  
-train_with_provenance.py  

Testing step:  
1.Open a terminal and navigate to the folder containing anvil.exe   
cd C:\foundry_v1.10.0_win32_amd64  
.\anvil.exe  

2.Open another new terminal and navigate to the project folder  
cd "C:\COMP4330_project  
python deploy_contract.py  
python hash_dataset.py  
python train_with_provenance.py  



