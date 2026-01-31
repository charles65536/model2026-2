# Run debug inspector for season 1
$ErrorActionPreference = 'Stop'
py "src\sim\debug_replay_inspect.py"
Write-Output "Inspect completed."
