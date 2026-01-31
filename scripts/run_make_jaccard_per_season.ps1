# Generate per-season Jaccard CSV
$ErrorActionPreference = 'Stop'
$py='py'
$script='src\eval\make_jaccard_per_season.py'
Write-Output "Running: $py $script"
& $py $script
Write-Output "Done. Output: src/eval/jaccard_per_season.csv"
