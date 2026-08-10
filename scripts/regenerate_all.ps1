# Clean-tree regeneration campaign (decision D-016, Phase 10 finding 1).
# Re-executes every simulation experiment sequentially from ONE clean commit
# so all manifests record git_dirty: false. Stops on first failure.
# E10 (QPU) is excluded: not re-executable; its provenance stands.
$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"
$steps = @(
    "experiments\E00_dataset_validation\run_e00.py",
    "experiments\E01_nominal_baselines\run_e01.py",
    "experiments\E02_systematic_landscape\run_e02.py",
    "experiments\E02_systematic_landscape\run_e02_multiseed.py",
    "experiments\E03_kernel_geometry\run_e03.py",
    "experiments\E04_geometry_failure\run_e04.py",
    "experiments\E04_geometry_failure\run_e04_v2.py",
    "experiments\E05_conditional_auditing\run_e05.py",
    "experiments\E06_partial_labels\run_e06.py",
    "experiments\E07_active_auditing\run_e07.py",
    "experiments\E08_physics_inference\run_e08.py",
    "experiments\E09_finite_shots\run_e09.py",
    "experiments\E11_cms_real_data\run_e11.py"
)
$dirty = git status --porcelain -- . ":(exclude)results"
if ($dirty) { Write-Output "ABORT: code tree dirty"; Write-Output $dirty; exit 1 }
Write-Output ("CAMPAIGN START at commit " + (git rev-parse HEAD))
foreach ($s in $steps) {
    Write-Output ("STEP START " + $s + " " + (Get-Date -Format HH:mm:ss))
    & $py $s 2>&1 | Select-Object -Last 3 | ForEach-Object { Write-Output ("  " + $_) }
    if ($LASTEXITCODE -ne 0) { Write-Output ("STEP FAILED " + $s); exit 1 }
    Write-Output ("STEP OK " + $s)
}
& $py scripts\make_figures.py 2>&1 | Select-Object -Last 1
& $py scripts\make_fig1.py 2>&1 | Select-Object -Last 1
Write-Output "CAMPAIGN COMPLETE"
