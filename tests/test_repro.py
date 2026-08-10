import json

import pytest

from qevc.utils.repro import RunManifest, canonical_json, config_hash, file_sha256


def test_config_hash_deterministic_and_order_invariant():
    a = {"model": "qksvc", "qubits": 8, "nested": {"x": 1, "y": [1, 2]}}
    b = {"nested": {"y": [1, 2], "x": 1}, "qubits": 8, "model": "qksvc"}
    assert config_hash(a) == config_hash(b)
    assert config_hash(a) != config_hash({**a, "qubits": 9})


def test_canonical_json_stable():
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_file_sha256(tmp_path):
    p = tmp_path / "x.bin"
    p.write_bytes(b"qevc")
    assert file_sha256(p) == file_sha256(p)


def test_manifest_write_and_immutability(tmp_path):
    m = RunManifest(experiment_id="E99_test", config={"k": 1}, seed=7)
    m.finalize(outputs=["results/tables/E99.csv"])
    path = m.write(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["experiment_id"] == "E99_test"
    assert data["config_hash"] == config_hash({"k": 1})
    assert len(data["git_commit"]) == 40
    assert data["wall_seconds"] is not None
    with pytest.raises(FileExistsError):
        m.write(tmp_path)
