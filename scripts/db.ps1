# Project-local PostgreSQL 17 cluster for development: data in .pgdata/, port 5433,
# listening on 127.0.0.1 only with trust auth, so no superuser password is needed.
param([ValidateSet("start", "stop", "status")][string]$Command = "start")
$ErrorActionPreference = "Stop"

$bin = if ($env:PG_BIN) { $env:PG_BIN } else { "C:\Program Files\PostgreSQL\17\bin" }
$data = Join-Path (Split-Path $PSScriptRoot -Parent) ".pgdata"
$port = 5433

function Invoke-Pg([string]$exe, [string[]]$pgArgs) {
    & (Join-Path $bin $exe) @pgArgs
    if ($LASTEXITCODE -ne 0) { throw "$exe failed with exit code $LASTEXITCODE" }
}

switch ($Command) {
    "start" {
        if (-not (Test-Path (Join-Path $data "PG_VERSION"))) {
            Invoke-Pg "initdb.exe" @("-D", $data, "-U", "proofskill", "--auth=trust", "--encoding=UTF8", "--locale=C")
        }
        & (Join-Path $bin "pg_ctl.exe") -D $data status *> $null
        if ($LASTEXITCODE -ne 0) {
            Invoke-Pg "pg_ctl.exe" @("-D", $data, "-o", "-p $port -h 127.0.0.1", "-l", (Join-Path $data "server.log"), "-w", "start")
        }
        $exists = & (Join-Path $bin "psql.exe") -h 127.0.0.1 -p $port -U proofskill -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'proofskill'"
        if ($exists -ne "1") { Invoke-Pg "createdb.exe" @("-h", "127.0.0.1", "-p", "$port", "-U", "proofskill", "proofskill") }
        Write-Output "PostgreSQL ready: postgresql://proofskill@127.0.0.1:$port/proofskill"
    }
    "stop" { Invoke-Pg "pg_ctl.exe" @("-D", $data, "-w", "stop") }
    "status" { & (Join-Path $bin "pg_ctl.exe") -D $data status }
}
