# 08 — Sandbox takroran yiqilmoqda, ish to'xtatilgan (6-…21-run)

**Sessiya:** `local_d9cd1a43` (6-run), `local_e91b2267` (7-run),
`local_44e07f35` (8-run), `local_0d1cefc6` (9-run), `local_f17f103a` (10-run),
`local_1f44d4db` (11-run), `local_882408c6` (12-run), `local_997e4202` (13-run),
`local_8fbf2da1` (14-run), `local_04dc5274` (15-run), `local_7a425a6b` (16-run),
`local_561e818c` (17-run), `local_d31b110b` (18-run),
`local_1741b615` (19-run), `local_0bfbc3cc` (20-run), `local_6773453c` (21-run)
**Sana:** 2026-08-07 (oxirgi tekshiruv — 21-run, `useradd failed`, ikki urinish)
**Ketma-ket muvaffaqiyatsiz runlar:** 21
**Natija:** ⛔ Kod yozilmadi, statik review qilinmadi. INFRA-1 kutilmoqda.

> **7-run (2026-08-07, `local_e91b2267`).** `INDEX.md` ko'rsatmasi bo'yicha
> yangi sessiya fayli yaratilmadi — shu fayl yangilandi. Tekshiruv:
> `ls .../sveta/` va `echo OK` — ikkalasi ham aynan bir xil
> `useradd failed: exit status 12` xatosi. Repo o'zgarmadi.

> **8-run (2026-08-07, `local_44e07f35`).** Yana yangi sessiya fayli
> yaratilmadi. Tekshiruv: `ls .../sveta/ && python3 --version` va `echo ok` —
> ikkalasi ham `useradd failed: exit status 12`, endi
> `/sessions/confident-lucid-hawking` papkasi uchun. Ya'ni xato sessiya
> nomiga bog'liq emas — diskdagi umumiy sabab o'zgarmagan. Repo o'zgarmadi.

> **9-run (2026-08-07, `local_0d1cefc6`).** Yangi sessiya fayli yaratilmadi.
> Tekshiruv: `echo OK && python3 --version && ls .../sveta/` va `echo OK` —
> ikkalasi ham `useradd failed: exit status 12`, bu safar
> `/sessions/epic-fervent-cannon` papkasi uchun. Xato uchinchi xil sessiya
> nomida ham bir xil — sabab diskda. Repo o'zgarmadi.

> **10-run (2026-08-07, `local_f17f103a`).** Yangi sessiya fayli yaratilmadi.
> Tekshiruv: `echo OK && date -u && ls .../mnt/` va `echo OK` — ikkalasi ham
> `useradd failed: exit status 12`, bu safar `/sessions/vibrant-vigilant-gauss`
> papkasi uchun (to'rtinchi xil sessiya nomi). Repo o'zgarmadi.

> **11-run (2026-08-07, `local_1f44d4db`).** Yangi sessiya fayli yaratilmadi.
> Tekshiruv: `echo ok && ls .../svetyoq/sveta/` va `echo ok` — ikkalasi ham
> `useradd failed: exit status 12`, bu safar `/sessions/gracious-awesome-pascal`
> papkasi uchun (beshinchi xil sessiya nomi). Repo o'zgarmadi.

> **12-run (2026-08-07, `local_882408c6`).** Yangi sessiya fayli yaratilmadi.
> Tekshiruv: `cd .../svetyoq/sveta && echo OK && ls` va `echo probe` — ikkalasi
> ham `useradd failed: exit status 12`, bu safar
> `/sessions/hopeful-elegant-hamilton` papkasi uchun (oltinchi xil sessiya
> nomi). Repo o'zgarmadi.

> **13-run (2026-08-07, `local_997e4202`).** Yangi sessiya fayli yaratilmadi.
> Tekshiruv: `cd .../svetyoq/sveta && ls && python3 --version` va `echo ok` —
> ikkalasi ham `useradd failed: exit status 12`, bu safar
> `/sessions/elegant-friendly-euler` papkasi uchun (yettinchi xil sessiya
> nomi). Repo o'zgarmadi.

> **14-run (2026-08-07, `local_8fbf2da1`).** Yangi sessiya fayli yaratilmadi.
> Tekshiruv: `echo OK && ls .../svetyoq/sveta/` va `echo probe2` — ikkalasi ham
> `useradd failed: exit status 12`, bu safar
> `/sessions/gallant-zealous-faraday` papkasi uchun (sakkizinchi xil sessiya
> nomi). Repo o'zgarmadi.

> **15-run (2026-08-07, `local_04dc5274`).** Yangi sessiya fayli yaratilmadi.
> Tekshiruv: `echo ok && ls .../svetyoq/sveta/` va `echo ok` — ikkalasi ham
> `useradd failed: exit status 12`, bu safar `/sessions/cool-epic-carson`
> papkasi uchun (to'qqizinchi xil sessiya nomi). Repo o'zgarmadi.

> **16-run (2026-08-07, `local_7a425a6b`).** Yangi sessiya fayli yaratilmadi.
> Tekshiruv: `echo OK && ls .../svetyoq/sveta/ && python3 --version` va
> `echo OK` — ikkalasi ham `useradd failed: exit status 12`, bu safar
> `/sessions/gracious-trusting-keller` papkasi uchun (o'ninchi xil sessiya
> nomi). Repo o'zgarmadi.

> **17-run (2026-08-07, `local_561e818c`).** Yangi sessiya fayli yaratilmadi.
> Tekshiruv: `echo ok && ls .../svetyoq/sveta/` va `echo ok` — ikkalasi ham
> `useradd failed: exit status 12`, bu safar
> `/sessions/wizardly-sleepy-albattani` papkasi uchun (o'n birinchi xil sessiya
> nomi). Repo o'zgarmadi.

> **18-run (2026-08-07, `local_d31b110b`).** Yangi sessiya fayli yaratilmadi.
> Tekshiruv: `echo ok && ls .../svetyoq/sveta/` va `echo alive` — ikkalasi ham
> `useradd failed: exit status 12`, bu safar `/sessions/bold-kind-ptolemy`
> papkasi uchun (o'n ikkinchi xil sessiya nomi). Repo o'zgarmadi.

> **19-run (2026-08-07, `local_1741b615`).** Yangi sessiya fayli yaratilmadi.
> Tekshiruv: `echo ok && ls .../svetyoq/sveta/` va `echo ok` — ikkalasi ham
> `useradd failed: exit status 12`, bu safar `/sessions/gifted-zen-goodall`
> papkasi uchun (o'n uchinchi xil sessiya nomi). Repo o'zgarmadi.

> **20-run (2026-08-07, `local_0bfbc3cc`).** Yangi sessiya fayli yaratilmadi.
> Tekshiruv: `cd .../svetyoq/sveta && ls && python3 --version` va `echo ok` —
> ikkalasi ham `useradd failed: exit status 12`, bu safar
> `/sessions/modest-optimistic-hamilton` papkasi uchun (o'n to'rtinchi xil
> sessiya nomi). Repo o'zgarmadi.

> **21-run (2026-08-07, `local_6773453c`).** Yangi sessiya fayli yaratilmadi.
> Tekshiruv: `cd .../svetyoq/sveta && ls && python --version` va `echo ok` —
> ikkalasi ham `useradd failed: exit status 12`, bu safar
> `/sessions/great-clever-pasteur` papkasi uchun (o'n beshinchi xil sessiya
> nomi). Repo o'zgarmadi.

---

## Run tartibi

1. `cowork_session/INDEX.md` o'qildi — «Qayerda to'xtadik»: sandbox 5 run
   ketma-ket yiqilgan, ish to'xtatilgan, keyingi sessiyaning **birinchi ishi —
   yana sandboxni tekshirish**.
2. `sveta/PROGRESS.md` o'qildi — E2, E5, E5b uchtasi ham 🔄, hech biri
   `ruff`/`pytest` ko'rmagan.
3. Sandbox tekshirildi (ikki urinish):

```
python3 --version && ls .../svetyoq/sveta/
→ RPC error -1: ensure user: useradd failed: exit status 12:
  useradd: cannot create directory /sessions/wizardly-tender-keller
```

Ikkinchi urinish (`echo OK`) — **aynan bir xil xato**. Uchinchi urinish
qilinmadi: xato o'zgarmasa qayta urinmaslik kerak.

---

## Qaror

`INDEX.md` ning ko'rsatmasi so'zma-so'z bajarildi:

> «Yana yiqilsa: kod yozmang, statik review qilmang — shu holatni takrorlab
> odamga ayting.»

Sabab o'zgarmagan: E2, E5, E5b — **uchta tekshirilmagan qatlam**. To'rtinchisini
qo'shish yoki uchinchi marta ko'z bilan review qilish (05-sessiya buni
allaqachon qilgan, defekt topmagan) hech qanday yangi ma'lumot bermaydi. Yagona
haqiqiy signal — CI.

Repo holati o'zgarmadi. Faqat `INDEX.md` va `PROGRESS.md` yangilandi.

---

## Odamdan kutilayotgani (tartib bo'yicha, o'zgarmagan)

1. **`.\cleanup-sessions.ps1`** — sandbox yiqilishining sababi C diskdagi
   `local-agent-mode-sessions\` papkasi to'lgani. Agent bu skriptni o'zi ishga
   tushira olmaydi. Yordam bermasa: Cowork ni qayta ishga tushirish yoki
   o'sha papkani qo'lda tozalash.
2. **`.\push.ps1`** → CI **E2 + E5 + E5b ni birga** tekshiradi (PostGIS xizmati
   bilan) — uchala epic uchun birinchi haqiqiy tekshiruv.

Bu ikkitasisiz keyingi runlar ham xuddi shu natijani beradi.

---

## Kuzatuv: takrorlanuvchi behuda run

2026-08-06 dan beri **yigirma bitta** run bir xil xato bilan yiqildi. Bloklanish
odam aralashuvisiz o'z-o'zidan yechilmaydi, ya'ni har soatlik `sveta-net-build`
task hozir faqat hujjatni qayta yozmoqda.

**Taklif (odam qaroriga):** INFRA-1 hal bo'lgunicha scheduled task ni
**pauza qilish**. Aks holda arxivda bir xil mazmunli sessiya fayllari
to'planadi. Agent task ni o'zi o'chirmadi — bu odam qarori.
