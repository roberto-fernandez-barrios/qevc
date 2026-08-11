import numpy as np
import pytest

from qevc.geometry.descriptors import psd_violation
from qevc.kernels.quantum import build_feature_map, kernel_exact, kernel_shots

RNG = np.random.default_rng(11)
X = RNG.uniform(-np.pi / 2, np.pi / 2, size=(12, 3))


@pytest.mark.parametrize("ent", ["linear", "full", "none"])
def test_exact_kernel_is_valid_gram(ent):
    fm = build_feature_map(3, reps=2, entanglement=ent)
    K = kernel_exact(X, fm)
    assert K.shape == (12, 12)
    assert np.allclose(K, K.T)
    assert np.allclose(np.diag(K), 1.0)
    assert np.all((K >= -1e-12) & (K <= 1 + 1e-12))
    assert psd_violation(K) < 1e-10


def test_cross_kernel_matches_blocks():
    fm = build_feature_map(3)
    X2 = RNG.uniform(-1, 1, size=(5, 3))
    K_cross = kernel_exact(X, fm, X2)
    assert K_cross.shape == (12, 5)
    K_full = kernel_exact(np.vstack([X, X2]), fm)
    assert np.allclose(K_cross, K_full[:12, 12:], atol=1e-10)


def test_shots_converge_to_exact():
    fm = build_feature_map(3)
    K = kernel_exact(X, fm)
    err_lo = np.abs(kernel_shots(X, fm, shots=64, seed=0) - K).mean()
    err_hi = np.abs(kernel_shots(X, fm, shots=8192, seed=0) - K).mean()
    assert err_hi < err_lo
    assert err_hi < 0.01


def test_low_shots_can_break_psd():
    fm = build_feature_map(3)
    viol = max(
        psd_violation(kernel_shots(X, fm, shots=16, seed=s)) for s in range(5)
    )
    assert viol > 0  # PSD violation is a real, measurable finite-shot effect


def test_shot_estimates_unbiased():
    fm = build_feature_map(2)
    Xs = X[:6, :2]
    K = kernel_exact(Xs, fm)
    est = np.mean(
        [kernel_shots(Xs, fm, shots=256, seed=s) for s in range(200)], axis=0
    )
    assert np.abs(est - K).max() < 0.02


def test_scale_controls_concentration():
    """Larger bandwidth scale spreads angles: off-diagonal mass drops."""
    off = {}
    for scale in (0.25, 1.0, 3.0):
        fm = build_feature_map(3, scale=scale)
        K = kernel_exact(X, fm)
        off[scale] = K[np.triu_indices(12, k=1)].mean()
    assert off[0.25] > off[1.0] > off[3.0]


@pytest.mark.parametrize("ent", ["linear", "full", "none"])
@pytest.mark.parametrize("reps", [1, 2, 3])
def test_fast_simulator_matches_qiskit(ent, reps):
    """The vectorized simulator must reproduce Qiskit kernels exactly."""
    fm = build_feature_map(3, reps=reps, entanglement=ent, scale=0.8)
    K_fast = kernel_exact(X, fm, method="fast")
    K_ref = kernel_exact(X, fm, method="qiskit")
    np.testing.assert_allclose(K_fast, K_ref, atol=1e-10)
    X2 = RNG.uniform(-1, 1, size=(5, 3))
    np.testing.assert_allclose(
        kernel_exact(X, fm, X2, method="fast"),
        kernel_exact(X, fm, X2, method="qiskit"),
        atol=1e-10,
    )


def test_fast_simulator_chunking_consistent():
    from qevc.kernels.quantum import _statevectors_fast

    fm = build_feature_map(3, reps=2)
    V_one = _statevectors_fast(X, fm, chunk=4)
    V_all = _statevectors_fast(X, fm, chunk=10_000)
    np.testing.assert_allclose(np.abs(V_one @ V_all.conj().T),
                               np.abs(V_all @ V_all.conj().T), atol=1e-10)


def test_input_validation():
    fm = build_feature_map(3)
    with pytest.raises(ValueError):
        fm(np.zeros(2))
    with pytest.raises(ValueError):
        build_feature_map(3, entanglement="ring")
    with pytest.raises(ValueError):
        kernel_shots(X, fm, shots=0, seed=1)


def test_qksvc_shot_noise_independent_per_call_but_deterministic():
    """D-022: successive Gram evaluations draw independent noise (like a
    device), while two identically-seeded models remain reproducible."""
    from qevc.models.quantum.qksvc import QKSVC

    rng = np.random.default_rng(3)
    Xtr = rng.uniform(0, 1, size=(30, 3))
    ytr = (rng.random(30) < 0.5).astype(int)
    Xte = rng.uniform(0, 1, size=(10, 3))

    m1 = QKSVC(C=1.0, reps=1, scale=0.5, shots=64, seed=7).fit(Xtr, ytr)
    s_a = m1.scores(Xte)
    s_b = m1.scores(Xte)
    assert not np.allclose(s_a, s_b)  # independent noise per evaluation

    m2 = QKSVC(C=1.0, reps=1, scale=0.5, shots=64, seed=7).fit(Xtr, ytr)
    np.testing.assert_allclose(m2.scores(Xte), s_a)  # same call order -> same
