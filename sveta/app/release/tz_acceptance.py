"""TZ §10 — qabul ro'yxati (ТС-201…ТС-220).

**Nima uchun bu modul bor.** §10 — TZ ning yagona joyi bo'lib, u
«qurildimi?» degan savolga **hujjatning o'z tili bilan** javob
beradi: yigirmata satr, har biri «tekshiruv → kutilgan natija».
172–181 runlar §11 navbatining yettala bandini qurdi va har bir
band o'z testida ТС nomerlarini izohda qoldirdi. Ya'ni qamrov
**bor** edi, lekin uni ko'radigan joy yo'q edi: qaysi ТС qaysi
faylda o'lchanadi degan savolga javob faqat `grep` bilan olinardi,
va aynan shu sababdan bitta band yigirma to'qqizta run davomida
ko'zdan qochib qoldi.

## Nimani topdi

`ТС-208` — «В районе 50 кварталов, пользователи в 12, подтверждено
5» — 181-run oxirida butun `tests/` daraxtida **bir marta ham**
uchramasdi. Sababi navbatda: §11 ning yetti bandi §3 (masshtab) ni
**umuman nomlamaydi**, ya'ni u na «Подсчёт» ga, na «Восстановление»
ga tushdi. Shu bilan birga §7 ning `tz.scale.*` sozlamalari
172-runda reyestrga yozilgan va migratsiyada bor edi — sozlama
iste'molchisiz turgani hech qayerda qizarmasdi. 182-run
`app.clustering.tzscale` ni yozdi.

`ТС-218` — «Попытка удалить подтверждённую аварию → Отказ базы»
(Т-10) — 182-run oxirida **qurilmagan** edi: `outages` jadvalida
`DELETE` ni qaytaradigan trigger yo'q, chunki `0012`…`0015`
migratsiyalari bunday himoyani faqat TZ ning **yangi** jadvallariga
qo'ygan (`config_journal`, `tz_signals`, `tz_receipts`,
`tz_operator_actions`) — `outages` esa `0002` da tug'ilgani uchun
o'sha to'lqinga tushmagan. 183-run `0016` bilan yopdi; qorovul
`confirmed_at IS NOT NULL` ni o'qiydi (joriy status **emas** — aks
holda «tasdiqla → yop → o'chir» taqiqni ikki qadamda chetlab
o'tardi), Т-3 ning qayta hisoblashi uchun esa bitta ko'rinadigan
teshik qoldirilgan: tranzaksiya doirasidagi `SET LOCAL` bayrog'i
(`RECLUSTER_GUC`), faqat `app.clustering.repository.delete_outages`
da.

## Uchta holat, ikkita har xil savol

`State` — «mahsulot kodi bormi», `Depth` — «qanchalik chuqur
o'lchandi». Ularni bitta ustunga qo'shish eng ko'p uchraydigan
xatoni jimgina qilardi: modul ichida nomma-nom o'lchangan band
«bajarilgan» ko'rinadi, holbuki bandning o'zi **yo'l** haqida
(«исправление отправлено тем же людям» — bu sanash ham, status
ham, jurnal ham, yuborish ham).

`Depth.PER_MODULE` — band o'z modulining testida bor, lekin yo'lning
boshidan oxirigacha bitta testda yurilmagan. `Depth.WALKED` — bitta
test butun yo'lni yuradi va uning fayli `walk` maydonida nomlanadi.
Da'vo tekshiriladi: `tests/test_tz_acceptance.py` o'sha faylni
`ast` bilan o'qiydi va yo'lning **har** bosqichi uchun mos modul
import qilinganini talab qiladi. Ya'ni `WALKED` ni qo'lda yozib
qo'yib bo'lmaydi.

## Bosqich bittadan ko'p modulga tegishi mumkin (184-run)

`Stage.NOTIFY` boshida `app.notifications.tzoutage` ga qarardi,
holbuki §6.3 ning jadvalida to'rtta xabar bor va «Свет вернулся»
butunlay boshqa modulda (`tzrestored`). Natijasi jim edi:
ТС-214…ТС-217 ikkala test fayli bilan o'lchanadi, lekin `WALKED`
da'vosi ulardan faqat bittasini talab qilardi — ya'ni yo'lni
yurgan deb belgilangan band amalda yarmini o'lchagan bo'lardi.
Shundan `Stage.NOTIFY_RESTORED` ajratildi.

## Yo'l bosqichdan ko'proq narsani ochadi (185-run)

ТС-209, ТС-211 va ТС-213 reyestrda bitta bosqichli (`RESTORE`)
bandlar edi, ya'ni ular ta'rifi bo'yicha «yurilmaydigan» hisoblanardi
— `test_a_single_stage_case_is_never_marked_walked` shuni talab
qiladi. Ammo bosqichlar ro'yxati **da'voning o'zidan** chiqadi, va
uchchalasining da'vosi tiklanish hisobi bilan tugamaydi: «квартал не
закрыт» degani kartada ham, xabarda ham hech narsa o'zgarmasligi.
Yo'lni uzaytirgach ТС-209 ning ostidan 184-run qorovulining teshigi
chiqdi: §6.2 ning yuborish huquqi hodisaning **statusidan** olinadi
va yopilmagan kvartalli hodisada ham rost bo'ladi, ya'ni
`Restoration.blocks` dan xabar yasagan chaqiruvchini u to'smaydi.
Filtr shundan keyin `Restoration.announced` ga chiqarildi.

## Bosqichlar soni yo'lning qiymatini o'lchamaydi (186-run)

ТС-214…ТС-217 — atigi ikki bosqichli bandlar (`NOTIFY`,
`NOTIFY_RESTORED`), ya'ni reyestrga qaraganda ular «eng qisqa»
yo'llar. Amalda esa aynan shular eng ko'p yashirardi: ikkala bosqich
bir-birini chaqirmaydi va ular orasida **Т-9 ning jurnali** turadi,
har modul esa `Ledger` ni **tayyor** oladi. Chok modulda emas,
chokda.

186-run shundan bittasini topdi. §6.2/4 ertalabki svodkani «одним
сводным сообщением» deb ta'riflaydi va bildirishnoma **turini
umuman nomlamaydi** — qoida odam haqida. Ikkala modulning svodka
testi ham bir turdagi yetkazishlar ustida yurardi, ya'ni tunda
tasdiqlangan uzilish va o'sha tunda qaytgan svet bitta odamga
ikkita alohida xabar bo'lib chiqishi hech qayerda o'lchanmasdi.
`digests()` ni `text_key` bo'yicha ham guruhlaydigan mutant butun
to'plamda **faqat** yangi yo'l testlari bilan o'ladi.

## Maxraj — yo'lsiz ko'rinmaydigan tur (187-run)

ТС-208 reyestrda ikki bosqichli (`COUNT`, `SCALE`) va uning o'z
testi §3 ning arifmetikasini to'liq qoplaydi. Ammo o'sha test
`ZoneFact` larni **qo'lda** yasaydi, ya'ni §3 ning eng qimmat
jumlasi — «знаменатель — только зоны с пользователями» — modul
ichida emas, modullar **orasida** yashaydi. `from_zone_verdicts()`
ning `blocks_with_users` argumenti sukut bo'yicha bo'sh edi, ya'ni
argumentni yozmagan chaqiruvchi maxrajni jimgina «bugun xabar
qilgan kvartallar» ga qisqartirardi. Ikkinchisi birinchisidan har
doim kichik va xabar qilgan kvartalning tasdiqlanishi odatiy hol,
demak §3 ning 40 % i o'z-o'zidan bajariladigan shartga aylanardi:
o'sha to'rtta kvartal bilan tuman bir chaqiruvda tasdiqlanmaydi,
ikkinchisida tasdiqlanadi. Hujjat faqat teskari xavfdan
ogohlantiradi («иначе порог недостижим навсегда»), shuning uchun
bu tomon hech qayerda qizarmasdi. Sukut qiymati olib tashlandi.

ТС-207 esa bosqichini oshirdi: bandning ikkinchi yarmi («без
уведомлений») §6.2 da, ya'ni yo'l `NOTIFY` gacha boradi. Bu —
yagona qurilgan holat bo'lib, unda `ZoneVerdict.reached` rost va
xabar baribir ketmaydi; qolgan hamma joyda hisob bilan yuborish
huquqi bir tomonga qaraydi.

## Bir bosqichli band ham yo'l bo'lib chiqdi (188-run)

ТС-202, ТС-203 va ТС-204 reyestrda bitta bosqichli (`COUNT`) edi,
ya'ni `test_a_single_stage_case_is_never_marked_walked` bo'yicha
ular yurilmaydigan hisoblanardi. Ammo ularning da'vosi §1.1 ning
**yaqinlashuvi** haqida, va u tasdiqlashda ham, §2.2 ning qarshi
dalilida ham, §4 ning tiklanishida ham bir xil ishlashi kerak —
uchala modul `tzcount.count_witnesses()` ni ataylab qayta
ishlatadi. Ya'ni da'vo bitta modulda tugamaydi, yo'l esa
`COUNT` → `DISPUTE` → `RESTORE` → `STATUS`.

Chokdan ikkita nosozlik chiqdi. `count_rebuttals()` ning
`reporters` argumenti sukut bo'yicha bo'sh edi: uni yozmagan
chaqiruvchida §2.2 ning 🔴 qarori («uzilishni xabar qilgan
odamning "menda svet bor" i qarshi dalil emas») jimgina o'chib,
haqiqiy uzilish «Спорно» ga tushardi. Sababi esa qo'shni modulda
edi — `ZoneVerdict` sanagan akkauntlarini **qaytarmasdi**, ya'ni
normal yo'ldan kelgan chaqiruvchi to'g'ri ro'yxatni topa olmasdi
va bo'sh sukut qiymati shundan zararsiz ko'rinardi.
`ZoneVerdict.users` qo'shildi, sukut qiymati olib tashlandi.

Bugungi hisob (188-run): 20 banddan 20 tasi qurilgan, 17 tasi
uchidan-uchiga yurilgan. Reyestr shu bilan **toza emas**: qolgan
uchtasi (ТС-218, ТС-219, ТС-220) faqat o'z modulida o'lchanadi.

Modul **toza**: faqat ro'yxat va undan chiqadigan hisob.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Hujjat bo'limi. Reyestrlar vitrinasi (`app.admin.registries`) shuni o'qiydi.
SPEC = "TZ §10"


class Stage(StrEnum):
    """Yo'lning bosqichi — bandning qaysi qatlamga tegishi.

    Ro'yxat §11 ning navbatidan **emas**, TZ ning bo'limlaridan
    chiqadi: navbat ish tartibi, bu esa mahsulotning qatlamlari.
    Farqi aynan §3 da ko'rindi — navbatda yo'q bosqich mavjud.
    """

    #: §1 — xabarning qabuli va uning katagi.
    INTAKE = "intake"
    #: §1.1, §2.1, §2.3 — guvohlarni sanash va poroglar.
    COUNT = "count"
    #: §2.2 — qarshi dalillar va veto.
    DISPUTE = "dispute"
    #: §3 — masshtab: tuman va shahar.
    SCALE = "scale"
    #: §5 — status va karta.
    STATUS = "status"
    #: §4, §4.1, §4.2 — tiklanish, opros, jimlik.
    RESTORE = "restore"
    #: §6.1–§6.3 — **uzilish** haqidagi bildirishnoma va rejali ishlar.
    NOTIFY = "notify"
    #: §6.3 — «Свет вернулся». Alohida bosqich, chunki alohida modul:
    #: §6.3 ning jadvalida to'rtta xabar bor va ularning ikkitasi
    #: («Авария подтверждена» va «Свет вернулся») har xil kirishdan
    #: quriladi. Bitta `NOTIFY` bosqichi ikkala modulni bittasining
    #: nomi bilan yashirardi: `WALKED` da'vosi faqat `tzoutage` ni
    #: talab qilardi, holbuki ТС-214…ТС-217 ikkala fayl bilan
    #: o'lchanadi.
    NOTIFY_RESTORED = "notify_restored"
    #: §6.4 — majburiy tuzatish.
    CORRECT = "correct"
    #: §8 — operatorning qarori.
    OPERATOR = "operator"
    #: §7, Т-2, Т-10 — sozlamalar va bazadagi taqiqlar.
    SCHEMA = "schema"


#: `Stage` → shu bosqichni bajaradigan modul. `WALKED` da'vosi shu
#: xarita bilan tekshiriladi, ya'ni xarita izoh emas — shart.
STAGE_MODULES: dict[Stage, str] = {
    Stage.INTAKE: "app.reports.tzsensor",
    Stage.COUNT: "app.clustering.tzcount",
    Stage.DISPUTE: "app.clustering.tzdispute",
    Stage.SCALE: "app.clustering.tzscale",
    Stage.STATUS: "app.clustering.tzstatus",
    Stage.RESTORE: "app.clustering.tzrestore",
    Stage.NOTIFY: "app.notifications.tzoutage",
    Stage.NOTIFY_RESTORED: "app.notifications.tzrestored",
    Stage.CORRECT: "app.notifications.tzoutage",
    Stage.OPERATOR: "app.admin.tzoperator",
    Stage.SCHEMA: "app.core.tzconfig",
}


class State(StrEnum):
    """Mahsulot kodi bormi."""

    BUILT = "built"
    #: Kod yo'q — band bugun bajarilmaydi.
    UNBUILT = "unbuilt"


class Depth(StrEnum):
    """Qanchalik chuqur o'lchandi."""

    #: Umuman o'lchanmagan.
    NONE = "none"
    #: Har bosqich o'z modulining testida, yo'l bo'ylab emas.
    PER_MODULE = "per_module"
    #: Bitta test yo'lning boshidan oxirigacha yuradi.
    WALKED = "walked"


@dataclass(frozen=True)
class Case:
    """§10 jadvalining bitta qatori."""

    code: str
    #: «Проверка» ustuni — qisqartirilgan.
    check: str
    #: «Ожидается» ustuni.
    expects: str
    path: tuple[Stage, ...]
    #: Bandni nomma-nom eslatadigan test fayllari (`tests/` ga nisbatan).
    tests: tuple[str, ...]
    #: Yo'lni to'liq yuradigan test fayli — `Depth.WALKED` ning dalili.
    walk: str | None
    state: State
    note: str = ""

    @property
    def depth(self) -> Depth:
        """Chuqurlik ro'yxatdan **hisoblanadi**, qo'lda yozilmaydi."""
        if not self.tests:
            return Depth.NONE
        if self.walk is not None:
            return Depth.WALKED
        return Depth.PER_MODULE


CASES: tuple[Case, ...] = (
    Case(
        code="ТС-201",
        check="3 kishi turli manzildan, r10 katagida, 15 daqiqada",
        expects="Tasdiqlangan",
        path=(Stage.COUNT, Stage.STATUS),
        tests=("test_tz_counting.py",),
        walk="test_tz_walk.py",
        state=State.BUILT,
    ),
    Case(
        code="ТС-202",
        check="Bitta odamning turli nuqtadan 3 xabari",
        expects="Tasdiqlanmagan",
        path=(Stage.COUNT, Stage.DISPUTE, Stage.RESTORE, Stage.STATUS),
        tests=("test_tz_counting.py", "test_tz_dispute.py", "test_tz_restore.py"),
        walk="test_tz_walk_count.py",
        state=State.BUILT,
    ),
    Case(
        code="ТС-203",
        check="Bitta r11 katagidagi 3 akkaunt",
        expects="Tasdiqlanmagan",
        path=(Stage.COUNT, Stage.DISPUTE, Stage.RESTORE, Stage.STATUS),
        tests=("test_tz_counting.py", "test_tz_dispute.py", "test_tz_restore.py"),
        walk="test_tz_walk_count.py",
        state=State.BUILT,
    ),
    Case(
        code="ТС-204",
        check="3 kishi, lekin 40 daqiqada (oyna 20)",
        expects="Tasdiqlanmagan",
        path=(Stage.COUNT, Stage.DISPUTE, Stage.RESTORE, Stage.STATUS),
        tests=("test_tz_counting.py",),
        walk="test_tz_walk_count.py",
        state=State.BUILT,
    ),
    Case(
        code="ТС-205",
        check="Tasdiqlangan, keyin 2 kishi «svet bor» dedi",
        expects="«Sporno», tasdiq qaytarib olindi",
        path=(Stage.COUNT, Stage.DISPUTE, Stage.STATUS),
        tests=("test_tz_dispute.py",),
        walk="test_tz_walk.py",
        state=State.BUILT,
    ),
    Case(
        code="ТС-206",
        check="O'sha, lekin bildirishnomalar allaqachon ketgan",
        expects="Tuzatish o'sha odamlarga yuborildi",
        path=(Stage.DISPUTE, Stage.STATUS, Stage.NOTIFY, Stage.CORRECT),
        tests=("test_tz_dispute.py", "test_tz_outage_notice.py"),
        walk="test_tz_walk.py",
        state=State.BUILT,
        note="181-run ning jim defekti aynan shu yo'lning ikki moduli orasida edi",
    ),
    Case(
        code="ТС-207",
        check="Zonada jami 2 foydalanuvchi, ikkalasi ham xabar qildi",
        expects="«Вероятно», bildirishnoma yo'q",
        path=(Stage.COUNT, Stage.STATUS, Stage.NOTIFY),
        tests=("test_tz_counting.py", "test_tz_status.py"),
        walk="test_tz_walk.py",
        state=State.BUILT,
        note=(
            "Yo'lga bildirishnoma qo'shildi: bandning ikkinchi yarmi "
            "(«без уведомлений») §6.2 da yashaydi. Bu — yagona qurilgan "
            "holat bo'lib, unda hisob `reached=True` deydi va xabar "
            "baribir ketmaydi; ya'ni yuborish huquqini `verdict.reached` "
            "dan olgan chaqiruvchi faqat shu bandda yiqiladi"
        ),
    ),
    Case(
        code="ТС-208",
        check="Tumanda 50 kvartal, foydalanuvchi 12 tasida, 5 tasi tasdiqlangan",
        expects="Tuman tasdiqlandi (5 ≥ 12 ning 40 % i va ≥ 3)",
        path=(Stage.COUNT, Stage.SCALE),
        tests=("test_tz_scale.py",),
        walk="test_tz_walk_scale.py",
        state=State.BUILT,
        note=(
            "182-rungacha butun `tests/` da bir marta ham uchramasdi — §3 "
            "navbatda yo'q edi. 187-run yo'l bo'ylab yurganda §3 ning "
            "maxraji `tzcount` ning natijasidan **kelib chiqmasligi** "
            "ochildi: `from_zone_verdicts()` ning `blocks_with_users` "
            "sukut qiymati bo'sh edi, ya'ni argumentni yozmagan "
            "chaqiruvchi maxrajni jimgina «bugun xabar qilgan "
            "kvartallar» ga qisqartirardi va o'sha dalildan teskari "
            "verdikt chiqardi. Sukut qiymati olib tashlandi"
        ),
    ),
    Case(
        code="ТС-209",
        check="20 xabar berganda 1 kishi «svet qaytdi» ni bosdi",
        expects="Kvartal yopilmadi",
        path=(Stage.COUNT, Stage.RESTORE, Stage.STATUS, Stage.NOTIFY_RESTORED),
        tests=("test_tz_restore.py",),
        walk="test_tz_walk_restore.py",
        state=State.BUILT,
        note=(
            "Yo'lga sanash ham kiradi: В-4 nuqtani **olib tashlaydi** va "
            "o'sha akkauntni guvoh qiladi — ikkala yarim ham "
            "chaqiruvchida. 185-run ning topilmasi oxirida: §6.2 ning "
            "huquqi yopilmagan kvartalni to'smaydi, chunki u hodisaning "
            "statusidan olinadi va «Подтверждено жителями» da rost. "
            "Yagona to'siq — `Restoration.announced`"
        ),
    ),
    Case(
        code="ТС-210",
        check="2 kishi va javob berganlarning 40 % i",
        expects="Kvartal yopildi, hodisa «qisman tiklandi»",
        path=(Stage.RESTORE, Stage.STATUS, Stage.NOTIFY_RESTORED),
        tests=("test_tz_restore.py",),
        walk="test_tz_walk_restore.py",
        state=State.BUILT,
        note=(
            "Yo'lga bildirishnoma qo'shildi: §5 jadvalining «Частично "
            "восстановлено» qatori «уведомления: **да, по кварталам**» "
            "deydi, ya'ni «hodisa qisman tiklandi» degan natija xabar "
            "yuborilishini ham o'z ichiga oladi — va aynan o'sha "
            "kvartalning manzillariga"
        ),
    ),
    Case(
        code="ТС-211",
        check="Uzilish 6 soat, so'ralgan 4 tadan 3 tasi javob berdi",
        expects="Yopish mumkin, ulush pasaygan",
        path=(Stage.RESTORE, Stage.STATUS, Stage.NOTIFY_RESTORED),
        tests=("test_tz_restore.py",),
        walk="test_tz_walk_restore.py",
        state=State.BUILT,
        note=(
            "«Восстановлено» o'qi (hamma kvartal yopilgan → aniq "
            "davomiylik → xabar) 184-rungacha umuman yurilmagan edi. "
            "«Доля снижена» solishtirish bilan o'lchanadi: aynan shu "
            "javoblar birinchi soatda kvartalni yopmaydi. Oltinchi soat "
            "esa В-5 ning **qiyaligini** emas, `share_floor` ni "
            "o'lchaydi — pasayish beshinchi soatda chekka tushadi"
        ),
    ),
    Case(
        code="ТС-212",
        check="3 soat jimlik",
        expects="«Ma'lumot eskirgan», ikkita son, statistikada bor",
        path=(Stage.RESTORE, Stage.STATUS, Stage.NOTIFY_RESTORED),
        tests=("test_tz_restore.py",),
        walk="test_tz_walk_restore.py",
        state=State.BUILT,
        note=(
            "Bildirishnoma yo'lda **jimlikni** o'lchash uchun: §5 ning "
            "«Данные устарели» qatori «уведомления — нет» deydi, lekin "
            "jimlik statusga aylanishining sharti aynan kvartallarning "
            "bir qismi yopilgani. 184-run gacha bu jimlikni hech narsa "
            "qulflamasdi — `Closure` da yuborish huquqi umuman yo'q edi"
        ),
    ),
    Case(
        code="ТС-213",
        check="Odam oprosga javob bermadi",
        expects="Hech narsa o'zgarmadi",
        path=(Stage.RESTORE, Stage.STATUS, Stage.NOTIFY_RESTORED),
        tests=("test_tz_restore.py",),
        walk="test_tz_walk_restore.py",
        state=State.BUILT,
        note=(
            "«Ничего не изменилось» — butun yo'lning natijasi haqidagi "
            "da'vo, shuning uchun karta va yetkazishlar to'liq "
            "solishtiriladi. Yolg'iz o'zi kam: `share` ni umuman "
            "o'qimaydigan kod ham o'tardi, shuning uchun yonida qarama-"
            "qarshi holat turadi — «нет» maxrajga tushadi (В-6) va "
            "kvartal yopilmay qoladi"
        ),
    ),
    Case(
        code="ТС-214",
        check="Odam birinchi marta geolokatsiya yubordi",
        expects="Obuna yaratilmadi, savol berildi",
        path=(Stage.NOTIFY, Stage.NOTIFY_RESTORED),
        tests=("test_tz_outage_notice.py", "test_tz_restored_notice.py"),
        walk="test_tz_walk_notice.py",
        state=State.BUILT,
        note=(
            "Botning dialogi §11/5–6 da yozilmadi: bu yerda faqat obunaning "
            "yo'qligi o'lchanadi. Yo'l bo'ylab qo'shilgani (186-run): roziligi "
            "yo'q odam Т-9 ning jurnaliga **umuman tushmaydi**, ya'ni u §6.4 "
            "ning tuzatishi uchun ham ko'rinmas"
        ),
    ),
    Case(
        code="ТС-215",
        check="Uzilish 02:00 da tasdiqlandi",
        expects="Bildirishnoma ertalab keladi",
        path=(Stage.NOTIFY, Stage.NOTIFY_RESTORED),
        tests=("test_tz_outage_notice.py", "test_tz_restored_notice.py"),
        walk="test_tz_walk_notice.py",
        state=State.BUILT,
        note=(
            "186-run ning topilmasi shu bandning ostida: §6.2/4 «одним "
            "сводным сообщением» deydi va turni **nomlamaydi**. Ikkala "
            "modulning svodka testi ham bir turdagi yetkazishlar ustida "
            "yurardi, ya'ni tunda tasdiqlangan uzilish va o'sha tunda "
            "qaytgan svet bitta odamga ikkita xabar bo'lib chiqishi "
            "hech qayerda o'lchanmagan edi"
        ),
    ),
    Case(
        code="ТС-216",
        check="Sutkadagi 6-bildirishnoma",
        expects="Ushlab qolindi",
        path=(Stage.NOTIFY, Stage.NOTIFY_RESTORED),
        tests=("test_tz_outage_notice.py", "test_tz_restored_notice.py"),
        walk="test_tz_walk_notice.py",
        state=State.BUILT,
        note=(
            "Band bitta bildirishnoma turi bilan **umuman qurilmaydi**: "
            "§6.2/5 bir manzilga soatiga bitta uzilish xabarini beradi va "
            "§6.1 bir odamga uchtagacha manzil. Sutkada beshtaga yetish "
            "uchun ikkita hodisa va uchta manzil kerak, oltinchisi esa "
            "«свет вернулся» — chunki ikkinchi yarim turni nomlamaydi"
        ),
    ),
    Case(
        code="ТС-217",
        check="Uzilishni o'zi xabar qilgan odam",
        expects="Uzilish haqida xabar yo'q, svet qaytgani haqida bor",
        path=(Stage.NOTIFY, Stage.NOTIFY_RESTORED),
        tests=("test_tz_outage_notice.py", "test_tz_restored_notice.py"),
        walk="test_tz_walk_notice.py",
        state=State.BUILT,
        note=(
            "§10 ning yagona bandi bo'lib, u ikkala moduldan **qarama-"
            "qarshi** javob talab qiladi. Modulning o'z testi yarmini "
            "o'lchaydi va ikkala yarim ham yashil bo'lgani holda mahsulot "
            "buzuq bo'lishi mumkin: bir xil `Address` ro'yxati ikkala "
            "rejalashtiruvchiga berilmasa, farq ko'rinmaydi"
        ),
    ),
    Case(
        code="ТС-218",
        check="Tasdiqlangan uzilishni o'chirishga urinish",
        expects="Baza rad etadi",
        path=(Stage.SCHEMA,),
        tests=("test_outage_delete_guard.py", "test_outage_delete_reach.py"),
        walk=None,
        state=State.BUILT,
        note=(
            "Т-10, `0016`: qorovul `confirmed_at IS NOT NULL` ni o'qiydi, "
            "joriy statusni emas — aks holda «tasdiqla → yop → o'chir» "
            "taqiqni ikki qadamda chetlab o'tardi. Т-3 ning qayta "
            "hisoblashi uchun bitta ko'rinadigan teshik: "
            "`SET LOCAL` bayrog'i (`RECLUSTER_GUC`), faqat "
            "`app.clustering.repository.delete_outages` da. 189-run "
            "teshikning **kengligini** ham o'lchadi "
            "(`test_outage_delete_reach.py`): eshikning chaqiruvchisi "
            "bitta (`tools/recluster.py`), bayroqni qo'yish chaqiruv "
            "bo'yicha sanaladi (f-satr bilan yasalgan nom tripwire dan "
            "o'tib ketardi) va bayroq `DELETE` dan keyin **yopiladi** — "
            "`SET LOCAL` aks holda tranzaksiyaning qolgan qismida "
            "ochiq qolardi"
        ),
    ),
    Case(
        code="ТС-219",
        check="Sozlamada porogning o'zgarishi",
        expects="Yangi versiya, eskisi saqlanadi, chop etiladi",
        path=(Stage.SCHEMA,),
        tests=("test_schema.py", "test_schema_index_parity.py"),
        walk=None,
        state=State.BUILT,
    ),
    Case(
        code="ТС-220",
        check="Sozlama-son kodda",
        expects="Yig'ilish yiqiladi",
        path=(Stage.SCHEMA,),
        tests=(
            "test_tz_counting.py",
            "test_tz_operator.py",
            "test_tz_outage_notice.py",
            "test_tz_restore.py",
            "test_tz_restored_notice.py",
            "test_tz_scale.py",
            "test_tz_sensor.py",
        ),
        walk=None,
        state=State.BUILT,
        note=(
            "Har TZ moduli o'z Т-1 qorovulini olib yuradi — ro'yxat "
            "qo'lda emas, modul qo'shilishi bilan o'sadi"
        ),
    ),
)

CASE_BY_CODE: dict[str, Case] = {case.code: case for case in CASES}


@dataclass(frozen=True)
class Report:
    """§10 ning bugungi hisobi."""

    total: int
    built: int
    walked: int
    per_module: int
    unmeasured: int

    @property
    def clean(self) -> bool:
        """Hammasi qurilgan **va** uchidan-uchiga o'lchangan.

        Ikkala shart ham talab qilinadi: qurilgan, lekin yo'l bo'ylab
        yurilmagan band aynan modullar **orasida** yiqiladi va
        modulning o'z testi buni ko'rmaydi.
        """
        return self.built == self.total and self.walked == self.total


def evaluate() -> Report:
    """Ro'yxatdan hisob. Sonlar qo'lda yozilmaydi."""
    return Report(
        total=len(CASES),
        built=sum(1 for case in CASES if case.state is State.BUILT),
        walked=sum(1 for case in CASES if case.depth is Depth.WALKED),
        per_module=sum(1 for case in CASES if case.depth is Depth.PER_MODULE),
        unmeasured=sum(1 for case in CASES if case.depth is Depth.NONE),
    )
