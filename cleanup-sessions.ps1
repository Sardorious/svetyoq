# cleanup-sessions.ps1 - Cowork sessiya papkalarini tozalash
#
# Muammo: har scheduled run C diskda alohida sessiya papkasi yaratadi
# (kuniga ~48 ta). Agent o'sha papkaga ula olmaydi va o'zi tozalay olmaydi -
# shuning uchun tozalash Windows tomonda, shu skript orqali bajariladi.
# Batafsil: cowork_session\90_infra_sessiya_xotirasi_94739a47.md
#
# ==========================================================================
# 2026-08-19 (166-run) - SKRIPT TUZATILDI. Oldingi versiya HECH QACHON
# hech narsa o'chira olmasdi, ikkita mustaqil sabab bilan:
#
#   1. U "Get-ChildItem -Directory" ni ILDIZDA chaqirardi, sessiya
#      papkalari esa uch qavat pastda yotadi:
#         <ildiz>\<space-guid>\<project-guid>\local_<sessiya-guid>\
#      Ildizda esa bor-yo'g'i bitta-ikkita <space-guid> bor. Ya'ni
#      "Select-Object -Skip 5" dan keyin nomzodlar ro'yxati DOIM bo'sh
#      qolardi - yo'l to'g'ri bo'lganda ham.
#
#   2. 140-run da odam "[=] topilmadi: ..." xabarini oldi. Yo'lning o'zi
#      to'g'ri ($env:APPDATA\Claude\local-agent-mode-sessions), lekin
#      $env:APPDATA skript kim nomidan yurgizilganiga bog'liq: elevated
#      ("Administrator nomidan") PowerShell da u boshqa profilga ishora
#      qiladi va papka topilmaydi. Endi skript ildizni bir nechta
#      nomzoddan qidiradi va topgan/topmaganini ochiq yozadi.
#
# ==========================================================================
# MUHIM - FAYL FAQAT ASCII BELGILARDAN IBORAT. O'zgartirganda ham shunday
# qoldiring. Sabab: Windows PowerShell 5.1 .ps1 faylni BOM siz bo'lsa ANSI
# (bu mashinada CP1251) deb o'qiydi. UTF-8 dagi uzun tire (E2 80 94) o'shanda
# uchta belgiga aylanadi va ularning oxirgisi (0x94) - "aqlli qo'shtirnoq",
# PowerShell esa uni HAQIQIY qo'shtirnoq deb qabul qiladi. Natijada satr
# vaqtidan oldin yopiladi va butun fayl "MissingEndCurlyBrace" bilan
# yiqiladi. Aynan shu 166-runda sodir bo'ldi. Uzun tire, tirnoqcha,
# emoji - hech biri ishlatilmaydi.
# ==========================================================================
#
# Ishlatish:
#   .\cleanup-sessions.ps1 -Report          -> hech narsa o'chirmaydi,
#                                              joy qayerda ketganini ko'rsatadi
#   .\cleanup-sessions.ps1 -DryRun          -> nima o'chirilishini ko'rsatadi
#   .\cleanup-sessions.ps1                  -> 3 kundan eski sessiyalarni o'chiradi
#   .\cleanup-sessions.ps1 -Days 1          -> 1 kundan eskisini
#   .\cleanup-sessions.ps1 -Quiet           -> Task Scheduler uchun, faqat xulosa
#
# Xavfsizlik:
#   - joriy (ochiq) sessiya papkasi band bo'lgani uchun o'chmaydi va
#     skript buni xato deb hisoblamaydi;
#   - eng yangi $KeepAtLeast ta sessiya yoshidan qat'i nazar saqlanadi;
#   - faqat nomi "local_" bilan boshlanadigan papkalar ko'riladi;
#     skills-plugin, spaces, sozlamalar va boshqa hech narsa emas.

param(
    [int]$Days = 3,
    [int]$KeepAtLeast = 5,
    [switch]$DryRun,
    [switch]$Report,
    [switch]$Quiet
)

$ErrorActionPreference = "Continue"

function Write-Info($text, $color = "White") {
    if (-not $Quiet) { Write-Host $text -ForegroundColor $color }
}

function Get-FolderSizeMb($path) {
    try {
        $bytes = (Get-ChildItem -LiteralPath $path -Recurse -File -Force -ErrorAction SilentlyContinue |
                  Measure-Object -Property Length -Sum).Sum
        if (-not $bytes) { return 0.0 }
        return [math]::Round($bytes / 1MB, 1)
    } catch {
        return 0.0
    }
}

# --------------------------------------------------------------------------
# Ildizni topish. $env:APPDATA elevated seansda boshqa profilga ishora
# qilishi mumkin - shuning uchun bir nechta nomzod tekshiriladi.
# --------------------------------------------------------------------------

$candidateRoots = New-Object System.Collections.Generic.List[string]

if ($env:APPDATA) {
    $candidateRoots.Add((Join-Path $env:APPDATA "Claude\local-agent-mode-sessions"))
}
if ($env:USERPROFILE) {
    $candidateRoots.Add((Join-Path $env:USERPROFILE "AppData\Roaming\Claude\local-agent-mode-sessions"))
}

$userDirs = @(Get-ChildItem -LiteralPath "C:\Users" -Directory -Force -ErrorAction SilentlyContinue)
foreach ($userDir in $userDirs) {
    $candidateRoots.Add((Join-Path $userDir.FullName "AppData\Roaming\Claude\local-agent-mode-sessions"))
}

# --------------------------------------------------------------------------
# HAQIQIY YO'L (166-run da topildi). Claude Desktop - Store/MSIX ilovasi,
# ya'ni uning "AppData\Roaming\Claude" ga yozgani VIRTUALLASHTIRILADI:
# ilova o'sha yo'lni ko'radi, fayllar esa aslida shu yerda yotadi:
#
#   %LOCALAPPDATA%\Packages\Claude_<paket-id>\LocalCache\Roaming\Claude\
#                                            local-agent-mode-sessions\
#
# Shu mashinada: Claude_pzs8sxrjxfjjc. Paket id o'zgarishi mumkin, shuning
# uchun "Claude*" shabloni bilan qidiriladi.
#
# ANA SHU 122-rundan beri "papka topilmadi" degan xabarning butun sababi:
# skript to'g'ri profilga qarardi, lekin virtual yo'lga emas.
# --------------------------------------------------------------------------

$packageParents = @()
if ($env:LOCALAPPDATA) { $packageParents += (Join-Path $env:LOCALAPPDATA "Packages") }
foreach ($userDir in $userDirs) {
    $packageParents += (Join-Path $userDir.FullName "AppData\Local\Packages")
}

foreach ($packageParent in ($packageParents | Sort-Object -Unique)) {
    if (-not (Test-Path -LiteralPath $packageParent)) { continue }
    $claudePackages = @(Get-ChildItem -LiteralPath $packageParent -Directory -Force -ErrorAction SilentlyContinue |
                        Where-Object { $_.Name -like "Claude*" })
    foreach ($claudePackage in $claudePackages) {
        $candidateRoots.Add((Join-Path $claudePackage.FullName "LocalCache\Roaming\Claude\local-agent-mode-sessions"))
    }
}

$allCandidates = @($candidateRoots | Sort-Object -Unique)
$roots = @($allCandidates | Where-Object { Test-Path -LiteralPath $_ })

Write-Info "=== Cowork sessiya tozalash ===" "Cyan"
Write-Info ""

if ($roots.Count -eq 0) {
    Write-Info "[!] Sessiya ildizi topilmadi. Tekshirilgan yo'llar:" "Red"
    foreach ($candidate in $allCandidates) {
        Write-Info "      $candidate" "DarkGray"
    }

    # ----------------------------------------------------------------------
    # Diagnostika. 166-run: Cowork agenti fayllarni
    # C:\Users\5\AppData\Roaming\Claude\local-agent-mode-sessions\... da
    # ko'radi, bu skript esa o'sha yerda hech narsa topmadi. Ya'ni taxmin
    # qilish mumkin emas - qaysi bo'g'inda uzilganini ko'rsatish kerak.
    # ----------------------------------------------------------------------

    Write-Info ""
    Write-Info "--- Diagnostika ---" "Cyan"
    Write-Info ("  USERNAME     : {0}" -f $env:USERNAME) "DarkGray"
    Write-Info ("  COMPUTERNAME : {0}" -f $env:COMPUTERNAME) "DarkGray"
    Write-Info ("  APPDATA      : {0}" -f $env:APPDATA) "DarkGray"
    Write-Info ("  LOCALAPPDATA : {0}" -f $env:LOCALAPPDATA) "DarkGray"
    Write-Info ("  USERPROFILE  : {0}" -f $env:USERPROFILE) "DarkGray"

    # Zanjir qayerda uziladi?
    if ($env:APPDATA) {
        Write-Info ""
        Write-Info "  Yo'l zanjiri (qaysi bo'g'inda uziladi):" "White"
        $chain = @(
            $env:APPDATA,
            (Join-Path $env:APPDATA "Claude"),
            (Join-Path $env:APPDATA "Claude\local-agent-mode-sessions")
        )
        foreach ($link in $chain) {
            if (Test-Path -LiteralPath $link) {
                Write-Info ("    [+] {0}" -f $link) "Green"
            } else {
                Write-Info ("    [-] {0}" -f $link) "Red"
            }
        }

        $claudeDir = Join-Path $env:APPDATA "Claude"
        if (Test-Path -LiteralPath $claudeDir) {
            Write-Info ""
            Write-Info "  Claude papkasi ichida nima bor:" "White"
            $inside = @(Get-ChildItem -LiteralPath $claudeDir -Force -ErrorAction SilentlyContinue |
                        Select-Object -First 25)
            if ($inside.Count -eq 0) {
                Write-Info "    (bo'sh yoki o'qib bo'lmadi)" "DarkGray"
            } else {
                foreach ($entry in $inside) {
                    Write-Info ("    {0}" -f $entry.Name) "DarkGray"
                }
            }
        }
    }

    # Butun profil bo'ylab qidiruv - papka boshqa joyda bo'lishi mumkin
    # (Store/MSIX virtualizatsiyasi, boshqa profil va h.k.).
    Write-Info ""
    Write-Info "  Qidirilmoqda (bir necha daqiqa ketishi mumkin)..." "Yellow"

    # Chuqurlik ATAYLAB cheklangan. Sabab ikkita:
    #   1. AppData ichida o'ziga qaytadigan junction lar bor
    #      (masalan "Application Data") - cheklovsiz -Recurse ularda
    #      MAX_PATH gacha aylanib yuradi;
    #   2. Store/MSIX virtualizatsiyasida papka
    #      AppData\Local\Packages\<paket>\LocalCache\Roaming\Claude\...
    #      da yotadi, ya'ni profildan ~7 qavat ichkarida.
    $searchRoots = @()
    if ($env:LOCALAPPDATA) {
        $searchRoots += (Join-Path $env:LOCALAPPDATA "Packages")
        $searchRoots += $env:LOCALAPPDATA
    }
    if ($env:APPDATA)     { $searchRoots += $env:APPDATA }
    if ($env:USERPROFILE) { $searchRoots += $env:USERPROFILE }
    $searchRoots += "C:\Users\5\AppData\Local\Packages"
    $searchRoots += "C:\Users\5\AppData\Local"
    $searchRoots += "C:\Users\5\AppData\Roaming"

    $found = @()
    foreach ($searchRoot in ($searchRoots | Sort-Object -Unique)) {
        if (-not (Test-Path -LiteralPath $searchRoot)) { continue }
        Write-Info ("    ... {0}" -f $searchRoot) "DarkGray"
        $found += @(Get-ChildItem -LiteralPath $searchRoot -Directory -Recurse -Depth 7 -Force -ErrorAction SilentlyContinue |
                    Where-Object { $_.Name -eq "local-agent-mode-sessions" })
    }
    $found = @($found | Sort-Object FullName -Unique)

    if ($found.Count -eq 0) {
        Write-Info "  [!] Butun profilda 'local-agent-mode-sessions' topilmadi." "Red"
        Write-Info "      Ya'ni Cowork sessiyalari bu mashinada emas yoki" "Yellow"
        Write-Info "      boshqa foydalanuvchi nomidan ishlayapti." "Yellow"
    } else {
        Write-Info "  [+] TOPILDI:" "Green"
        foreach ($hit in $found) {
            Write-Info ("      {0}" -f $hit.FullName) "Green"
        }
        Write-Info "      Shu yo'lni skriptga qo'shish kerak." "Yellow"
    }

    return
}

$cutoff       = (Get-Date).AddDays(-$Days)
$totalDeleted = 0
$totalFreedMb = 0.0
$totalSkipped = 0

foreach ($root in $roots) {
    Write-Info "Ildiz: $root" "White"

    # Sessiya papkalari: <ildiz>\<space>\<project>\local_<guid>
    # Depth 3 - zaxira bilan; nomi bo'yicha filtr aniqlaydi.
    $sessions = @(
        Get-ChildItem -LiteralPath $root -Directory -Recurse -Depth 3 -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "local_*" } |
        Sort-Object LastWriteTime -Descending
    )

    if ($sessions.Count -eq 0) {
        Write-Info "  local_* papkasi yo'q" "DarkGray"
        continue
    }

    # ------------------------------------------------------------- Report
    if ($Report) {
        Write-Info "  (hajm sanalmoqda - yuzlab sessiyada bir necha daqiqa ketishi mumkin)" "DarkGray"

        $sized = foreach ($dir in $sessions) {
            [pscustomobject]@{
                Name   = $dir.Name
                SizeMb = (Get-FolderSizeMb $dir.FullName)
                Age    = [int]((Get-Date) - $dir.LastWriteTime).TotalDays
            }
        }

        $totalMb = ($sized | Measure-Object -Property SizeMb -Sum).Sum
        if (-not $totalMb) { $totalMb = 0.0 }

        $oldest = $sessions[$sessions.Count - 1].LastWriteTime
        $newest = $sessions[0].LastWriteTime

        Write-Info ("  jami {0} ta sessiya, ~{1} MB" -f $sessions.Count, [math]::Round($totalMb, 1)) "Cyan"
        Write-Info ("  eng eskisi: {0:yyyy-MM-dd}   eng yangisi: {1:yyyy-MM-dd}" -f $oldest, $newest) "DarkGray"

        Write-Info "  eng katta o'nta:" "White"
        $biggest = @($sized | Sort-Object SizeMb -Descending | Select-Object -First 10)
        foreach ($item in $biggest) {
            Write-Info ("    {0,9:N1} MB  {1,4} kun  {2}" -f $item.SizeMb, $item.Age, $item.Name) "DarkGray"
        }

        $stale = @($sized | Where-Object { $_.Age -ge $Days })
        $staleMb = ($stale | Measure-Object -Property SizeMb -Sum).Sum
        if (-not $staleMb) { $staleMb = 0.0 }
        Write-Info ("  {0} kundan eski: {1} ta, ~{2} MB bo'shatish mumkin" -f $Days, $stale.Count, [math]::Round($staleMb, 1)) "Yellow"
        Write-Info ""
        continue
    }

    # ------------------------------------------------------------- Delete
    # Eng yangi $KeepAtLeast ta - har doim saqlanadi (joriy sessiya shular ichida).
    $candidates = @($sessions | Select-Object -Skip $KeepAtLeast | Where-Object { $_.LastWriteTime -lt $cutoff })

    Write-Info ("  jami {0} ta sessiya, nomzod {1} ta ({2} kundan eski, eng yangi {3} tasi saqlanadi)" -f $sessions.Count, $candidates.Count, $Days, $KeepAtLeast) "DarkGray"

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

if (-not $Report) {
    Write-Info ""
    if ($DryRun) { $verb = "o'chirilardi" } else { $verb = "o'chirildi" }
    $summary = "{0} ta sessiya {1}, ~{2} MB bo'shadi" -f $totalDeleted, $verb, [math]::Round($totalFreedMb, 1)
    if ($totalSkipped -gt 0) { $summary += " ({0} tasi band edi)" -f $totalSkipped }

    if ($Quiet) { Write-Output $summary } else { Write-Host $summary -ForegroundColor Cyan }
}

# --------------------------------------------------------------------------
# Disklardagi bo'sh joy. VM_DISK_SPACE_INSUFFICIENT - sandbox VM ini
# YARATISHDAGI xato, ya'ni u xost diskiga bog'liq bo'lishi MUMKIN, lekin
# bu TASDIQLANMAGAN. Raqamlarni ko'rib, o'zingiz baholang.
# --------------------------------------------------------------------------

Write-Info ""
Write-Info "Disklardagi bo'sh joy:" "Cyan"
$drives = @(Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue)
foreach ($drive in $drives) {
    if ($null -eq $drive.Free) { continue }
    if ($null -eq $drive.Used) { continue }
    $freeGb  = [math]::Round($drive.Free / 1GB, 1)
    $totalGb = [math]::Round(($drive.Free + $drive.Used) / 1GB, 1)
    $line    = "  {0}:  {1} GB bo'sh / {2} GB" -f $drive.Name, $freeGb, $totalGb
    if ($Quiet) { Write-Output $line } else { Write-Host $line -ForegroundColor DarkGray }
}

# Virtual disk fayllari - Cowork sandboxi shular ustida ishlaydi.
Write-Info ""
Write-Info "Eng katta .vhdx fayllari (sandbox VM i shular ustida):" "Cyan"
$vhdxRoots = @()
if ($env:LOCALAPPDATA) { $vhdxRoots += (Join-Path $env:LOCALAPPDATA "Packages") }
if ($env:LOCALAPPDATA) { $vhdxRoots += (Join-Path $env:LOCALAPPDATA "Docker") }
if ($env:USERPROFILE)  { $vhdxRoots += (Join-Path $env:USERPROFILE "AppData\Local\wsl") }

$vhdxFiles = @()
foreach ($vhdxRoot in ($vhdxRoots | Sort-Object -Unique)) {
    if (-not (Test-Path -LiteralPath $vhdxRoot)) { continue }
    $vhdxFiles += @(Get-ChildItem -LiteralPath $vhdxRoot -Recurse -Filter "*.vhdx" -File -Force -ErrorAction SilentlyContinue)
}

if ($vhdxFiles.Count -eq 0) {
    Write-Info "  topilmadi" "DarkGray"
} else {
    foreach ($file in (@($vhdxFiles | Sort-Object Length -Descending) | Select-Object -First 5)) {
        Write-Info ("  {0,8:N1} GB  {1}" -f ($file.Length / 1GB), $file.FullName) "DarkGray"
    }
}
