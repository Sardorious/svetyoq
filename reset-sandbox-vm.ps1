# reset-sandbox-vm.ps1 - Cowork sandbox VM disklarini C dan ko'chirish
#
# ==========================================================================
# MUAMMO (166-run da o'lchandi)
#
# Sandbox "VM_DISK_SPACE_INSUFFICIENT" bilan ko'tarilmaydi. 166-run
# cleanup-sessions.ps1 ni tuzatib 378 ta eski sessiyani o'chirdi - bu
# atigi ~950 MB berdi, ya'ni sessiyalar muammo EMAS edi. Haqiqiy
# iste'molchi:
#
#   9.8 GB  ...\vm_bundles\claudevm.bundle\sessiondata.vhdx
#   9.8 GB  ...\vm_bundles\claudevm.bundle\rootfs.vhdx
#
# Ikkalasi C da 19.6 GB egallaydi, C da esa 8.2 GB bo'sh (222.9 dan).
# sessiondata.vhdx - bu sandboxning /sessions mounti; 141-run dagi
# "df" aynan shuni ko'rsatgan edi: /dev/sdc 9.8G 9.3G 0 100%.
#
# ==========================================================================
# NIMA QILADI
#
# vm_bundles papkasini butunligicha boshqa diskka KO'CHIRADI (o'chirmaydi).
# Keyingi ishga tushirishda Claude yangi, bo'sh VM yaratishi kutiladi.
# Loyiha ma'lumotlari xavf ostida emas: repo H: da, VM ichida faqat
# vaqtinchalik /sessions va rootfs turadi.
#
# Agar biror narsa noto'g'ri ketsa - "-Restore" bilan hammasi qaytariladi.
#
# ==========================================================================
# MUHIM: AVVAL CLAUDE NI YOPING
#
# Skript Claude ishlab turganini o'zi tekshiradi va ishlayotgan bo'lsa
# hech narsa qilmaydi. Yopilmagan holda fayllar band bo'ladi.
#
# DIQQAT: bu skript ishga tushganda joriy Cowork sessiyasi ham tugaydi -
# agentga aytadigan narsangiz bo'lsa, avval yozib qo'ying.
# ==========================================================================
#
# MUHIM: FAYL FAQAT ASCII (sabab: push.ps1 boshidagi izoh).
#
# Ishlatish:
#   .\reset-sandbox-vm.ps1 -DryRun     -> nima bo'lishini ko'rsatadi
#   .\reset-sandbox-vm.ps1             -> ko'chiradi
#   .\reset-sandbox-vm.ps1 -Restore    -> zaxiradan qaytaradi

param(
    [string]$BackupRoot = "H:\tukhaev_s\claude-vm-backup",
    [switch]$Restore,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Say($text, $color = "White") {
    Write-Host $text -ForegroundColor $color
}

function Get-FolderSizeGb($path) {
    try {
        $bytes = (Get-ChildItem -LiteralPath $path -Recurse -File -Force -ErrorAction SilentlyContinue |
                  Measure-Object -Property Length -Sum).Sum
        if (-not $bytes) { return 0.0 }
        return [math]::Round($bytes / 1GB, 2)
    } catch {
        return 0.0
    }
}

Say "=== Cowork sandbox VM ni ko'chirish ===" "Cyan"
Say ""

# --------------------------------------------------------------------------
# 1. Claude ishlab turmasin
# --------------------------------------------------------------------------

$running = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like "*laude*" })
if ($running.Count -gt 0) {
    Say "[!] Claude ishlab turibdi. Avval uni butunlay yoping." "Red"
    foreach ($proc in $running) {
        Say ("      {0} (PID {1})" -f $proc.ProcessName, $proc.Id) "DarkGray"
    }
    Say "    Tray dagi belgidan ham chiqing, keyin qayta yurgizing." "Yellow"
    return
}
Say "[+] Claude ishlamayapti - davom etamiz." "Green"

# --------------------------------------------------------------------------
# 2. Bundle ni topish
# --------------------------------------------------------------------------

$packageParents = @()
if ($env:LOCALAPPDATA) { $packageParents += (Join-Path $env:LOCALAPPDATA "Packages") }

$bundleParents = @()
foreach ($packageParent in ($packageParents | Sort-Object -Unique)) {
    if (-not (Test-Path -LiteralPath $packageParent)) { continue }
    $claudePackages = @(Get-ChildItem -LiteralPath $packageParent -Directory -Force -ErrorAction SilentlyContinue |
                        Where-Object { $_.Name -like "Claude*" })
    foreach ($claudePackage in $claudePackages) {
        $bundleParents += (Join-Path $claudePackage.FullName "LocalCache\Roaming\Claude\vm_bundles")
    }
}
# Virtualizatsiyasiz o'rnatish ehtimoli.
if ($env:APPDATA) { $bundleParents += (Join-Path $env:APPDATA "Claude\vm_bundles") }

$bundles = @($bundleParents | Sort-Object -Unique | Where-Object { Test-Path -LiteralPath $_ })

# --------------------------------------------------------------------------
# 3. Restore
# --------------------------------------------------------------------------

if ($Restore) {
    if (-not (Test-Path -LiteralPath $BackupRoot)) {
        Say ("[!] Zaxira papkasi yo'q: {0}" -f $BackupRoot) "Red"
        return
    }
    $backups = @(Get-ChildItem -LiteralPath $BackupRoot -Directory -Force -ErrorAction SilentlyContinue |
                 Sort-Object Name -Descending)
    if ($backups.Count -eq 0) {
        Say "[!] Zaxira topilmadi." "Red"
        return
    }

    $newest = $backups[0]
    $marker = Join-Path $newest.FullName "ORIGINAL_PATH.txt"
    if (-not (Test-Path -LiteralPath $marker)) {
        Say ("[!] {0} ichida ORIGINAL_PATH.txt yo'q - qo'lda qaytaring." -f $newest.FullName) "Red"
        return
    }

    $target  = (Get-Content -LiteralPath $marker -Raw).Trim()
    $payload = Join-Path $newest.FullName "vm_bundles"

    Say ("  zaxira : {0}" -f $payload) "DarkGray"
    Say ("  manzil : {0}" -f $target) "DarkGray"

    if (Test-Path -LiteralPath $target) {
        Say ("[!] Manzilda allaqachon vm_bundles bor: {0}" -f $target) "Red"
        Say "    Yangi VM yaratilgan bo'lishi mumkin. Qo'lda hal qiling." "Yellow"
        return
    }
    if ($DryRun) {
        Say "  [DryRun] ko'chirilardi" "Yellow"
        return
    }

    $targetParent = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $targetParent)) {
        New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
    }
    Move-Item -LiteralPath $payload -Destination $target -Force
    Say "[+] Qaytarildi." "Green"
    return
}

# --------------------------------------------------------------------------
# 4. Ko'chirish
# --------------------------------------------------------------------------

if ($bundles.Count -eq 0) {
    Say "[!] vm_bundles topilmadi. Tekshirilgan yo'llar:" "Red"
    foreach ($candidate in ($bundleParents | Sort-Object -Unique)) {
        Say ("      {0}" -f $candidate) "DarkGray"
    }
    return
}

$stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

foreach ($bundle in $bundles) {
    $sizeGb = Get-FolderSizeGb $bundle
    Say ""
    Say ("Topildi: {0}" -f $bundle) "White"
    Say ("  hajmi : {0} GB" -f $sizeGb) "Cyan"

    $destDir = Join-Path $BackupRoot $stamp
    $dest    = Join-Path $destDir "vm_bundles"
    Say ("  manzil: {0}" -f $dest) "DarkGray"

    if ($DryRun) {
        Say "  [DryRun] ko'chirilardi" "Yellow"
        continue
    }

    if (-not (Test-Path -LiteralPath $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
    Set-Content -LiteralPath (Join-Path $destDir "ORIGINAL_PATH.txt") -Value $bundle -Encoding ASCII

    try {
        Move-Item -LiteralPath $bundle -Destination $dest -Force
        Say ("  [+] ko'chirildi, C da ~{0} GB bo'shadi" -f $sizeGb) "Green"
    } catch {
        Say ("  [!] ko'chirib bo'lmadi: {0}" -f $_.Exception.Message) "Red"
        Say "      Claude to'liq yopilganiga ishonch hosil qiling." "Yellow"
    }
}

# --------------------------------------------------------------------------
# 5. Natija
# --------------------------------------------------------------------------

Say ""
Say "Disklardagi bo'sh joy:" "Cyan"
foreach ($drive in @(Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue)) {
    if ($null -eq $drive.Free) { continue }
    if ($null -eq $drive.Used) { continue }
    $freeGb  = [math]::Round($drive.Free / 1GB, 1)
    $totalGb = [math]::Round(($drive.Free + $drive.Used) / 1GB, 1)
    Say ("  {0}:  {1} GB bo'sh / {2} GB" -f $drive.Name, $freeGb, $totalGb) "DarkGray"
}

if (-not $DryRun) {
    Say ""
    Say "Keyingi qadam:" "Cyan"
    Say "  1. Claude ni ishga tushiring - u yangi VM yaratishi kerak." "White"
    Say "  2. Agentga sandbox ni tekshirishni ayting." "White"
    Say "  3. Ishlasa, zaxirani o'chirsangiz bo'ladi:" "White"
    Say ("       {0}" -f $BackupRoot) "DarkGray"
    Say "  4. Ishlamasa - .\reset-sandbox-vm.ps1 -Restore" "White"
}
