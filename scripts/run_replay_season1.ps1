# Run replay simulator for season 1
$ErrorActionPreference = 'Stop'
py "src\sim\replay_simulator.py" --panel "output\data_cleaned\intermediate_weekly_panel.csv" --pest "src\sim\fan_shares_entropy_1.0.csv" --season 1 --alpha 0.5 --methods percent,rank
Write-Output "Replay for season 1 completed."
