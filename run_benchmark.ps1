# ===========================================
# run_benchmark.ps1 — запуск бенчмарка с кэшем
# Автоматически находит последний results.csv и передаёт как --cache
# ===========================================

$BenchmarkRoot = "$PSScriptRoot\api_benchmarks"
$Parallel = 4
$BatchSize = 10

# Ищем последний results.csv среди всех папок api_benchmark_*
$LastResultsCsv = Get-ChildItem -Path $BenchmarkRoot -Filter "results.csv" -Recurse |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1 -ExpandProperty FullName

if ($LastResultsCsv) {
    Write-Host "✅ Найден кэш: $LastResultsCsv" -ForegroundColor Green
    $CacheArg = "--cache `"$LastResultsCsv`""
} else {
    Write-Host "⚠️  Кэш не найден — запуск без кэша" -ForegroundColor Yellow
    $CacheArg = ""
}

Write-Host ""
Write-Host "🚀 Запуск бенчмарка..." -ForegroundColor Cyan
Write-Host "   parallel=$Parallel  batch-size=$BatchSize" -ForegroundColor Gray
Write-Host ""

$Cmd = "python `"$PSScriptRoot\backend\benchmarks\api_benchmark.py`" --parallel $Parallel --batch-size $BatchSize $CacheArg"
Write-Host $Cmd -ForegroundColor DarkGray
Write-Host ""

Invoke-Expression $Cmd
