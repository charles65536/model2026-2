# Run eval replay for all seasons using canonical p_est and compute agreement
$ErrorActionPreference = 'Stop'
$py = 'py'
$script = 'src\eval\replay_simulator.py'
$panel = 'output\data_cleaned\intermediate_weekly_panel.csv'
$pest = 'src\sim\fan_shares_popularity_0_1.csv'
$args = @($script, '--panel', $panel, '--pest', $pest, '--season', 'all', '--alpha', '0.5', '--methods', 'percent,rank', '--elim-col', 'true_elim_flag')
Write-Output "Running replay for all seasons: $py $($args -join ' ')"
& $py @args
Write-Output "Replay complete — computing agreement metrics"
& $py "src\eval\compute_replay_agreement.py"
Write-Output "Done. Agreement CSV at src/eval/replay_agreement_allseasons.csv"
