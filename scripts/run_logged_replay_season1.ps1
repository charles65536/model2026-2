# Run logged replay for season 1 and print logs
$ErrorActionPreference = 'Stop'
$py='py'
$script='src\eval\logged_replay_season1.py'
$args = @('--methods','percent,rank','--season','1')
Write-Output "Running: $py $script $($args -join ' ')"
& $py $script $args
Write-Output "Done. Logs written to src/eval/logged_replay_season1_{method}.txt"
