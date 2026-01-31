# Run solver with popularity_reg = 0.1 (and entropy_reg = 0.1, lambda_reg = 1000)
$ErrorActionPreference = 'Stop'

$py = 'py'
$script = 'src\sim\model_main.py'
$panel = 'output\data_cleaned\intermediate_weekly_panel.csv'
$outp = 'src\sim\fan_shares_popularity_0_1.csv'
$outxi = 'src\sim\xi_popularity_0_1.csv'
$args = @($script, '--panel', $panel, '--out-p', $outp, '--out-xi', $outxi, '--alpha', '0.5', '--lambda_reg', '1000', '--entropy-reg', '0.1', '--popularity-reg', '0.1', '--verbose')
$log = 'scripts\run_solver_popularity_0_1.log'

Write-Output "Running: $py $($args -join ' ')"

# Run and capture output and exit code using splatting and Tee-Object
try {
    & $py @args 2>&1 | Tee-Object -FilePath $log
    $rc = $LASTEXITCODE
} catch {
    "Exception invoking $py: $_" | Out-File -FilePath $log -Encoding utf8 -Append
    $rc = $LASTEXITCODE
}

Write-Output "Exit code: $rc"
Write-Output "--- Captured output (first 200 lines) ---"
if (Test-Path $log) { Get-Content $log -TotalCount 200 | ForEach-Object { Write-Output $_ } } else { Write-Output "No log found at $log" }
Write-Output "--- end output ---"

# Check outputs
$files = @($outp, $outxi)
foreach($f in $files){
    if(Test-Path $f){
        $info = Get-Item $f
        Write-Output "$f -> exists, size=$($info.Length) bytes"
    } else {
        Write-Output "$f -> MISSING"
    }
}

if($rc -ne 0){
    Write-Error "Solver exited with code $rc. See $log for details."
} else {
    Write-Output "Solver run (popularity=0.1) completed successfully."
}
