Write-Host "Verifying files for Render deployment..." -ForegroundColor Green

$files = @{
    "requirements.txt" = @(
        "Flask==2.3.3",
        "SQLAlchemy==1.4.50",
        "psycopg2-binary==2.9.9",
        "gunicorn==21.2.0"
    )
    "runtime.txt" = @("python-3.11.8")
    "render.yaml" = @("PYTHON_VERSION", "3.11.8", "pos-database")
    "Procfile" = @("gunicorn", "web_server:app")
}

foreach ($file in $files.Keys) {
    if (Test-Path $file) {
        $content = Get-Content $file -Raw
        Write-Host " $file exists" -ForegroundColor Green
        
        foreach ($check in $files[$file]) {
            if ($content -match $check) {
                Write-Host "    Contains: $check" -ForegroundColor Cyan
            } else {
                Write-Host "    Missing: $check" -ForegroundColor Red
            }
        }
    } else {
        Write-Host " $file missing" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "Files ready for GitHub commit!" -ForegroundColor Green
