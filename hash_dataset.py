import hashlib, json, os

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

dataset_path = "train_data.jsonl"
dataset_hash = "0x" + sha256_file(dataset_path)

metadata = {
    "dataset_hash": dataset_hash,
    "contributor_id": "student_001",
    "dataset_name": "test_data",
    "version": "1.0",
    "size_bytes": os.path.getsize(dataset_path),
}

with open("dataset_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"✅ 資料集指紋已生成: {dataset_hash}")