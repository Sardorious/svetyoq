# 184-run — §10 ning tiklanish o'qi uchidan-uchiga (ТС-210, ТС-212)

**Sessiya:** `local_ef2ca8c2` · **Sana:** 2026-08-20 · **Epic:** TZ (yangi qonun)

**Topshiriq (183-run qoldirgan):** «ТС-210/ТС-212 ni uchidan-uchiga yurish
(tiklanish → status → bildirishnoma), keyin reyestrdagi qolgan `PER_MODULE`
bandlar».

---

## 1. Nimadan boshlandi

`cowork_session/INDEX.md` → `EpicProgress.md` → `PROGRESS.md` ning run
jurnali → `app/release/tz_acceptance.py`. Reyestr ikkala bandni
`Depth.PER_MODULE` deb ko'rsatadi: ikkalasi ham `test_tz_restore.py` da
nomma-nom bor, lekin `walk=None`.

Keyin uchala modulning kodi o'qildi (`tzrestore.py` 710 qator,
`tzstatus.py` 616, `tzrestored.py` 595) va TZ ning §4.2, §5, §10
bo'limlari.

## 2. Birinchi topilma — yuborish huquqi hech qayerda o'lchanmagan

`tzrestored.py` ning docstringi 176-rundan beri shunday yozardi:

> «Podtverjdeno va undan yuqori» filtri `tzstatus.notifies()` da qoladi;
> bu modul chaqirilgan bo'lsa, demak status allaqachon tanlangan.

Ya'ni §6.2 ning filtri **chaqiruvchining yodida** turardi. §11/6 da
(177-run) aynan shu naql rad etilgan edi: `tzoutage.Outage.notifies` —
sukut qiymatisiz maydon, chunki «chaqiruvchi biladi» degan da'vo
o'lchanmaydi. Tiklanish tarafida esa o'sha qadam qilinmagan.

ТС-212 buni ko'rinadigan qiladi:

* §5 jadvali «Данные устарели» qatorida «уведомления — **нет**» deydi;
* `tzstatus.is_stale()` ga ko'ra jimlik **statusga aylanishining sharti**
  aynan kvartallarning bir qismi yopilgani (`Restoration.any_closed`)
  yoki oldingi statusning bildirishnoma yuborishi;
* ya'ni «Данные устарели» va «yopilgan kvartal bor» bir vaqtda bo'ladi, va
  yopilgan kvartallardan to'g'ridan-to'g'ri `Closure` yasagan chaqiruvchi
  jimgina «svet qaytdi» yuborardi.

**Qaror:** `Closure.notifies` — sukut qiymatisiz maydon, `plan()` esa
`False` da **bo'sh ro'yxat** qaytaradi.

*Rad etilgan variant:* sabab bilan `DROP` (`Reason.NOT_NOTIFYING`).
`plan_outage()` ning docstringi buni allaqachon rad etgan: sabab yozilsa,
keyingi qatlam uni «keyinroq yuborsak bo'ladi» deb o'qishi mumkin, §5 ning
«нет» i esa vaqtinchalik to'siq emas.

*Rad etilgan variant:* `tzrestored` ning o'zi `TzStatus` ni import qilsin.
`05` §1 va Т-5 ni buzardi — `app.notifications` `app.clustering` ni
bilmaydi.

## 3. Ikkinchi topilma — bitta bosqich ikkita modulni yashirardi

Reyestrning `STAGE_MODULES` xaritasida `Stage.NOTIFY` faqat
`app.notifications.tzoutage` ga qarardi. Lekin §6.3 ning jadvalida to'rtta
xabar bor va «Свет вернулся» butunlay boshqa modulda; ТС-214…ТС-217
ikkala test fayli bilan o'lchanadi. Natijasi jim edi: o'sha bandlarni
`WALKED` deb belgilash da'voning **yarmini** o'lchagan bo'lardi, chunki
`test_a_walked_case_names_a_file_that_imports_every_stage` faqat
`tzoutage` ni talab qilardi.

**Qaror:** `Stage.NOTIFY_RESTORED` ajratildi va ТС-214…ТС-217 ning yo'liga
qo'shildi.

*Rad etilgan variant:* `STAGE_MODULES` qiymatini `tuple[str, ...]` qilish.
U holda ТС-210 ning yo'li tiklanish xabari uchun `tzoutage` ni ham talab
qilardi — ya'ni yo'lga aloqasi yo'q modul.

## 4. ТС-210 ning chegarasi

§7 ning `tz.restore.answered_share` i bugun `0.40`, ТС-210 esa aynan
«40 % ответивших» beradi — ya'ni band `<` va `<=` orasidagi farqni
o'lchaydi (`close_block` da `share < need_share` → blocker). Buni alohida
test qulfladi: `yes=2/5` yopadi, `yes=1/5` yopmaydi.

Ikkinchi qulf — davomiylik: karta **hodisa** haqida (kvartallarning bir
qismi ochiq → aniq emas), xabar esa **kvartal** haqida (yopilgan lahza
ma'lum → aniq). Ikkalasini bitta songa yig'ish odamga uzilish o'z
kvartalida qancha davom etganini noto'g'ri aytardi.

## 5. Yozilgani

* `app/notifications/tzrestored.py` — `Closure.notifies` (sukut qiymatisiz),
  `plan()` da qorovul, docstringda 176-run naqli tuzatildi.
* `app/release/tz_acceptance.py` — `Stage.NOTIFY_RESTORED`, ТС-210/ТС-212
  ning `walk` i va yo'li, ТС-214…ТС-217 ning yo'li, hisob 5/20 `WALKED`.
* `tests/test_tz_walk_restore.py` — yangi, 7 test.
* `tests/test_tz_restored_notice.py` — fikstyuraga `notifies`, bitta yangi
  qulf.

## 6. O'lchov

Sandbox: `/tmp/mamba/envs/py311` (97-run retsepti), `TMPDIR=/tmp`,
to'plam `/sessions/.../work184` dagi nusxada (mount ustida 180 s ga
sig'maydi).

* **4560 passed, 371 skipped** — 50 s, bazasiz (`requires_db` skip).
  183-run bilan solishtirganda jami +12 test (7 yangi walk + 1 qulf +
  reyestrning parametrlangan ikkita testi ikkita yangi `WALKED` band uchun).
* `ruff check` — toza.
* Migratsiya, yangi sozlama, i18n kaliti va API **yo'q**.

### Qorovul haqiqatan otiladimi — uchta mutant tekshirildi (nusxada)

| Mutatsiya | Natija |
|---|---|
| `plan()` dan `if not closure.notifies: return ()` olib tashlandi | **KILLED** — 3 test |
| `notifies: bool = True` (sukut qiymati qaytarildi) | **KILLED** — `test_the_right_to_send_has_no_default_value` |
| `decide()` da jimlik qisman tiklanishdan **keyin** qo'yildi | **KILLED** — ТС-212 |

Uchala holatda ham fayllar `diff` bilan asl holatiga qaytarildi.

## 7. Ochiq savol (👤)

В-7 ning rasmiy manbasi (datchik, RES e'loni) **odamning xabari emas**,
ya'ni u uch soatlik jimlik ichida kvartalni yopishi mumkin: kvartal
haqiqatan yopilgan, odamlar esa «svet qaytdi» ni olmaydi. 184-run
spetsifikatsiyaga amal qildi (§5 — «нет») va buni ТС-212 ning yo'lida
qulfladi. Savol `PROGRESS.md` ning «Ochiq savollar» ida: §5 ning «нет» i
faqat odamlarning dalili bilan yopilganlarga tegishlimi?

## 8. Keyingi qadam

ТС-209/ТС-211/ТС-213 ni o'sha yo'lga qo'shish (ular bugun ham faqat
`test_tz_restore.py` da), keyin reyestrdagi qolgan `PER_MODULE` bandlar.
