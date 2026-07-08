#requires -Version 5.1
<#
    Prueba basica del instalador Windows de CuadernoPro.

    Instala en una carpeta temporal, arranca el ejecutable con data-root
    temporal, comprueba HTTP local y desinstala sin borrar el data-root.
#>

param(
    [int]$Port = 18531,
    [int]$TimeoutSeconds = 120,
    [string]$InstallDir = (Join-Path $env:TEMP ("CuadernoProInstallTest_" + [guid]::NewGuid().ToString("N"))),
    [string]$DataRoot = (Join-Path $env:TEMP ("CuadernoProInstallerData_" + [guid]::NewGuid().ToString("N")))
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

function Get-CuadernoProVersion {
    $VersionPath = Join-Path $RepoRoot "core\version.py"
    $Content = Get-Content -Raw -Path $VersionPath

    if ($Content -notmatch 'APP_VERSION\s*=\s*"([^"]+)"') {
        throw "No se pudo leer APP_VERSION desde core\version.py"
    }

    return $Matches[1]
}

function Invoke-Installer {
    param([string]$FilePath, [string[]]$Arguments)

    $Process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -PassThru -Wait

    if ($Process.ExitCode -ne 0) {
        throw "$FilePath termino con codigo $($Process.ExitCode)"
    }
}

$AppVersion = Get-CuadernoProVersion
$SetupPath = Join-Path $ScriptDir "output\CuadernoPro-$AppVersion-Setup.exe"
$ExePath = Join-Path $InstallDir "CuadernoPro.exe"
$UninstallPath = Join-Path $InstallDir "unins000.exe"
$Process = $null

try {
    if (-not (Test-Path $SetupPath)) {
        throw "No existe el instalador: $SetupPath"
    }

    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null

    Write-Host "Instalador: $SetupPath"
    Write-Host "Carpeta instalacion: $InstallDir"
    Write-Host "Datos de prueba: $DataRoot"

    Invoke-Installer $SetupPath @(
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/SP-",
        "/NOICONS",
        "/DIR=$InstallDir"
    )

    if (-not (Test-Path $ExePath)) {
        throw "No existe CuadernoPro.exe instalado: $ExePath"
    }

    $Process = Start-Process -FilePath $ExePath -ArgumentList @(
        "--debug",
        "--no-browser",
        "--port", $Port.ToString(),
        "--data-root", $DataRoot
    ) -PassThru

    $Url = "http://127.0.0.1:$Port"
    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $Ready = $false
    $HasVersionText = $false

    while ((Get-Date) -lt $Deadline) {
        if ($Process.HasExited) {
            throw "CuadernoPro.exe termino antes de responder. Codigo: $($Process.ExitCode)"
        }

        try {
            $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3

            if ($Response.StatusCode -eq 200) {
                $Ready = $true
                $HasVersionText = ($Response.Content -match "CuadernoPro") -and ($Response.Content -match [regex]::Escape($AppVersion))
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

    if (-not $HasVersionText) {
        Write-Warning "HTTP respondio OK, pero la comprobacion de texto visible requiere prueba manual con navegador."
    }

    Write-Host "Instalador OK: $Url"
}
finally {
    if ($Process -and -not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path $UninstallPath) {
        Invoke-Installer $UninstallPath @(
            "/VERYSILENT",
            "/SUPPRESSMSGBOXES",
            "/NORESTART"
        )
    }

    if (-not (Test-Path $DataRoot)) {
        throw "La carpeta de datos de prueba fue borrada por la desinstalacion: $DataRoot"
    }

    Write-Host "Datos conservados tras desinstalar: $DataRoot"
}
