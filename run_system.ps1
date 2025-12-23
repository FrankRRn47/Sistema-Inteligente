Param(
    [switch]$SkipMigrate
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"
$pythonExe = Join-Path $repoRoot ".venv" | Join-Path -ChildPath "Scripts" | Join-Path -ChildPath "python.exe"
$dotenvPath = Join-Path $backendDir ".env"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python executable not found at $pythonExe. Activate/create the venv first." -ErrorAction Stop
}

function Set-EnvFromDotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        Write-Warning "No .env file found at $Path"
        return
    }
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^[#\s]') { return }
        if ($_ -match '^(?<key>[^=\s]+)=(?<value>.*)$') {
            $key = $matches.key.Trim()
            $value = $matches.value.Trim().Trim('"')
            [Environment]::SetEnvironmentVariable($key, $value)
        }
    }
}

Set-EnvFromDotEnv -Path $dotenvPath
$env:PYTHONPATH = $backendDir
$env:FLASK_APP = "app:create_app"
if (-not $env:FLASK_ENV) {
    $env:FLASK_ENV = "development"
}

if (-not $SkipMigrate) {
    Write-Host "Running flask db upgrade..." -ForegroundColor Cyan
    Push-Location $backendDir
    & $pythonExe -m flask db upgrade
    $upgradeExit = $LASTEXITCODE
    Pop-Location
    if ($upgradeExit -ne 0) {
        Write-Error "flask db upgrade failed." -ErrorAction Stop
    }
}

Write-Host "Launching backend server (http://127.0.0.1:5005)..." -ForegroundColor Green
$backendLines = @(
    "Set-Location -LiteralPath '$backendDir'",
    "`$env:PYTHONPATH = '$backendDir'",
    "`$env:FLASK_APP = 'app:create_app'",
    "`$env:FLASK_ENV = '${env:FLASK_ENV}'",
    "`$env:DATABASE_URL = '${env:DATABASE_URL}'",
    "`$env:JWT_SECRET_KEY = '${env:JWT_SECRET_KEY}'",
    "`$env:SECRET_KEY = '${env:SECRET_KEY}'",
    "& '$pythonExe' app.py"
)
$backendScript = $backendLines -join [Environment]::NewLine
Start-Process powershell -ArgumentList "-NoExit","-Command",$backendScript

Write-Host "Launching frontend dev server (http://localhost:3000)..." -ForegroundColor Green
$frontendLines = @(
    "Set-Location -LiteralPath '$frontendDir'",
    "if (-not (Test-Path 'node_modules')) { npm install }",
    "npm start"
)
$frontendScript = $frontendLines -join [Environment]::NewLine
Start-Process powershell -ArgumentList "-NoExit","-Command",$frontendScript

Write-Host "Backend and frontend processes started in new PowerShell windows." -ForegroundColor Yellow
