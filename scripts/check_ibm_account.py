"""Inspect the IBM Quantum account: instances, plan, backends (dev aid).

Reads the token from the gitignored .env; saves nothing to the repo.
Read-only: no jobs are submitted.
"""

from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService

REPO = Path(__file__).resolve().parents[1]
token = None
for line in (REPO / ".env").read_text().splitlines():
    if line.startswith("IBM_QUANTUM_TOKEN="):
        token = line.split("=", 1)[1].strip()
if not token:
    raise SystemExit("no token in .env")

svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
print("account OK")
try:
    for inst in svc.instances():
        print("instance:", inst)
except Exception as e:  # older API shapes
    print("instances() unavailable:", e)

for b in svc.backends():
    try:
        status = b.status()
        print(f"backend: {b.name}  qubits={b.num_qubits}  "
              f"pending_jobs={status.pending_jobs}  operational={status.operational}")
    except Exception as e:
        print(f"backend: {b.name}  (status error: {e})")
