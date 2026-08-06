# push.ps1 — o'zgarishlarni GitHub ga yuborish
# Ishlatish:
#   .\push.ps1                      -> commit xabari PROGRESS.md dan olinadi
#   .\push.ps1 "o'z xabarim"        -> qo'lda xabar
#   .\push.ps1 -DryRun              -> faqat ko'rsatadi, yubormaydi

param(
    [Parameter(Position = 0)][string]$Message,
    [switch]$DryRun
)

# git stderr ga yozganda PowerShell uni "xato" deb hisoblamasin
$ErrorActionPreference = "Continue"
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Test-GitOk { return $LASTEXITCODE -eq 0 }

Write-Host "=== Sveta.Net push ===" -ForegroundColor Cyan

# 0. tekshiruvlar
& git --version *> $null
if (-not (Test-GitOk)) {
    Write-Host "XATO: git topilmadi." -ForegroundColor Red; exit 1
}
if (-not (Test-Path ".git")) {
    Write-Host "XATO: git sozlanmagan. Avval .\setup-git.ps1 ni ishga tushiring." -ForegroundColor Red; exit 1
}

# 1. o'zgarish bormi
$changes = @(& git status --porcelain)
if ($changes.Count -eq 0) {
    Write-Host "O'zgarish yo'q. Push kerak emas." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "O'zgargan fayllar:" -ForegroundColor White
& git status --short
Write-Host ""

# 2. commit xabari — PROGRESS.md run jurnalidan
if (-not $Message) {
    $progress = Join-Path $Root "sveta\PROGRESS.md"
    if (Test-Path $progress) {
        $lines = Get-Content $progress -Encoding UTF8
        $inLog = $false
        foreach ($line in $lines) {
            if ($line -match "^##\s+Run jurnali") { $inLog = $true; continue }
            if (-not $inLog) { continue }
            if ($line -match "^##\s") { break }
            if ($line -match "^\|" -and $line -notmatch "^\|[\s\-\|]*$" -and $line -notmatch "Sana/vaqt") {
                $cols = @(($line -split "\|") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
                if ($cols.Count -ge 3) { $Message = "$($cols[1]): $($cols[2])" }
                break
            }
        }
    }
}
if (-not $Message) {
    $Message = "wip: " + (Get-Date -Format "yyyy-MM-dd HH:mm")
}
if ($Message.Length -gt 200) { $Message = $Message.Substring(0, 197) + "..." }

Write-Host "Commit xabari:" -ForegroundColor White
Write-Host "  $Message" -ForegroundColor Green
Write-Host ""

if ($DryRun) {
    Write-Host "[DryRun] Hech narsa yuborilmadi." -ForegroundColor Yellow
    exit 0
}

# 3. commit
& git add -A
& git commit -m $Message *> $null
if (Test-GitOk) {
    Write-Host "[+] commit yaratildi" -ForegroundColor Green
} else {
    Write-Host "[!] commit yaratilmadi" -ForegroundColor Yellow
}

# 4. remote bilan sinxronlash (faqat origin/main mavjud bo'lsa)
Write-Host "[~] origin/main tekshirilmoqda..." -ForegroundColor DarkGray
& git fetch origin main *> $null
if (Test-GitOk) {
    & git rev-parse --verify origin/main *> $null
    if (Test-GitOk) {
        & git rebase origin/main
        if (-not (Test-GitOk)) {
            Write-Host ""
            Write-Host "TO'QNASHUV: rebase to'xtadi." -ForegroundColor Red
            Write-Host "Qo'lda hal qiling, keyin:  git rebase --continue ; git push" -ForegroundColor Yellow
            Write-Host "Yoki bekor qilish:         git rebase --abort" -ForegroundColor Yellow
            exit 1
        }
    }
} else {
    Write-Host "[=] origin/main hali yo'q — birinchi push" -ForegroundColor DarkGray
}

# 5. push
& git push -u origin main
if (Test-GitOk) {
    Write-Host ""
    Write-Host "[+] Yuborildi -> https://github.com/Sardorious/svetyoq" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Push bajarilmadi. Kirish huquqini tekshiring (GitHub token / SSH kalit)." -ForegroundColor Red
    exit 1
}
