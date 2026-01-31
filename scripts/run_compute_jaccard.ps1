# Run Jaccard computation for survival sets across seasons
$ErrorActionPreference = 'Stop'
$py='py'
$script='src\eval\compute_survival_jaccard.py'
Write-Output "Running: $py $script"
& $py $script
Write-Output "Done. Output: src/eval/jaccard_summary_allseasons.csv and src/eval/jaccard_details_{method}.csv"
