#requires -Version 5.1
<#
    Inventario y control previo a publicar un instalador EXE.
    El modo normal exige firmas confiables. -AuditOnly permite diagnosticar
    un candidato sin firmar; no lo declara apto para publicacion.
#>
param(
    [Parameter(Mandatory=$true)][string]$AppDirectory,
    [Parameter(Mandatory=$true)][string]$InstallerPath,
    [string]$UninstallerPath,
    [string]$ExpectedPublisher,
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'output\auditoria'),
    [switch]$AuditOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$VersionSource = Get-Content -LiteralPath (Join-Path $RepoRoot 'core\version.py') -Raw
if ($VersionSource -notmatch 'APP_VERSION\s*=\s*"(\d+\.\d+\.\d+)"') {
    throw 'No se pudo leer APP_VERSION.'
}
$ExpectedVersion = $Matches[1]
$AppRoot = (Resolve-Path -LiteralPath $AppDirectory).Path.TrimEnd('\', '/')
if (-not (Test-Path -LiteralPath $AppRoot -PathType Container)) { throw 'Falta el portable.' }
$Installer = Get-Item -LiteralPath $InstallerPath
if ($Installer.PSIsContainer -or $Installer.Extension -ne '.exe') { throw 'Falta el instalador EXE.' }
if (-not (Test-Path -LiteralPath (Join-Path $AppRoot 'CuadernoPro.exe') -PathType Leaf)) {
    throw 'Falta CuadernoPro.exe.'
}
$OutputRoot = [IO.Path]::GetFullPath($OutputDirectory).TrimEnd('\', '/')
if ($OutputRoot -eq $AppRoot -or $OutputRoot.StartsWith($AppRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Los informes deben guardarse fuera de la carpeta de la aplicacion.'
}
$Candidates = @(Get-ChildItem -LiteralPath $AppRoot -Recurse -Force)
if (@($Candidates | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) {
    throw 'El portable contiene enlaces o junctions. Revisar antes de distribuir.'
}
$Files = @($Candidates | Where-Object { -not $_.PSIsContainer -and $_.Extension -in '.exe','.dll','.pyd' })
$Inputs = @($Files | ForEach-Object {
    [pscustomobject]@{ Item=$_; Name=('app/' + $_.FullName.Substring($AppRoot.Length + 1).Replace('\','/')); Own=($_.Name -eq 'CuadernoPro.exe') }
})
$Inputs += [pscustomobject]@{Item=$Installer; Name=('installer/' + $Installer.Name); Own=$true}
$Problems = [Collections.Generic.List[string]]::new()
if (-not $ExpectedPublisher) { $Problems.Add('No se ha indicado el firmante esperado del proyecto.') }
if ($UninstallerPath) {
    $Uninstaller = Get-Item -LiteralPath $UninstallerPath
    if ($Uninstaller.PSIsContainer -or $Uninstaller.Extension -ne '.exe') { throw 'Desinstalador incorrecto.' }
    $Inputs += [pscustomobject]@{Item=$Uninstaller; Name='uninstaller/unins000.exe'; Own=$true}
}
else { $Problems.Add('Falta comprobar el desinstalador extraido del instalador final.') }

$Results = @(foreach ($InputFile in $Inputs) {
    $File = $InputFile.Item
    $Signature = Get-AuthenticodeSignature -LiteralPath $File.FullName
    $Certificate = $Signature.SignerCertificate
    $Signer = if ($Certificate) { $Certificate.Subject } else { $null }
    $Rsa = $Certificate -and $Certificate.PublicKey.Oid.Value -eq '1.2.840.113549.1.1.1'
    $Timestamped = $null -ne $Signature.TimeStamperCertificate
    if ($Signature.Status -ne 'Valid' -or -not $Rsa) {
        $Problems.Add("$($InputFile.Name): no tiene firma RSA confiable ($($Signature.Status)).")
    }
    if ($InputFile.Own) {
        if ($ExpectedPublisher -and $Signer -ne $ExpectedPublisher) {
            $Problems.Add("$($InputFile.Name): el firmante no coincide con el del proyecto.")
        }
        if (-not $Timestamped) { $Problems.Add("$($InputFile.Name): falta sello de tiempo.") }
        # Inno Setup asigna al desinstalador su propia version de motor.
        if ($InputFile.Name -notlike 'uninstaller/*') {
            $Metadata = $File.VersionInfo
            if ($Metadata.ProductName -ne 'CuadernoPro' -or $Metadata.CompanyName -ne 'CuadernoPro' -or
                $Metadata.ProductVersion -ne $ExpectedVersion) {
                $Problems.Add("$($InputFile.Name): identidad o version de producto incorrectas.")
            }
        }
    }
    [ordered]@{
        file=$InputFile.Name
        sha256=(Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        signature=[string]$Signature.Status
        signer=$Signer
        rsa=[bool]$Rsa
        timestamped=$Timestamped
        product=$File.VersionInfo.ProductName
        product_version=$File.VersionInfo.ProductVersion
    }
})
$Report = [ordered]@{
    schema_version=1
    app_version=$ExpectedVersion
    checked_at_utc=[DateTime]::UtcNow.ToString('o')
    signature_gate_passed=($Problems.Count -eq 0)
    mode=$(if ($AuditOnly) { 'audit-only' } else { 'require-trusted-signatures' })
    notice='Este informe comprueba firmas e identidad; no sustituye pruebas funcionales, antivirus ni Smart App Control.'
    problems=@($Problems.ToArray())
    files=$Results
}
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$Report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputRoot 'windows-release-audit.json') -Encoding UTF8
$InstallerHash = (Get-FileHash -LiteralPath $Installer.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath (Join-Path $OutputRoot ($Installer.Name + '.sha256')) -Encoding ASCII -Value "$InstallerHash *$($Installer.Name)"
Write-Host "Version: $ExpectedVersion; binarios comprobados: $($Results.Count); incidencias: $($Problems.Count)"
Write-Host "Informe: $(Join-Path $OutputRoot 'windows-release-audit.json')"
if ($Problems.Count) {
    if ($AuditOnly) {
        Write-Warning 'CANDIDATO SIN VALIDAR PARA PUBLICACION. Consultar problems en el informe.'
    }
    else { throw 'PUBLICACION BLOQUEADA: faltan firmas, identidad, sello de tiempo o desinstalador verificado.' }
}
else { Write-Host 'Control de firmas superado. Completar las pruebas funcionales y de Smart App Control.' }
