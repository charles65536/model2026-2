# Run eval replay simulator for season 1 using canonical p_est
$ErrorActionPreference = 'Stop'
$py = 'py'
$script = 'src\eval\replay_simulator.py'
$panel = 'output\data_cleaned\intermediate_weekly_panel.csv'
$pest = 'src\sim\fan_shares_popularity_0_1.csv'
$args = @($script, '--panel', $panel, '--pest', $pest, '--season', 1, '--alpha', '0.5', '--methods', 'percent,rank', '--elim-col', 'true_elim_flag', '--verbose')
Write-Output "Running: $py $($args -join ' ')"
& $py @args
Write-Output "Done. Outputs written to src/eval/"
