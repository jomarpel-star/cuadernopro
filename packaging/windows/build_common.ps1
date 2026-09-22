#requires -Version 5.1

function Stop-CheckedTestProcess {
    param([System.Diagnostics.Process]$Process)
    if ($null -eq $Process) { return }
    if (-not $Process.HasExited) { $Process.Kill() }
    if (-not $Process.WaitForExit(20000)) {
        throw "El proceso de prueba $($Process.Id) no ha terminado."
    }
    # Cerrar el handle evita enumerar como vivo un proceso ya terminado.
    $Process.Dispose()
}

function Assert-CuadernoProIdentity {
    param([string]$Path, [string]$Version)
    $Info = (Get-Item -LiteralPath $Path).VersionInfo
    # Inno Setup reserva espacio en estos campos y los rellena con blancos.
    if (([string]$Info.ProductName).Trim() -ne 'CuadernoPro' -or
        ([string]$Info.CompanyName).Trim() -ne 'CuadernoPro' -or
        ([string]$Info.ProductVersion).Trim() -ne $Version) {
        throw "Identidad incorrecta en ${Path}: producto='$($Info.ProductName)', editor='$($Info.CompanyName)', version='$($Info.ProductVersion)'; se esperaba CuadernoPro $Version."
    }
    Write-Host "Identidad Windows verificada: CuadernoPro $Version"
}

function Invoke-CheckedNative {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Program termino con codigo $LASTEXITCODE. Se detiene el build."
    }
}

function Remove-CheckedBuildDirectory {
    param([string]$Path, [string]$RepoRoot)
    $Root = [IO.Path]::GetFullPath($RepoRoot).TrimEnd('\', '/')
    $Target = [IO.Path]::GetFullPath($Path)
    if (-not $Target.StartsWith($Root + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "La limpieza queda fuera del repositorio: $Target"
    }
    # No seguir junctions o enlaces, ni siquiera en un directorio antecesor.
    $Ancestor = $Target
    while ($Ancestor -and $Ancestor -ne $Root) {
        if (Test-Path -LiteralPath $Ancestor) {
            $Item = Get-Item -LiteralPath $Ancestor -Force
            if ($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "No se limpia una ruta con enlaces: $Ancestor"
            }
        }
        $Ancestor = Split-Path -Parent $Ancestor
    }
    if (Test-Path -LiteralPath $Target) {
        $Links = @(Get-ChildItem -LiteralPath $Target -Recurse -Force |
            Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
        if ($Links.Count) { throw "Hay enlaces dentro de $Target; revisar manualmente." }
        Remove-Item -LiteralPath $Target -Recurse -Force
    }
}
