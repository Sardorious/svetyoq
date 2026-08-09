"""Mintaqaning ma'lumot chuqurligi — «yosh mintaqa» belgisi (FR-S-901).

**Nima uchun bu Coverage Index dan boshqa narsa.** Indeks fazoviy savolga
javob beradi: «hudud xabar beruvchilar bilan qamralganmi». Bu modul vaqt
savoliga javob beradi: «kuzatuv qancha vaqtdan beri olib borilmoqda va
statistik xulosa chiqarish uchun yetarlicha hodisa bo'lganmi». Ular
ustma-ust tushmaydi. Kecha ishga tushgan, lekin darhol mingta xabar
beruvchi yig'gan mintaqa **to'liq qamralgan** bo'lishi va shu bilan birga
hech qanday tarixiy taqqoslashga yaramasligi mumkin — bir kunlik kesimdan
«tumanlarning ishonchliligi» chiqmaydi.

`01` FR-S-901 (P0) aynan shuni talab qiladi: «Vitrina statistikasi
kuzatuvning ≥N oyi to'planmaguncha ma'lumot chuqurligi yetarli emasligi
haqidagi aniq pometa bilan birga ko'rsatiladi». `01` §23 qabul mezoni ham
buni sanaydi («Дисклеймер молодого региона активен»), `01` RS-10 esa
sababini aytadi: yosh statistika Toshkentnikiga qo'shib nashr etilsa,
o'quvchi ikkalasini bir xil chuqurlikdagi ma'lumot deb o'qiydi.

**Ikkita mustaqil shart.** FR-S-901 muddatni belgilaydi va `FR-901` dan
«<30 holat» ahamiyat chegarasini meros qilib oladi. Ular bir-birini
almashtirmaydi:

- uzoq tarix + kam hodisa — mintaqada uzilish kam bo'lgani ham, mahsulot
  ularni ko'rmagani ham bo'lishi mumkin, farqini ajratib bo'lmaydi;
- ko'p hodisa + qisqa tarix — bitta g'ayrioddiy hafta butun mintaqaning
  «odatdagi holati» bo'lib ko'rinadi.

Shuning uchun ikkalasidan biri bajarilmasa mintaqa **yosh** deb
belgilanadi va sabab(lar) javobda ochiq turadi.

**Tarix boshi — birinchi xabar, mintaqa qatorining sanasi emas.**
`regions` ga qator bir yil oldin qo'shilib, xabar kecha kelgan bo'lishi
mumkin; chuqurlik konfiguratsiyaning yoshi emas, kuzatuvning yoshi.

Modul **toza**: bazaga ham, konfiguratsiyaga ham murojaat qilmaydi —
qiymatlar chaqiruvchidan keladi.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

#: Sabab kodlari. Javobda `stats.maturity.reason.<kod>` kaliti sifatida
#: chiqadi — matn katalogda, `04` §6.
REASON_NO_HISTORY = "no_history"
REASON_SHORT_HISTORY = "short_history"
REASON_FEW_EVENTS = "few_events"

MESSAGE_YOUNG = "stats.maturity.young"
MESSAGE_MATURE = "stats.maturity.mature"

#: Vitrinaga qo'yiladigan ogohlantirish (`01` §23 «dislaymer faol»).
WARNING_YOUNG = "stats.warning.young_region"


@dataclass(frozen=True)
class MaturityInput:
    """Chuqurlikni hisoblash uchun kerakli faktlar."""

    #: Mintaqadagi eng birinchi xabarning vaqti; `None` — xabar yo'q.
    observed_since: datetime | None
    #: Butun tarix bo'yicha **tasdiqlangan** hodisalar soni. Tasdiqlanmagan
    #: hodisa «holat» emas: u shovqin ham bo'lishi mumkin edi.
    events: int
    now: datetime
    min_days: int
    min_events: int


@dataclass(frozen=True)
class Maturity:
    """Vitrinaga chiqadigan chuqurlik kesimi."""

    observed_since: datetime | None
    observed_days: int
    events: int
    is_young: bool
    #: Nima uchun yosh. Bo'sh — mintaqa yosh emas.
    reasons: tuple[str, ...]
    #: Chegaralar javobda ochiq turadi: mijoz «yosh» so'zining nimani
    #: anglatishini o'zi ko'ra oladi va uni o'ylab topmaydi.
    min_days: int
    min_events: int

    @property
    def message_key(self) -> str:
        return MESSAGE_YOUNG if self.is_young else MESSAGE_MATURE

    @property
    def reason_keys(self) -> tuple[str, ...]:
        return tuple(f"stats.maturity.reason.{code}" for code in self.reasons)


def compute(facts: MaturityInput) -> Maturity:
    """Faktlardan chuqurlik kesimini yig'adi.

    Kunlar **pastga yaxlitlanadi**: chegara `90` bo'lsa, 89.9 kunlik
    tarix hali 89 kun. Teskarisi «bugun 90 kun to'ldi» degan yolg'onni
    bir kun oldin aytardi.
    """
    if facts.observed_since is None:
        days = 0
    else:
        days = max(0, int((facts.now - facts.observed_since).total_seconds() // 86400))

    reasons: list[str] = []
    if facts.observed_since is None:
        reasons.append(REASON_NO_HISTORY)
    elif days < facts.min_days:
        reasons.append(REASON_SHORT_HISTORY)
    if facts.events < facts.min_events:
        reasons.append(REASON_FEW_EVENTS)

    return Maturity(
        observed_since=facts.observed_since,
        observed_days=days,
        events=facts.events,
        is_young=bool(reasons),
        reasons=tuple(reasons),
        min_days=facts.min_days,
        min_events=facts.min_events,
    )
