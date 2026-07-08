#requires -Version 5.1
<#
    Prueba inicial del portable Windows.

    Debe ejecutarse despues de build_windows.ps1 en Windows. Usa una carpeta
    temporal de datos mediante CUADERNOPRO_WINDOWS_DATA_ROOT para no tocar datos
    reales de Documents\CuadernoPro.

    Prueba manual complementaria para v8.3.2:
    ejecutar CuadernoPro.exe sin --no-browser, comprobar que abre Edge en modo
    app y confirmar que al cerrar esa ventana no queda CuadernoPro.exe vivo.
#>

param(
    [int]$Port = 18501,
    [int]$TimeoutSeconds = 120,
    [string]$DataRoot = (Join-Path $env:TEMP ("CuadernoProPortableTest_" + [guid]::NewGuid().ToString("N")))
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$ExePath = Join-Path $RepoRoot "dist_windows\CuadernoPro\CuadernoPro.exe"

if ($env:OS -ne "Windows_NT") {
    throw "Esta prueba debe ejecutarse en Windows."
}

if (-not (Test-Path $ExePath)) {
    throw "No existe el ejecutable portable: $ExePath"
}

$ExistingProcesses = @(Get-Process CuadernoPro -ErrorAction SilentlyContinue)

if ($ExistingProcesses.Count -gt 0) {
    $Ids = ($ExistingProcesses | ForEach-Object { $_.Id }) -join ", "
    throw "Hay procesos CuadernoPro previos vivos antes de la prueba: $Ids"
}

$PreviousDataRoot = $env:CUADERNOPRO_WINDOWS_DATA_ROOT
$env:CUADERNOPRO_WINDOWS_DATA_ROOT = $DataRoot
$Process = $null

try {
    New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null
    Write-Host "Datos de prueba: $DataRoot"
    Write-Host "Arrancando: $ExePath"

    $Process = Start-Process -FilePath $ExePath -ArgumentList @(
        "--no-browser",
        "--port", $Port.ToString(),
        "--data-root", $DataRoot
    ) -PassThru
    $Url = "http://127.0.0.1:$Port"
    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $Ready = $false

    while ((Get-Date) -lt $Deadline) {
        if ($Process.HasExited) {
            throw "CuadernoPro.exe termino antes de responder. Codigo: $($Process.ExitCode)"
        }

        try {
            $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3

            if ($Response.StatusCode -eq 200) {
                $Ready = $true
                break
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }

    if (-not $Ready) {
        throw "No se recibio HTTP 200 desde $Url en $TimeoutSeconds segundos."
    }

    foreach ($DirName in @("datos", "documentos", "copias", "exportaciones", "logs")) {
        $Candidate = Join-Path $DataRoot $DirName

        if (-not (Test-Path $Candidate)) {
            throw "No se creo la carpeta esperada: $Candidate"
        }
    }

    Write-Host "Portable OK: $Url"
    Write-Host "Cerrando proceso de prueba: $($Process.Id)"
    Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
    Wait-Process -Id $Process.Id -Timeout 20 -ErrorAction SilentlyContinue
    $Process = $null
}
finally {
    if ($Process -and -not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        Wait-Process -Id $Process.Id -Timeout 20 -ErrorAction SilentlyContinue
    }

    if ($null -eq $PreviousDataRoot) {
        Remove-Item Env:\CUADERNOPRO_WINDOWS_DATA_ROOT -ErrorAction SilentlyContinue
    }
    else {
        $env:CUADERNOPRO_WINDOWS_DATA_ROOT = $PreviousDataRoot
    }

    $RemainingProcesses = @(Get-Process CuadernoPro -ErrorAction SilentlyContinue)

    if ($RemainingProcesses.Count -gt 0) {
        $Ids = ($RemainingProcesses | ForEach-Object { $_.Id }) -join ", "
        throw "Quedan procesos CuadernoPro vivos tras la prueba: $Ids"
    }

    Write-Host "Sin procesos CuadernoPro vivos tras la prueba."
}
