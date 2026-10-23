$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& node src/server.js @args
exit $LASTEXITCODE
