#requires -Version 5.1

function Assert-CuadernoProIdentity {
    param([string]$Path, [string]$Version)
    $Info = (Get-Item -LiteralPath $Path).VersionInfo
    if ($Info.ProductName -ne 'CuadernoPro' -or $Info.CompanyName -ne 'CuadernoPro' -or
        $Info.ProductVersion -ne $Version) {
        throw "Identidad o version incorrecta en el artefacto construido: $Path"
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
