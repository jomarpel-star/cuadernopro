#requires -Version 5.1
<#
    Build del instalador Windows de CuadernoPro con Inno Setup.

    Genera:
        packaging\windows\output\CuadernoPro-<version>-Setup.exe
#>

param(
    [string]$Python = "python",
    [switch]$Release,
    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$DistWindowsApp = Join-Path $RepoRoot "dist_windows\CuadernoPro"
$ExePath = Join-Path $DistWindowsApp "CuadernoPro.exe"
$TemplatePath = Join-Path $ScriptDir "CuadernoPro.iss.template"
$IssPath = Join-Path $ScriptDir "CuadernoPro.iss"
$OutputDir = Join-Path $ScriptDir "output"
$BrandingIconPath = Join-Path $RepoRoot "assets\branding\cuadernopro.ico"

function Invoke-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "== $Message" -ForegroundColor Cyan
}

function Assert-File {
    param([string]$Path, [string]$Message)

    if (-not (Test-Path $Path)) {
        throw $Message
    }
}

function Confirm-BrandingIcon {
    if (Test-Path $BrandingIconPath -PathType Leaf) {
        Write-Host "Icono Windows/Inno Setup: $BrandingIconPath"
        return
    }

    $Message = (
        "No se encontro assets\branding\cuadernopro.ico. " +
        "El instalador se compilara sin icono personalizado y los accesos " +
        "directos usaran el icono disponible en CuadernoPro.exe. " +
        "Para release, coloque el icono oficial y ejecute con -Release."
    )

    if ($Release) {
        throw "Falta icono de branding obligatorio para release: $BrandingIconPath"
    }

    Write-Warning $Message
}

function Find-InnoSetupCompiler {
    $Candidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )

    foreach ($Candidate in $Candidates) {
        if (Test-Path $Candidate) {
            return (Resolve-Path $Candidate).Path
        }
    }

    $Command = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue

    if ($Command) {
        return $Command.Source
    }

    throw "Instala Inno Setup 6 y vuelve a ejecutar."
}

function Get-CuadernoProVersion {
    $VersionPath = Join-Path $RepoRoot "core\version.py"
    $Content = Get-Content -Raw -Path $VersionPath

    if ($Content -notmatch 'APP_VERSION\s*=\s*"([^"]+)"') {
        throw "No se pudo leer APP_VERSION desde core\version.py"
    }

    return $Matches[1]
}

function Test-ForbiddenInstallerSource {
    param([string]$Path)

    $DistRootFull = [System.IO.Path]::GetFullPath($DistWindowsApp).TrimEnd('\', '/')
    $ArtifactFull = [System.IO.Path]::GetFullPath($Path)
    $RelativePath = $ArtifactFull

    if ($ArtifactFull.StartsWith($DistRootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        $RelativePath = $ArtifactFull.Substring($DistRootFull.Length).TrimStart('\', '/')
    }

    $NormalizedPath = $RelativePath -replace '/', '\'
    $LowerPath = $NormalizedPath.ToLowerInvariant()
    $FileName = [System.IO.Path]::GetFileName($Path)
    $LowerFileName = $FileName.ToLowerInvariant()
    $Extension = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()

    if ($LowerPath -eq "_internal\base_library.zip") {
        return $false
    }

    if ($LowerPath -like "_internal\pyproj\*") {
        return $false
    }

    if ($LowerPath -like "_internal\pyproj.libs\*") {
        return $false
    }

    if ($LowerFileName -eq "cuadernopro.db") {
        return $true
    }

    if ($Extension -in @(".sqlite", ".sqlite3", ".xlsx")) {
        return $true
    }

    if ($Extension -eq ".zip") {
        return $true
    }

    if ($Extension -eq ".db") {
        return $true
    }

    if ($LowerPath -match '^(_internal\\)?(runtime|backups|exports|logs|dist|build)(\\|$)') {
        return $true
    }

    if ($LowerPath -match '^(_internal\\)?documentos\\(facturas|recetas)(\\|$)') {
        return $true
    }

    return $false
}

function Assert-CleanInstallerSource {
    $CandidateFiles = Get-ChildItem $DistWindowsApp -Recurse -Force -File -ErrorAction SilentlyContinue
    $ForbiddenFiles = @($CandidateFiles | Where-Object { Test-ForbiddenInstallerSource $_.FullName })

    if ($ForbiddenFiles) {
        $List = ($ForbiddenFiles | ForEach-Object { $_.FullName }) -join [Environment]::NewLine
        throw "El instalador incluiria ficheros prohibidos:$([Environment]::NewLine)$List"
    }

    foreach ($DirName in @("runtime", "backups", "exports", "logs", "dist", "build")) {
        $Candidate = Join-Path $DistWindowsApp $DirName

        if (Test-Path $Candidate) {
            throw "El instalador incluiria una carpeta prohibida: $Candidate"
        }
    }

    foreach ($DirPath in @("documentos\facturas", "documentos\recetas")) {
        $Candidate = Join-Path $DistWindowsApp $DirPath

        if (Test-Path $Candidate) {
            throw "El instalador incluiria una carpeta de documentos reales: $Candidate"
        }
    }
}

if ($env:OS -ne "Windows_NT") {
    throw "Este build debe ejecutarse en Windows."
}

Invoke-Step "Comprobando branding"
Confirm-BrandingIcon

Invoke-Step "Comprobando Inno Setup"
$IsccExe = Find-InnoSetupCompiler
Write-Host $IsccExe

Invoke-Step "Leyendo version"
$AppVersion = Get-CuadernoProVersion
$OutputExe = Join-Path $OutputDir "CuadernoPro-$AppVersion-Setup.exe"
Write-Host "Version: $AppVersion"

Invoke-Step "Generando portable PyInstaller"
$BuildArgs = @(
    "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $ScriptDir "build_windows.ps1"),
    "-Python", $Python,
    "-Clean",
    "-AppVersion", $AppVersion
)

if ($Release) {
    $BuildArgs += "-Release"
}

& powershell @BuildArgs

Assert-File $ExePath "No existe el ejecutable portable esperado: $ExePath"

Invoke-Step "Validando fuente del instalador"
Assert-CleanInstallerSource
Write-Host "Validacion de fuente de instalador: OK"

Invoke-Step "Generando CuadernoPro.iss"
Assert-File $TemplatePath "No existe la plantilla Inno Setup: $TemplatePath"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$Template = Get-Content -Raw -Path $TemplatePath
$IssContent = $Template.Replace("{{APP_VERSION}}", $AppVersion)
Set-Content -Path $IssPath -Value $IssContent -Encoding UTF8
Write-Host $IssPath

Invoke-Step "Compilando instalador Inno Setup"
Push-Location $ScriptDir
try {
    & $IsccExe $IssPath
}
finally {
    Pop-Location
}

Assert-File $OutputExe "No se genero el instalador esperado: $OutputExe"

Invoke-Step "Resultado"
Write-Host "Instalador Windows: $OutputExe"
