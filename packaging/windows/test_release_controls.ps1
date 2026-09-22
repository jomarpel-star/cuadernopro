#requires -Version 5.1
param([string]$Python = 'python')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_common.ps1')
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$TestRoot = Join-Path $RepoRoot ('runtime\windows-release-tests\' + [guid]::NewGuid().ToString('N'))
$AppRoot = Join-Path $TestRoot 'app'
New-Item -ItemType Directory -Path $AppRoot -Force | Out-Null

# Crear un PE minimo con metadatos reales, sin ejecutar ni instalar la app.
$FixtureCode = @'
import pathlib, runpy, shutil, sys
import PyInstaller
from PyInstaller.utils.win32 import versioninfo
repo, output = map(pathlib.Path, sys.argv[1:])
helpers = runpy.run_path(str(repo / 'packaging/windows/version_info.py'))
bootloader = pathlib.Path(PyInstaller.__file__).parent / 'bootloader/Windows-64bit-intel/runw.exe'
exe = output / 'app/CuadernoPro.exe'
shutil.copyfile(bootloader, exe)
versioninfo.write_version_info_to_executable(str(exe), helpers['windows_version_info'](repo))
shutil.copyfile(exe, output / 'Setup.exe')
shutil.copyfile(exe, output / 'unins000.exe')
shutil.copyfile(exe, output / 'app/dependency.pyd')
'@
Invoke-CheckedNative $Python @('-c', $FixtureCode, $RepoRoot, $TestRoot)
$Audit = Join-Path $PSScriptRoot 'audit_windows_release.ps1'
$Options = @{
    AppDirectory=$AppRoot
    InstallerPath=(Join-Path $TestRoot 'Setup.exe')
    UninstallerPath=(Join-Path $TestRoot 'unins000.exe')
    ExpectedPublisher='CN=Test publisher (not trusted)'
    OutputDirectory=(Join-Path $TestRoot 'reports')
}
& $Audit @Options -AuditOnly
$Report = Get-Content -LiteralPath (Join-Path $Options.OutputDirectory 'windows-release-audit.json') -Raw | ConvertFrom-Json
if ($Report.signature_gate_passed -or $Report.files.Count -ne 4) {
    throw 'El control ha aceptado binarios sin firmar o ha omitido una dependencia.'
}
$Main = @($Report.files | Where-Object file -eq 'app/CuadernoPro.exe')[0]
if ($Main.product -ne 'CuadernoPro' -or $Main.product_version -ne $Report.app_version) {
    throw 'Los metadatos Windows no coinciden con la aplicacion.'
}
$Hash = (Get-FileHash -LiteralPath (Join-Path $AppRoot 'CuadernoPro.exe')).Hash.ToLowerInvariant()
if ($Main.sha256 -ne $Hash) { throw 'Hash incorrecto.' }
if (@($Report.files | Where-Object { $_.file -match '^[A-Za-z]:|^/' }).Count) {
    throw 'El informe publica rutas locales absolutas.'
}
$Rejected = $false
try { & $Audit @Options } catch { $Rejected = $true }
if (-not $Rejected) { throw 'El modo de publicacion ha permitido archivos sin firma.' }
$Rejected = $false
try { Invoke-CheckedNative powershell @('-NoProfile', '-NonInteractive', '-Command', 'exit 7') }
catch { $Rejected = $true }
if (-not $Rejected) { throw 'Se ha ignorado un error de la herramienta de build.' }

$Rejected = $false
try { Remove-CheckedBuildDirectory -Path $TestRoot -RepoRoot $AppRoot }
catch { $Rejected = $true }
if (-not $Rejected -or -not (Test-Path -LiteralPath $TestRoot)) {
    throw 'La limpieza ha aceptado una ruta fuera del directorio autorizado.'
}
Write-Host 'OK: metadatos PE, inventario, hashes, rechazo de firmas ausentes, errores de build y limite de limpieza.'
