# Sessiya 90 — «ikkiattor»: C diskdagi sessiya papkalari

- **Session ID:** `local_94739a47-f6b8-43a5-9eff-1e5a16744bc4`
- **Holat:** idle
- **Turi:** infratuzilma (kod emas) — svetyoq va continuity ikkalasiga tegishli

Bu sessiya svetyoq kodiga tegmaydi, lekin **shu `cowork_session` papkasi paydo bo'lishiga sabab bo'lgan** muammoni tushuntiradi, shuning uchun saqlandi.

---

## Muammo

C diskda joy tugab qolgan. Ikkita scheduled task har soatda ishlaydi:

- **continuity-dev** → `H:\tukhaev_s\hbr`
- **sveta-net-build** → `H:\tukhaev_s\svetyoq`

## Aniqlangani

Loyihalarning o'zi C diskda emas — ikkalasi ham H: da. Joyni yeyayotgani — **Cowork ning sessiya xotirasi**: har run uchun `C:\Users\5\AppData\Roaming\Claude\local-agent-mode-sessions\` ichida alohida papka yaratiladi (suhbat tarixi, log, vaqtinchalik nusxalar). Kuniga ~48 run × har biri alohida papka.

Bu papka himoyalangan — agent unga ulana olmaydi va o'zi tozalay olmaydi.

## Yechim (odam qo'lda bajaradi)

1. Cowork/Claude ilovasini yopish
2. `C:\Users\5\AppData\Roaming\Claude\local-agent-mode-sessions\` ga o'tish
3. Date modified bo'yicha saralab, eski sessiya papkalarini o'chirish

## Taklif qilingan, hali qabul qilinmagan

Ikkala taskni har soatda emas, 3–4 soatda bir ishlashga o'tkazish — sessiya to'planish tezligi kamayadi. **Javob berilmagan, ochiq qolgan.**

## Natija

Shundan keyin odam so'radi: sessiya tarixi C diskda yo'qolib ketmasligi uchun **`H:\tukhaev_s\svetyoq\cowork_session` ga ko'chirilsin** va har run boshida o'qilsin. Qoida `H:\tukhaev_s\svetyoq\CLAUDE.md` da.

---

## Davomi — 2026-08-06 (E5 runi)

Sandbox ikki run ketma-ket ishdan chiqdi:

```
ensure user: useradd failed: exit status 12:
useradd: cannot create directory /sessions/<session>
```

`exit status 12` = «uy papkasini yarata olmadi» — bu odatda **joy yetmasligi**. Ya'ni yuqoridagi muammo endi shunchaki noqulaylik emas, **agentning ishlashiga to'sqinlik qilyapti**: lint va testlar ishga tushmadi, E2 va E5 kodi lokal tekshiruvsiz qoldi.

**Savol berildi:** «tozalash har scheduled run dan oldin ro'yxatga kiritilmadimi?»

**Javob:** ko'chirish — ha (`SKILL.md` §4.1, run oxirida), o'chirish — yo'q. Sabab texnik: agent `C:\Users\5\AppData\Roaming\Claude\local-agent-mode-sessions\` ga umuman ula olmaydi (qayta tekshirildi — *"outside this session's connected folders"*). Qoidaga yozilsa ham bajarilmasdi.

**Yechim:** `H:\tukhaev_s\svetyoq\cleanup-sessions.ps1` yozildi. Tozalash Cowork tomonda emas, **Windows tomonda** bajariladi:

```powershell
.\cleanup-sessions.ps1 -DryRun     # avval ko'rish
.\cleanup-sessions.ps1             # 3 kundan eskisini o'chirish
```

Xavfsizlik: eng yangi 5 ta papka yoshidan qat'i nazar saqlanadi (joriy sessiya shular ichida), band papka o'tkazib yuboriladi.

Windows Task Scheduler ga kunlik qilib qo'yish:

```powershell
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument '-NoProfile -ExecutionPolicy Bypass -File "H:\tukhaev_s\svetyoq\cleanup-sessions.ps1" -Quiet'
$trigger = New-ScheduledTaskTrigger -Daily -At 4am
Register-ScheduledTask -TaskName "Cowork sessiya tozalash" -Action $action -Trigger $trigger
```

**Hali ochiq:** runlar chastotasi. Ikkala task har soatda ishlaydi (kuniga ~48 papka). 3–4 soatda birga o'tkazish taklifi hamon javobsiz.
