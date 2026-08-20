"""TZ §8 — operatorning qarori: bahsli holatni yopish va uzilishni yakunlash.

§8 operatorga to'rt narsani ruxsat etadi va bittasini taqiqlaydi.
To'rttadan **ikkitasi** allaqachon ulangan: «внести официальный
источник» va «отметить плановые работы» — ikkalasi ham
`app/reports/tzsensor.py` ning `Channel.OPERATOR` kanali va
`POST /api/v1/tz/readings` orqali ketadi (179-run). Qolgan ikkitasi —
«подтвердить или отклонить спорный случай» va «закрыть аварию» — shu
modulda.

## Nima uchun alohida modul, `tzsensor` ga qo'shilmadi

Datchik va rasmiy manba **katak** haqida gapiradi: «bu yerda svet
yo'q». Operatorning qarori esa **hodisa** haqida: «bu hodisa haqiqiy»
yoki «bu hodisa tasdiqlanmadi». Ikkalasini bitta jadvalga qo'shish
farqni yo'qotardi, holbuki u §8 ning o'zagi: signal — dalil, qaror —
vakolat. Dalilni har qanday manba beradi, qarorni faqat operator
beradi va u har doim **imzolanadi**.

🔴 **§8 ning taqiqi shu yerda o'lchanadi.** «Не может: создать
подтверждение по собственному мнению без внешнего источника.» Erkin
matnli «asos» maydoni bu taqiqni bajara olmaydi: unga istalgan so'zni
yozish mumkin. Shuning uchun shakl operatordan **asosning turini**
so'raydi (`Basis`), va `CONFIRM` + `Basis.JUDGEMENT` birikmasi rad
etiladi. Bu operatorni tekshirmaydi — u yolg'on tanlashi mumkin —
lekin taqiqni **ko'rinadigan** qiladi: jurnalda «tasdiqladi, asos —
o'z fikri» degan qator hech qachon paydo bo'lmaydi, va nazoratchi
uchun bu bitta `SELECT`.

🔴 **Rad etish o'z fikri bilan mumkin.** §8 faqat **tasdiqlashni**
tashqi manbasiz taqiqlaydi. Rad etish da'vo yaratmaydi, aksincha —
tasdiqlanmagan da'voni olib tashlaydi, ya'ni taqiqning sababi unga
qo'llanmaydi. «Закрыть аварию» ni ham tashqi manba bilan cheklash
mumkin edi, lekin bu spetsifikatsiyadan qat'iyroq bo'lardi va
`PROGRESS.md` ning «Ochiq savollar» iga yozildi.

🔴 **Qaror abadiy emas.** Operator o'zi **ko'rgan** qarshi dalillarni
qarorga yozadi (`seen`). Keyin yangi akkaunt «menda svet bor» desa,
veto qaytadi: bir marta bosilgan tugma hodisani §2.2 dan butunlay
himoyalab qo'ysa, to'suvchi uchun eng arzon yo'l operatorni bir marta
chalg'itish bo'lardi. Bu qoida `tzstatus.Resolution.covers()` da
yashaydi va shu yerdagi `seen` uni to'ldiradi.

🔴 **Rad etilgan amal ham jurnalga tushadi.** §8: «Все действия
пишутся в журнал с указанием, кто и на основании чего.» «Amal» —
bosilgan tugma, natija emas. Muvaffaqiyatsiz urinishlarni yozmaslik
jurnalni aynan eng qiziq qatorlardan mahrum qilardi: kim tasdiqlashni
o'z fikri bilan o'tkazmoqchi bo'lgani ko'rinmasdi.

## Т-5 saqlanadi

Bu modul statusni **tanlamaydi** va `TzStatus` ni umuman import
qilmaydi. U qaror qabul qilinishi mumkinmi degan savolga javob beradi
va `resolution_fields()` bilan lug'at qaytaradi; tipni chaqiruvchi
yasaydi (`tzsensor.verified_fields()` dagi bilan bir xil naqsh, xuddi
shu sabab bilan: `admin` va `clustering` bir-birini import qilmasin).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

__all__ = [
    "SPEC",
    "Action",
    "Basis",
    "Decision",
    "Incident",
    "POWERS",
    "Power",
    "Refusal",
    "Request",
    "action_key",
    "decide_action",
    "resolution_fields",
]

SPEC = "TZ §8"


class Action(StrEnum):
    """§8 ning birinchi ikkita vakolati, uchta tugma sifatida.

    «Подтвердить или отклонить спорный случай» — bitta jumla, ikkita
    qarama-qarshi amal; «закрыть аварию» — uchinchisi. Qolgan ikkita
    vakolat (`rasmiy manba`, `rejali ishlar`) bu ro'yxatda **yo'q**:
    ular signal kanali orqali ketadi va `POWERS` da shunday yozilgan.
    """

    #: Bahsli holat tasdiqlandi → «Проверено оператором».
    CONFIRM = "confirm"
    #: Bahsli holat tasdiqlanmadi → tasdiq berilmaydi, §6.4 tuzatish.
    REJECT = "reject"
    #: Uzilish yakunlandi (operator yopdi).
    CLOSE = "close"


class Basis(StrEnum):
    """«На основании чего» ning **turi**, matnning o'zidan alohida.

    Matn nima bo'lganini aytadi, tur esa uni qaerdan olganini aytadi.
    §8 ning taqiqi ikkinchisiga tegishli, shuning uchun u alohida
    maydon: erkin matnda «RES qo'ng'irog'i» deb yozish ham, hech
    narsa yozmaslik ham bir xil oson.
    """

    #: Rasmiy e'lon, RES ga qo'ng'iroq, datchik — tashqi dalil.
    EXTERNAL = "external"
    #: Operatorning xabarlardan chiqargan o'z xulosasi.
    JUDGEMENT = "judgement"


class Refusal(StrEnum):
    """Amal bajarilmagan bo'lsa — nima uchun.

    `NONE` bo'shliq o'rniga: jurnalda `CHECK (accepted = (refusal =
    'none'))` ikkala da'voni bitta qatorda ushlab turadi (179-run
    ning `tz_signals` idagi bilan bir xil qaror).
    """

    NONE = "none"
    #: §8 ning taqiqi: tasdiqlash + o'z fikri.
    OWN_JUDGEMENT = "own_judgement"
    #: «Спорный случай» emas — tasdiqlash/rad etish uchun narsa yo'q.
    NOT_DISPUTED = "not_disputed"
    #: Hodisa allaqachon yopilgan.
    ALREADY_CLOSED = "already_closed"


#: Kalitning uzunligi — `tzsensor.KEY_DIGEST_BYTES` bilan bir xil
#: sinf: bu tarmoq/baza o'lchami, §7 ning sozlamasi emas.
KEY_DIGEST_BYTES = 16


@dataclass(frozen=True)
class Request:
    """Operator bosgan tugma va uning imzosi.

    `actor` va `reference` bo'sh bo'la olmaydi — bu **shaklning**
    xatosi, `Refusal` emas: §8 imzosiz amalni umuman tasavvur
    qilmaydi, ya'ni bunday so'rov yuborilmasligi kerak
    (`tzsensor.Reading` da xuddi shu qaror, xuddi shu sabab bilan).
    """

    action: Action
    #: Hodisaning identifikatori — shaffof matn (jurnal hodisadan
    #: uzoqroq yashaydi, `tz_receipts` dagi bilan bir xil sabab).
    incident_id: str
    #: §8: «кто».
    actor: str
    #: §8: «на основании чего» — matn.
    reference: str
    #: §8 ning taqiqi o'lchanadigan maydon.
    basis: Basis
    #: Qaror qachon qabul qilingan (Т-4: chaqiruvchi beradi).
    at: datetime
    #: Operator ko'rgan qarshi dalil akkauntlari (§2.2 ning
    #: `Rebuttals.users` i). Bo'sh bo'lishi mumkin — `CLOSE` uchun u
    #: umuman ishlatilmaydi.
    seen: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.actor.strip() or not self.reference.strip():
            raise ValueError(f"{SPEC}: imzosiz amal bo'lmaydi — «кто и на основании чего»")
        if not self.incident_id.strip():
            raise ValueError(f"{SPEC}: hodisasiz qaror bo'lmaydi")


@dataclass(frozen=True)
class Incident:
    """Qaror qabul qilinayotgan hodisaning holati — **ikkita bayroq**.

    `TzStatus` bu yerga kirmaydi: Т-5 statuslar to'plamini ikkinchi
    marta e'lon qilishni taqiqlaydi, va statusdan kelib chiqadigan
    ikkita savolni chaqiruvchi allaqachon biladi. Shu bilan modul
    `app.clustering` ni umuman import qilmaydi.
    """

    incident_id: str
    #: §2.2 ishlagan (yoki oldin ishlagan) — «спорный случай».
    disputed: bool
    #: Hodisa yopilganmi (tiklandi yoki operator yopgan).
    closed: bool = False
    #: Bugungi qarshi dalil akkauntlari — `seen` bilan solishtiriladi
    #: emas, jurnalga yoziladi: qaror qaysi manzarada qabul qilingani
    #: keyin tekshiriladigan yagona narsa.
    rebuttal_users: tuple[str, ...] = ()


@dataclass(frozen=True)
class Decision:
    """Qarorning natijasi. Rad etilgan bo'lsa ham jurnalga yoziladi."""

    request: Request
    accepted: bool
    refusal: Refusal
    #: Т-7: bir xil tugmaning ikkinchi bosilishi ikkinchi qator
    #: yaratmaydi.
    key: str
    #: Ko'rilgan qarshi dalillar — qarorning **qamrovi**.
    seen: tuple[str, ...] = ()
    #: Diagnostika uchun qo'shimcha izohlar.
    notes: dict[str, Any] = field(default_factory=dict)

    @property
    def resolves(self) -> bool:
        """Bu qaror §2.2 ning vetosini yopadimi."""
        return self.accepted and self.request.action in (Action.CONFIRM, Action.REJECT)

    @property
    def confirms(self) -> bool:
        """«Проверено оператором» ga olib boradimi."""
        return self.accepted and self.request.action is Action.CONFIRM

    @property
    def closes(self) -> bool:
        """Hodisani yopadimi."""
        return self.accepted and self.request.action is Action.CLOSE


def action_key(request: Request) -> str:
    """Т-7 ning kaliti: kim, nima, qaysi hodisada, qachon.

    `blake2b`, Python ning `hash()` i emas — u har protsessda
    tasodifiylanadi va jurnalning kaliti qayta ishga tushirilgandan
    keyin boshqa bo'lib qolardi.

    Asos matni kalitga **kirmaydi**: bir xil daqiqada bir xil tugmani
    boshqa izoh bilan ikkinchi marta bosish — o'sha qaror, va uning
    ikkinchi qatori jurnalni sinonimlar bilan to'ldirardi.
    """
    digest = hashlib.blake2b(digest_size=KEY_DIGEST_BYTES)
    digest.update(request.actor.strip().encode("utf-8"))
    digest.update(b"|")
    digest.update(request.action.value.encode("utf-8"))
    digest.update(b"|")
    digest.update(request.incident_id.strip().encode("utf-8"))
    digest.update(b"|")
    digest.update(request.at.isoformat().encode("utf-8"))
    return digest.hexdigest()


def decide_action(request: Request, incident: Incident) -> Decision:
    """§8: amal bajariladimi va bajarilmasa — nima uchun.

    Tartib ataylab shunday: avval hodisaning holati, keyin §8 ning
    taqiqi. Yopilgan hodisada «tasdiqlash o'z fikri bilan» degan
    xabar chalg'ituvchi bo'lardi — operator birinchi navbatda
    hodisaning allaqachon yopilganini bilishi kerak.
    """
    seen = tuple(dict.fromkeys(request.seen)) or incident.rebuttal_users
    key = action_key(request)

    def refuse(reason: Refusal) -> Decision:
        return Decision(
            request=request, accepted=False, refusal=reason, key=key, seen=seen
        )

    if incident.closed:
        return refuse(Refusal.ALREADY_CLOSED)
    if request.action in (Action.CONFIRM, Action.REJECT) and not incident.disputed:
        # §8 birinchi vakolatni «спорный случай» bilan cheklaydi.
        # Bahssiz hodisani «tasdiqlash» — aynan taqiqlangan narsa:
        # u odamlarning hisobini operatorning qo'li bilan
        # almashtirardi.
        return refuse(Refusal.NOT_DISPUTED)
    if request.action is Action.CONFIRM and request.basis is not Basis.EXTERNAL:
        return refuse(Refusal.OWN_JUDGEMENT)

    return Decision(
        request=request, accepted=True, refusal=Refusal.NONE, key=key, seen=seen
    )


def resolution_fields(decision: Decision) -> dict[str, Any]:
    """`tzstatus.Resolution` ning maydonlari — **lug'at**, tip emas.

    Т-5 ning naqshi: `admin` `clustering` ni import qilmaydi va
    aksincha. Tipni chaqiruvchi yasaydi, moslikni test qulflaydi.
    """
    request = decision.request
    return {
        "confirmed": decision.confirms,
        "actor": request.actor,
        "reference": request.reference,
        "at": request.at,
        "saw": frozenset(decision.seen),
    }


def journal_fields(decision: Decision) -> dict[str, Any]:
    """Jurnal qatorining maydonlari (§8 ning oxirgi jumlasi)."""
    request = decision.request
    return {
        "incident_id": request.incident_id,
        "action": request.action.value,
        "basis": request.basis.value,
        "actor": request.actor,
        "reference": request.reference,
        "accepted": decision.accepted,
        "refusal": decision.refusal.value,
        "seen": list(decision.seen),
        "decided_at": request.at,
        "key": decision.key,
    }


def latest(decisions: Iterable[Decision]) -> Decision | None:
    """Vaqt bo'yicha oxirgi **qabul qilingan** qaror.

    Rad etilgan urinish hech narsani yopmaydi — u jurnalda qoladi,
    lekin statusga ta'sir qilmaydi. Teng vaqtda kalit bo'yicha
    tartiblanadi: Т-3 bir xil kirishda bir xil natijani talab qiladi
    va vaqt bu yerda yagona emas.
    """
    accepted = [item for item in decisions if item.resolves or item.closes]
    if not accepted:
        return None
    return max(accepted, key=lambda item: (item.request.at, item.key))


# --------------------------------------------------------------------------
# Reyestr — `app.admin.registries` shuni o'qiydi
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Power:
    """§8 ning bitta vakolati va uning haqiqiy kirish yo'li.

    `wired` — operator amalni bugun **bajara oladimi** va u jurnalga
    tushadimi. `need` — shundan keyin qolgan ish. Ikkalasi ataylab
    ajratilgan (`tzsensor.Inbound` dagi bilan bir xil qaror): «tugma
    bor» va «tugma hodisaning holatini o'zgartiradi» — turli
    da'volar, va ularni bitta bayroqqa qo'shish reyestrni yolg'onga
    aylantirardi.
    """

    code: str
    note: str
    #: Qaysi modul bajaradi.
    where: str
    #: Operator uni bugun bajara oladimi (amal yozib olinadimi).
    wired: bool
    #: Shundan keyin nima yetishmayapti. Bo'sh satr — hech narsa.
    need: str = ""


POWERS: tuple[Power, ...] = (
    Power(
        code="resolve_dispute",
        note="подтвердить или отклонить спорный случай",
        where="app.admin.tzoperator + POST /tz/operator/actions",
        wired=True,
        # `tzstatus.decide()` ni mahsulot quvuri hali chaqirmaydi —
        # butun TZ qatlami mavjud E5 klasterlashining yonida turadi.
        # Buni `01` §7 ning DP-4 qorovuli alohida o'lchaydi; bu yerda
        # u yashirilmaydi.
        need="qaror hodisaning statusiga yetmaydi (DP-4)",
    ),
    Power(
        code="close_outage",
        note="закрыть аварию",
        where="app.admin.tzoperator + POST /tz/operator/actions",
        wired=True,
        need="qaror hodisaning statusiga yetmaydi (DP-4)",
    ),
    Power(
        code="mark_planned",
        note="отметить плановые работы",
        where="app.reports.tzsensor Signal.PLANNED + POST /tz/readings",
        wired=True,
    ),
    Power(
        code="add_source",
        note="внести официальный источник",
        where="app.reports.tzsensor Channel.OPERATOR + POST /tz/readings",
        wired=True,
    ),
)
