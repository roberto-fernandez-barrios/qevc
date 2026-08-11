# Best-effort Linux container (D-030) — HONESTY HEADER
#
# The environment of record is Windows + Python 3.13 with the fully pinned
# lockfile (environment/requirements-lock.txt, D-003); this image is a
# best-effort Linux approximation for reviewers without a Windows box.
# Bit-exact reproduction across OS/BLAS is NOT claimed. The scientific
# reproducibility instruments are the immutable run manifests
# (results/manifests/: git commit, config hash, dataset SHA-256, seeds,
# package versions) and the archived result tables.
#
# Build:  docker build -t qevc -f environment/containers/Dockerfile .
# Test:   docker run --rm qevc pytest -q
#   (data-dependent test modules skip unless the FAIR Universe parquet is
#    mounted at /work/data/raw/fair_universe/)

FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
COPY environment/requirements-lock.txt environment/requirements-lock.txt
RUN pip install --no-cache-dir -r environment/requirements-lock.txt || \
    (echo "pinned install failed on Linux — falling back to floors" && \
     pip install --no-cache-dir numpy scipy scikit-learn xgboost lightgbm \
        qiskit qiskit-aer qiskit-machine-learning pyarrow pandas matplotlib \
        pyyaml pytest)

COPY . .
RUN pip install --no-cache-dir -e . --no-deps

CMD ["pytest", "-q"]
