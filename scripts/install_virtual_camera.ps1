param(
    [switch]$SkipPythonPackage,
    [switch]$SkipOBS
)

$ErrorActionPreference = "Stop"

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-RegistryKey {
    param([string]$Path)
    return $null -ne (Get-Item -Path $Path -ErrorAction SilentlyContinue)
}

function Register-ObsVirtualCamera {
    $winDShowPath = Join-Path $env:ProgramFiles "obs-studio\data\obs-plugins\win-dshow"
    $module64 = Join-Path $winDShowPath "obs-virtualcam-module64.dll"
    $module32 = Join-Path $winDShowPath "obs-virtualcam-module32.dll"
    $registry64 = "Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Classes\CLSID\{A3FCE0F5-3493-419F-958A-ABA1250EC20B}"
    $registry32 = "Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Classes\WOW6432Node\CLSID\{A3FCE0F5-3493-419F-958A-ABA1250EC20B}"
    $registered64 = Test-RegistryKey $registry64
    $registered32 = Test-RegistryKey $registry32

    if ($registered64 -and $registered32) {
        Write-Host "[virtual-camera] OBS Virtual Camera is already registered."
        return
    }

    if (-not (Test-Path $module64)) {
        Write-Warning "OBS Virtual Camera module was not found at $module64"
        return
    }

    if (-not (Test-Administrator)) {
        Write-Warning "Administrator rights are required to register OBS Virtual Camera."
        Write-Warning "Re-run this script from an elevated PowerShell, or let the final installer run it elevated."
        return
    }

    Write-Host "[virtual-camera] Registering 64-bit OBS Virtual Camera..."
    & "$env:windir\System32\regsvr32.exe" /i /s $module64

    if (Test-Path $module32) {
        Write-Host "[virtual-camera] Registering 32-bit OBS Virtual Camera..."
        & "$env:windir\SysWOW64\regsvr32.exe" /i /s $module32
    }

    $registered64 = Test-RegistryKey $registry64
    $registered32 = Test-RegistryKey $registry32

    if ($registered64) {
        Write-Host "[virtual-camera] 64-bit OBS Virtual Camera registered."
    }
    else {
        Write-Warning "64-bit OBS Virtual Camera registration was not detected."
    }

    if ($registered32) {
        Write-Host "[virtual-camera] 32-bit OBS Virtual Camera registered."
    }
}

Write-Host "[virtual-camera] Preparing virtual camera support..."

if (-not $SkipPythonPackage) {
    Write-Host "[virtual-camera] Installing Python package pyvirtualcam..."
    python -m pip install "pyvirtualcam>=0.15.0"
}

if (-not $SkipOBS) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($null -eq $winget) {
        Write-Warning "winget was not found. Install OBS Studio manually or bundle a driver in the final installer."
    }
    else {
        Write-Host "[virtual-camera] Installing OBS Studio with winget..."
        winget install --id OBSProject.OBSStudio -e --source winget --accept-source-agreements --accept-package-agreements
    }
}

Register-ObsVirtualCamera

Write-Host ""
Write-Host "[virtual-camera] Next steps:"
Write-Host "1. Start this app."
Write-Host "2. Select OBS Virtual Camera in Discord/browser/Meet/Teams."
Write-Host ""
Write-Host "The app publishes frames automatically by default. Use --no-virtual-camera to disable it."
