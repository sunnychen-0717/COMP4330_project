pragma solidity ^0.8.0;

contract DatasetProvenance {
    struct Record {
        bytes32 datasetHash;
        string contributorId;
        uint256 timestamp;
        string datasetName;
        string version;
        uint256 size;
    }

    mapping(bytes32 => Record) public records;

    event ProvenanceRecorded(
        bytes32 indexed datasetHash,
        string contributorId,
        uint256 timestamp
    );

    function recordDataset(
        bytes32 _hash,
        string memory _contributorId,
        string memory _name,
        string memory _version,
        uint256 _size
    ) public {
        require(records[_hash].timestamp == 0, "Record already exists");
        records[_hash] = Record({
            datasetHash: _hash,
            contributorId: _contributorId,
            timestamp: block.timestamp,
            datasetName: _name,
            version: _version,
            size: _size
        });
        emit ProvenanceRecorded(_hash, _contributorId, block.timestamp);
    }

    function verify(bytes32 _hash) public view returns (bool) {
        return records[_hash].timestamp != 0;
    }
}