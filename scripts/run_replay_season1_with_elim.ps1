# Run replay simulator for season 1 using explicit elim column and verbose output
$ErrorActionPreference = 'Stop'
py "src\sim\replay_simulator.py" --panel "output\data_cleaned\intermediate_weekly_panel.csv" --pest "src\sim\fan_shares_entropy_1.0.csv" --season 1 --alpha 0.5 --methods percent,rank --elim-col true_elim_flag --verbose
Write-Output "Replay for season 1 (with elim_col) completed."
