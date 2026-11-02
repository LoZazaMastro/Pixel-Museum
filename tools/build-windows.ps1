#requires -Version 5.1
param([string]$MsysRoot='C:\msys64',[ValidateSet('Release','RelWithDebInfo','Debug')][string]$Configuration='Release',[int]$Jobs=8)
$ErrorActionPreference='Stop'
$project=Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$prefix=Join-Path $MsysRoot 'mingw64'
$cmake=Join-Path $prefix 'bin\cmake.exe'
if(-not(Test-Path -LiteralPath $cmake)){throw 'Install the documented MinGW-w64 dependencies first (docs/windows-port.md).'}
$env:PATH="$prefix\bin;$MsysRoot\usr\bin;$env:PATH"
$build=Join-Path $project 'build\windows-native'
& $cmake -S $project -B $build -G Ninja "-DCMAKE_BUILD_TYPE=$Configuration" "-DCMAKE_PREFIX_PATH=$prefix" "-DCMAKE_C_COMPILER=$prefix/bin/gcc.exe" "-DCMAKE_CXX_COMPILER=$prefix/bin/g++.exe" "-DCMAKE_RC_COMPILER=$prefix/bin/windres.exe"
if($LASTEXITCODE -ne 0){throw 'Windows configuration failed.'}
& $cmake --build $build --parallel $Jobs
if($LASTEXITCODE -ne 0){throw 'Windows compilation failed.'}
Write-Output (Join-Path $build 'Pixel Museum.exe')
