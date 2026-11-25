import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import json, hashlib, torch, time
from web3 import Web3
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset

MODEL_ID = "unsloth/Llama-3.1-8B-Instruct"
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3" # 稍後如果有變請更新

ABI = [{'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'bytes32', 'name': 'datasetHash', 'type': 'bytes32'}, {'indexed': False, 'internalType': 'string', 'name': 'contributorId', 'type': 'string'}, {'indexed': False, 'internalType': 'uint256', 'name': 'timestamp', 'type': 'uint256'}], 'name': 'ProvenanceRecorded', 'type': 'event'}, {'inputs': [{'internalType': 'bytes32', 'name': '_hash', 'type': 'bytes32'}, {'internalType': 'string', 'name': '_contributorId', 'type': 'string'}, {'internalType': 'string', 'name': '_name', 'type': 'string'}, {'internalType': 'string', 'name': '_version', 'type': 'string'}, {'internalType': 'uint256', 'name': '_size', 'type': 'uint256'}], 'name': 'recordDataset', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'bytes32', 'name': '', 'type': 'bytes32'}], 'name': 'records', 'outputs': [{'internalType': 'bytes32', 'name': 'datasetHash', 'type': 'bytes32'}, {'internalType': 'string', 'name': 'contributorId', 'type': 'string'}, {'internalType': 'uint256', 'name': 'timestamp', 'type': 'uint256'}, {'internalType': 'string', 'name': 'datasetName', 'type': 'string'}, {'internalType': 'string', 'name': 'version', 'type': 'string'}, {'internalType': 'uint256', 'name': 'size', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'bytes32', 'name': '_hash', 'type': 'bytes32'}], 'name': 'verify', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'}]

RPC_URL = "http://127.0.0.1:8545"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
account = w3.eth.accounts[0]

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

start_time = time.time()

metadata = json.load(open("dataset_metadata.json"))
current_hash_hex = "0x" + sha256_file("train_data.jsonl")

if current_hash_hex != metadata["dataset_hash"]:
    raise RuntimeError("❌ 哈希不匹配：資料集在記錄後被篡改，訓練已中止！")

on_chain_hash = w3.to_bytes(hexstr=current_hash_hex)
if not contract.functions.verify(on_chain_hash).call():
    tx = contract.functions.recordDataset(
        on_chain_hash, metadata["contributor_id"], metadata["dataset_name"], metadata["version"], metadata["size_bytes"]
    ).transact({'from': account})
    receipt = w3.eth.wait_for_transaction_receipt(tx)
    chain_status = f"✅ 區塊鏈存證成功，區塊號: {receipt.blockNumber}"
else:
    chain_status = "ℹ️ 數據集已在鏈上記錄"

end_time = time.time()
overhead_time = end_time - start_time

print("\n" + "="*40)
print("🔍 系統完整性驗證與區塊鏈存證")
print("="*40)
print(f"✅ 哈希校驗通過")
print(f"{chain_status}")
print(f"⏱️ 總體 Overhead 耗時: {overhead_time:.4f} 秒 (約 {overhead_time*1000:.2f} 毫秒)")
print("="*40 + "\n")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16, 
    bnb_4bit_use_double_quant=True,
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, quantization_config=bnb_config, device_map="auto", torch_dtype=torch.float16
)
model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM", target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
model = get_peft_model(model, lora_config)

dataset = load_dataset("json", data_files="train_data.jsonl", split="train")

def format_and_tokenize(example):
    text = f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"
    tokenized = tokenizer(text, truncation=True, max_length=1024, padding=False)
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

tokenized_dataset = dataset.map(format_and_tokenize, remove_columns=dataset.column_names)

training_args = TrainingArguments(
    output_dir="./llama31-8b-qlora-provenance",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    num_train_epochs=1,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=1,
    gradient_checkpointing=True,
    optim="paged_adamw_8bit",
    max_grad_norm=1.0,
    report_to="none",
)

trainer = Trainer(model=model, args=training_args, train_dataset=tokenized_dataset)
trainer.train()
trainer.save_model("./llama31-8b-qlora-provenance-final")
print("✅ 微調完成！")