[CmdletBinding()]
param(
    [string]$OutputDirectory
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $PSScriptRoot "dist"
}

$pluginName = Split-Path -Leaf $PSScriptRoot
$versionFile = Join-Path $PSScriptRoot "jimeng_c4d\__init__.py"
$versionMatch = Select-String -LiteralPath $versionFile -Pattern '^__version__\s*=\s*"([^"]+)"' | Select-Object -First 1

if (-not $versionMatch -or $versionMatch.Matches.Count -eq 0) {
    throw "未能从 $versionFile 读取插件版本号。"
}

$version = $versionMatch.Matches[0].Groups[1].Value
$stagingRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("{0}-release-{1}" -f $pluginName, [Guid]::NewGuid().ToString("N"))
$stagingPlugin = Join-Path $stagingRoot $pluginName

try {
    New-Item -ItemType Directory -Force -Path $stagingPlugin | Out-Null

    # 发行包只保留 C4D 运行插件、内置 Render Settings 预设和安装说明。
    foreach ($item in @("jimeng_c4d_uploader.pyp", "README.md", "jimeng_c4d", "presets")) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $item) -Destination $stagingPlugin -Recurse -Force
    }

    Get-ChildItem -LiteralPath $stagingPlugin -Recurse -Directory -Filter "__pycache__" |
        Remove-Item -Recurse -Force

    New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
    $archivePath = Join-Path $OutputDirectory ("{0}-v{1}.zip" -f $pluginName, $version)
    Compress-Archive -LiteralPath $stagingPlugin -DestinationPath $archivePath -Force

    Write-Output "已创建可安装包：$archivePath"
}
finally {
    if (Test-Path -LiteralPath $stagingRoot) {
        Remove-Item -LiteralPath $stagingRoot -Recurse -Force
    }
}
