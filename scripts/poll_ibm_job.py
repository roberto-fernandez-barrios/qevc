"""Print the current status of the E10 job (dev aid; read-only)."""

import json
from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService

REPO = Path(__file__).resolve().parents[1]
token = None
for line in (REPO / ".env").read_text().splitlines():
    if line.startswith("IBM_QUANTUM_TOKEN="):
        token = line.split("=", 1)[1].strip()

prov = json.loads((REPO / "results/raw/E10_hw/job_provenance.json").read_text())
svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=token,
                           verify=True)
job = svc.job(prov["job_id"])
print(str(job.status()))
