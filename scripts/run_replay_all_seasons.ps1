# Run replay simulator for all seasons
$ErrorActionPreference = 'Stop'
py "src\sim\replay_simulator.py" --panel "output\data_cleaned\intermediate_weekly_panel.csv" --pest "src\sim\fan_shares_entropy_1.0.csv" --season all --alpha 0.5 --methods percent,rank
Write-Output "Replay for all seasons completed."
