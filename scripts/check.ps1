# Local quality gate. Run before every commit. No CI runs in the cloud.
$ErrorActionPreference = "Stop"

function Step([string]$label, [scriptblock]$run) {
    & $run
    if ($LASTEXITCODE -ne 0) { throw "gate failed: $label" }
}

Step "ruff format" { ruff format --check . }
Step "ruff check" { ruff check . }
Step "mypy" { mypy --strict src tests }
Step "pytest" { pytest }
