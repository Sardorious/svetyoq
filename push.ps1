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

# 0b. eskirgan index.lock — yiqilgan git jarayonidan qoladi va hamma narsani bloklaydi
$lock = ".git\index.lock"
if (Test-Path $lock) {
    $lockAge = (Get-Date) - (Get-Item $lock).LastWriteTime
    if ($lockAge.TotalMinutes -gt 10) {
        Write-Host ("[!] Eskirgan .git\index.lock topildi ({0:N0} daqiqa oldin yaratilgan) - o'chirilmoqda." -f $lockAge.TotalMinutes) -ForegroundColor Yellow
        Remove-Item $lock -Force
    } else {
        Write-Host "XATO: .git\index.lock mavjud va yangi. Boshqa git jarayoni ishlayotgan bo'lishi mumkin." -ForegroundColor Red
        Write-Host "Barcha git/editor oynalarini yoping va qayta urinib ko'ring." -ForegroundColor Yellow
        exit 1
    }
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
# Qo'shtirnoq xabardan OLIB TASHLANADI (117-run, 2026-08-12 da yiqildi).
# Sabab: Windows PowerShell 5.1 tashqi dasturga argument uzatayotganda
# satrni qayta qo'shtirnoqqa oladi, lekin ichkaridagi `"` ni ekranlamaydi.
# `aria-label="uz / ru"` bo'lgan xabar git uchun bir necha argumentga
# bo'linib ketdi va `commit` yiqildi. Bitta tirnoq xavfsiz.
$Message = $Message -replace '"', "'"
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
    # commit yiqilgani ikki xil bo'ladi: (a) commit qiladigan narsa yo'q edi -
    # bu normal, davom etamiz; (b) haqiqiy xato - o'zgarishlar joyida qoldi,
    # bunda rebase/push ni davom ettirish mantiqsiz va chalg'ituvchi.
    $left = @(& git status --porcelain)
    if ($left.Count -eq 0) {
        Write-Host "[=] commit qilinadigan yangi narsa yo'q" -ForegroundColor DarkGray
    } else {
        Write-Host ""
        Write-Host "XATO: commit yaratilmadi, o'zgarishlar joyida qoldi." -ForegroundColor Red
        Write-Host "Sababini ko'rish uchun:  git commit -m `"$Message`"" -ForegroundColor Yellow
        exit 1
    }
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
