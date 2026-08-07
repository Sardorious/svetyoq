# setup-git.ps1 — bir martalik sozlash
# Ishga tushirish: PowerShell da shu papkada  ->  .\setup-git.ps1

# git stderr ga yozganda PowerShell uni "xato" deb hisoblamasin
$ErrorActionPreference = "Continue"
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$Repo = "https://github.com/Sardorious/svetyoq.git"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Test-GitOk { return $LASTEXITCODE -eq 0 }

Write-Host "=== Sveta.Net git sozlash ===" -ForegroundColor Cyan
Write-Host "Papka: $Root"

# 1. git bormi
& git --version *> $null
if (-not (Test-GitOk)) {
    Write-Host "XATO: git topilmadi. https://git-scm.com/download/win dan o'rnating." -ForegroundColor Red
    exit 1
}

# 2. init
if (-not (Test-Path ".git")) {
    & git init *> $null
    Write-Host "[+] git init bajarildi" -ForegroundColor Green
} else {
    Write-Host "[=] .git allaqachon mavjud" -ForegroundColor DarkGray
}

# 3. branch
& git branch -M main *> $null
Write-Host "[=] branch: main"

# 4. remote — 'git remote' ro'yxati orqali (stderr chiqmaydi)
$remotes = @(& git remote)
if ($remotes -contains "origin") {
    $existing = (& git remote get-url origin) | Select-Object -First 1
    if ($existing -ne $Repo) {
        & git remote set-url origin $Repo
        Write-Host "[~] remote origin yangilandi: $Repo" -ForegroundColor Yellow
    } else {
        Write-Host "[=] remote origin to'g'ri" -ForegroundColor DarkGray
    }
} else {
    & git remote add origin $Repo
    Write-Host "[+] remote origin qo'shildi: $Repo" -ForegroundColor Green
}

# 5. identifikatsiya (faqat shu repo uchun, global sozlamaga tegmaydi)
$uName = (& git config user.name) | Select-Object -First 1
if (-not $uName) {
    $n = Read-Host "git user.name (Enter -> 'Sardorious')"
    if (-not $n) { $n = "Sardorious" }
    & git config user.name $n
}
$uMail = (& git config user.email) | Select-Object -First 1
if (-not $uMail) {
    $m = Read-Host "git user.email"
    if ($m) { & git config user.email $m }
}

# 6. birinchi commit
& git rev-parse --verify HEAD *> $null
if (-not (Test-GitOk)) {
    & git add -A
    & git commit -m "chore: loyiha hujjatlari va skelet" *> $null
    if (Test-GitOk) {
        Write-Host "[+] birinchi commit yaratildi" -ForegroundColor Green
    } else {
        Write-Host "[!] commit yaratilmadi (o'zgarish yo'q bo'lishi mumkin)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[=] commit tarixi allaqachon bor" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Tayyor. Endi birinchi push:" -ForegroundColor Cyan
Write-Host "    git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "Keyinchalik shunchaki:  .\push.ps1   (yoki push.bat ni ikki marta bosing)" -ForegroundColor Cyan
