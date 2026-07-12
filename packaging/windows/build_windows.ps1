#requires -Version 5.1
<#
    Build portable de CuadernoPro para Windows sin Docker.

    Ejecutar en Windows desde la raiz del repositorio o desde esta carpeta:

        powershell -ExecutionPolicy Bypass -File packaging\windows\build_windows.ps1

    Este script genera dist_windows\CuadernoPro\CuadernoPro.exe con
    PyInstaller. No genera el instalador Inno Setup final y no debe incluir
    bases, runtime ni documentos reales.
#>

param(
    [string]$Python = "python",
    [string]$AppVersion = "8.3.2",
    [switch]$Clean,
    [switch]$Release,
    [switch]$NoVenv,
    [switch]$SkipInstall,
    [switch]$NoPyInstallerClean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$VenvDir = Join-Path $RepoRoot ".venv-windows"
$PythonExe = $Python
$BuildDir = Join-Path $RepoRoot "build"
$DistRoot = Join-Path $RepoRoot "dist"
$DistWindowsRoot = Join-Path $RepoRoot "dist_windows"
$SpecPath = Join-Path $ScriptDir "CuadernoPro.spec"
$DistWindowsApp = Join-Path $DistWindowsRoot "CuadernoPro"
$ExePath = Join-Path $DistWindowsApp "CuadernoPro.exe"
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
        Write-Host "Icono Windows: $BrandingIconPath"
        return
    }

    $Message = (
        "No se encontro assets\branding\cuadernopro.ico. " +
        "El ejecutable se generara con el icono por defecto. " +
        "Para release, coloque el icono oficial o ejecute con -Release para " +
        "bloquear el build si falta."
    )

    if ($Release) {
        throw "Falta icono de branding obligatorio para release: $BrandingIconPath"
    }

    Write-Warning $Message
}

function Test-ForbiddenBuildArtifact {
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

    if ($LowerPath -match '^(_internal\\)?runtime(\\|$)') {
        return $true
    }

    if ($LowerPath -match '^(_internal\\)?backups(\\|$)') {
        return $true
    }

    if ($LowerPath -match '^(_internal\\)?exports(\\|$)') {
        return $true
    }

    if ($LowerPath -match '^(_internal\\)?dist(\\|$)') {
        return $true
    }

    if ($LowerPath -match '^(_internal\\)?build(\\|$)') {
        return $true
    }

    if ($LowerPath -match '^(_internal\\)?documentos\\facturas(\\|$)') {
        return $true
    }

    if ($LowerPath -match '^(_internal\\)?documentos\\recetas(\\|$)') {
        return $true
    }

    return $false
}

if ($env:OS -ne "Windows_NT") {
    throw "Este build debe ejecutarse en Windows para generar CuadernoPro.exe."
}

Invoke-Step "Comprobando Python"
& $Python --version
where.exe python | Out-Host
where.exe powershell | Out-Host

if (-not $NoVenv) {
    $PythonExe = Join-Path $VenvDir "Scripts\python.exe"

    if (-not (Test-Path $PythonExe)) {
        Invoke-Step "Creando entorno virtual de build"
        & $Python -m venv $VenvDir
    }

    Assert-File $PythonExe "No se encontro Python en el entorno virtual: $PythonExe"
}

if (-not $SkipInstall) {
    Invoke-Step "Instalando dependencias de aplicacion y build"
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -r (Join-Path $RepoRoot "requirements.txt")
    & $PythonExe -m pip install pyinstaller
}

Assert-File (Join-Path $RepoRoot "app.py") "No se encontro app.py"
Assert-File (Join-Path $ScriptDir "cuadernopro_launcher.py") "No se encontro el launcher Windows"
Assert-File $SpecPath "No se encontro el spec de PyInstaller: $SpecPath"

Invoke-Step "Comprobando branding"
Confirm-BrandingIcon

Invoke-Step "Comprobando PyInstaller"
& $PythonExe -m PyInstaller --version
$PyInstallerExe = Join-Path (Split-Path $PythonExe -Parent) "pyinstaller.exe"

if (Test-Path $PyInstallerExe) {
    Write-Host $PyInstallerExe
}
else {
    where.exe pyinstaller 2>$null | Out-Host
}

if ($Clean) {
    Invoke-Step "Limpiando carpetas de build"
    Remove-Item $BuildDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $DistRoot -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $DistWindowsRoot -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $ScriptDir "build") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $ScriptDir "dist") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $ScriptDir "output") -Recurse -Force -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
New-Item -ItemType Directory -Force -Path $DistWindowsRoot | Out-Null

Invoke-Step "Ejecutando PyInstaller"
$PyInstallerArgs = @(
    "--noconfirm",
    "--distpath", $DistWindowsRoot,
    "--workpath", $BuildDir,
    $SpecPath
)

if (-not $NoPyInstallerClean) {
    $PyInstallerArgs = @("--clean") + $PyInstallerArgs
}

& $PythonExe -m PyInstaller @PyInstallerArgs

Assert-File $ExePath "No se genero el ejecutable esperado: $ExePath"

Invoke-Step "Copiando documentacion util"
$DocsOut = Join-Path $DistWindowsApp "docs"
New-Item -ItemType Directory -Force -Path $DocsOut | Out-Null

$Docs = @(
    "LICENSE",
    "DISCLAIMER.md",
    "TRADEMARKS.md",
    "README.md",
    "USO_BASICO.md",
    "GUIA_INSTALACION_SENCILLA.md",
    "AVISO_RESPONSABILIDAD.md",
    "THIRD_PARTY_NOTICES.md",
    "ATRIBUCIONES_DATOS.md"
)

foreach ($Doc in $Docs) {
    $Source = Join-Path $RepoRoot $Doc

    if (Test-Path $Source) {
        Copy-Item $Source -Destination $DocsOut -Force
    }
}

Invoke-Step "Validando que no se incluyen datos reales"
$CandidateFiles = Get-ChildItem $DistWindowsApp -Recurse -Force -File -ErrorAction SilentlyContinue
$ForbiddenFiles = @($CandidateFiles | Where-Object { Test-ForbiddenBuildArtifact $_.FullName })

if ($ForbiddenFiles) {
    $Lista = ($ForbiddenFiles | ForEach-Object { $_.FullName }) -join [Environment]::NewLine
    throw "El build contiene ficheros prohibidos:$([Environment]::NewLine)$Lista"
}

foreach ($DirName in @("runtime", "backups", "exports", "dist", "build")) {
    $Candidate = Join-Path $DistWindowsApp $DirName

    if (Test-Path $Candidate) {
        throw "El build contiene una carpeta de datos que no debe distribuirse: $Candidate"
    }
}

foreach ($DirPath in @("documentos\facturas", "documentos\recetas")) {
    $Candidate = Join-Path $DistWindowsApp $DirPath

    if (Test-Path $Candidate) {
        throw "El build contiene una carpeta de datos que no debe distribuirse: $Candidate"
    }
}

Write-Host "Validación de datos reales: OK"

Invoke-Step "Resultado"
Write-Host "Build portable: $DistWindowsApp"
Write-Host "Ejecutable: $ExePath"
Write-Host "Version indicada para documentacion/manual: $AppVersion"
Write-Host "No se ha generado instalador Inno Setup. Use build_installer_windows.ps1 para ello."
