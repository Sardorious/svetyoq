# cleanup-sessions.ps1 — Cowork sessiya papkalarini tozalash
#
# Muammo: har scheduled run C diskda alohida sessiya papkasi yaratadi
# (kuniga ~48 ta). Agent o'sha papkaga ula olmaydi va o'zi tozalay olmaydi —
# shuning uchun tozalash Windows tomonda, shu skript orqali bajariladi.
# Batafsil: cowork_session\90_infra_sessiya_xotirasi_94739a47.md
#
# Ishlatish:
#   .\cleanup-sessions.ps1                 -> 3 kundan eski papkalarni o'chiradi
#   .\cleanup-sessions.ps1 -Days 7         -> 7 kundan eskisini
#   .\cleanup-sessions.ps1 -DryRun         -> faqat ko'rsatadi, o'chirmaydi
#   .\cleanup-sessions.ps1 -Quiet          -> Task Scheduler uchun, faqat xulosa
#
# Xavfsizlik:
#   - joriy (ochiq) sessiya papkasiga tegmaydi — u band bo'lgani uchun
#     o'chmaydi va skript buni xato deb hisoblamaydi;
#   - eng yangi $KeepAtLeast ta papka yoshidan qat'i nazar saqlanadi;
#   - faqat sessiya papkalari ko'riladi, boshqa hech narsa emas.

param(
    [int]$Days = 3,
    [int]$KeepAtLeast = 5,
    [switch]$DryRun,
    [switch]$Quiet
)

$ErrorActionPreference = "Continue"

$Roots = @(
    (Join-Path $env:APPDATA "Claude\local-agent-mode-sessions")
)

function Write-Info($text, $color = "White") {
    if (-not $Quiet) { Write-Host $text -ForegroundColor $color }
}

function Get-FolderSizeMb($path) {
    try {
        $bytes = (Get-ChildItem -LiteralPath $path -Recurse -File -Force -ErrorAction SilentlyContinue |
                  Measure-Object -Property Length -Sum).Sum
        if (-not $bytes) { return 0 }
        return [math]::Round($bytes / 1MB, 1)
    } catch { return 0 }
}

Write-Info "=== Cowork sessiya tozalash ===" "Cyan"
Write-Info ""

$cutoff       = (Get-Date).AddDays(-$Days)
$totalDeleted = 0
$totalFreedMb = 0.0
$totalSkipped = 0

foreach ($root in $Roots) {
    if (-not (Test-Path -LiteralPath $root)) {
        Write-Info "[=] topilmadi: $root" "DarkGray"
        continue
    }

    Write-Info "Papka: $root" "White"

    $all = @(Get-ChildItem -LiteralPath $root -Directory -Force -ErrorAction SilentlyContinue |
             Sort-Object LastWriteTime -Descending)

    if ($all.Count -eq 0) {
        Write-Info "  bo'sh" "DarkGray"
        continue
    }

    # Eng yangi $KeepAtLeast ta — har doim saqlanadi (joriy sessiya shular ichida).
    $candidates = @($all | Select-Object -Skip $KeepAtLeast |
                    Where-Object { $_.LastWriteTime -lt $cutoff })

    Write-Info ("  jami {0} ta papka, nomzod {1} ta ({2} kundan eski)" -f $all.Count, $candidates.Count, $Days) "DarkGray"

    foreach ($dir in $candidates) {
        $sizeMb = Get-FolderSizeMb $dir.FullName
        $age    = [int]((Get-Date) - $dir.LastWriteTime).TotalDays

        if ($DryRun) {
            Write-Info ("  [DryRun] {0}  ({1} kun, {2} MB)" -f $dir.Name, $age, $sizeMb) "Yellow"
            $totalDeleted++
            $totalFreedMb += $sizeMb
            continue
        }

        try {
            Remove-Item -LiteralPath $dir.FullName -Recurse -Force -ErrorAction Stop
            Write-Info ("  [-] {0}  ({1} kun, {2} MB)" -f $dir.Name, $age, $sizeMb) "Green"
            $totalDeleted++
            $totalFreedMb += $sizeMb
        } catch {
            # Odatda: papka band (Cowork ochiq va shu sessiyada ishlayapti).
            Write-Info ("  [!] band, o'tkazib yuborildi: {0}" -f $dir.Name) "DarkYellow"
            $totalSkipped++
        }
    }
}

Write-Info ""
$verb = if ($DryRun) { "o'chirilardi" } else { "o'chirildi" }
$summary = "{0} ta papka {1}, ~{2} MB bo'shadi" -f $totalDeleted, $verb, [math]::Round($totalFreedMb, 1)
if ($totalSkipped -gt 0) { $summary += " ({0} tasi band edi)" -f $totalSkipped }

if ($Quiet) { Write-Output $summary } else { Write-Host $summary -ForegroundColor Cyan }

# C diskdagi qolgan joy
try {
    $drive  = Get-PSDrive -Name C -ErrorAction Stop
    $freeGb = [math]::Round($drive.Free / 1GB, 1)
    if ($Quiet) { Write-Output "C: bo'sh joy $freeGb GB" }
    else { Write-Host "C: bo'sh joy $freeGb GB" -ForegroundColor Cyan }
} catch { }
