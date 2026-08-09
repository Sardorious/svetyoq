"""Mahalla darajasidagi qamrov indeksi — toza modul (`01` §16, §21).

`01` §16 API deltasining to'rtinchi qatori ikkita talabdan iborat:
«Ответы статистики | Добавлено поле **версии справочника границ** и
**индекса покрытия махалли**». Birinchisi 25-sessiyada yozildi
(`app.stats.boundaries`), ikkinchisi esa umuman yo'q edi: qamrov indeksi
faqat tuman va mintaqa darajasida hisoblanardi. `01` §21 (Analytics)
o'sha talabni ikkinchi tomondan takrorlaydi — dashboardlar ro'yxatida
«Coverage Index по махаллям» alohida qator bo'lib turadi.

**Nima uchun tuman darajasi yetarli emas.** Tuman qamrovi — o'rtacha, va
o'rtacha aynan `01` §22 ogohlantiradigan xatoni takrorlaydi, faqat bir
daraja pastda: 30 ta faol xabar beruvchisi bor tuman «qamralgan» bo'lib
ko'rinadi, garchi ularning hammasi bitta mahalladan bo'lsa ham. Qolgan
mahallalar haqidagi sukunat esa «u yerda uzilish yo'q» deb o'qiladi —
`03` §R1.2 to'g'ridan-to'g'ri shundan ogohlantiradi. Mahalla — `01` §17
ning uchinchi geo-darajasi va `06` §5.3 masshtab narvonining o'rta
pog'onasi, ya'ni qamrov u yerda ham o'lchanishi kerak.

**Bo'sh spravochnik jim bo'lmaydi.** `mahallas` jadvali E17 gacha bo'sh
(`05` §2.1). Bo'sh ro'yxatdan hisoblangan indeks `0` bo'lardi va u
vitrinada «mahallalarning qamrovi nol» deb o'qilardi, aslida esa
«spravochnik hali to'ldirilmagan» — bu FR-S-802 **degradatsiyasi**, xato
emas, va u ko'rinishi shart (27-sessiyaning `GET /geo/mahallas` dagi
qarori bilan bir xil). Shuning uchun `available` bayrog'i va alohida
ogohlantirish kaliti bor: `unknown()` «bilmaymiz» deydi, `0` esa
«o'lchadik va nol chiqdi» degan boshqa gap.

Modul **toza**: bazaga ham, konfiguratsiyaga ham murojaat qilmaydi —
har bir mahallaning indeksi chaqiruvchida `app.stats.coverage.compute`
bilan hisoblanadi va bu yerga tayyor holda keladi.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.clustering.scale import QUALITY_UNKNOWN
from app.stats import coverage

#: Spravochnik umuman to'ldirilmaganda chiqadigan ogohlantirish
#: (FR-S-802 degradatsiyasi). `stats.warning.low_coverage` dan alohida:
#: u «o'lchadik, qamrov past» deydi, bu esa «o'lchay olmadik».
WARNING_MISSING = "stats.warning.mahallas_missing"

#: Spravochnik bor, lekin mahallalarning katta qismida `territory_stats`
#: qatori yo'q — indeks ular uchun `unknown` va o'rtacha ularni hisobga
#: olmaydi. Bu ham jim qolmasligi kerak.
WARNING_PARTIAL = "stats.warning.mahallas_unmeasured"

#: `measured / total` shu ulushdan past bo'lsa `WARNING_PARTIAL` chiqadi.
#: Yarmi — eng ehtiyotkor o'qish: ko'pchilik mahalla o'lchanmagan bo'lsa
#: o'rtacha qolgan ozchilikning xususiyati bo'lib qoladi.
MIN_MEASURED_RATIO = 0.5


@dataclass(frozen=True)
class MahallaFact:
    """Bitta mahallaning neytral kesimi + uning indeksi.

    Nomi ikki tilda saqlanadi, chunki javob tili so'rov darajasida hal
    qilinadi (`01` §16 — `Accept-Language` va mintaqaning standart tili),
    ya'ni bu yerda tanlash barvaqt bo'lardi.
    """

    id: uuid.UUID
    district_id: uuid.UUID
    district_code: str
    name_uz: str
    name_ru: str | None
    index: coverage.CoverageIndex

    def name(self, lang: str) -> str:
        """`name_ru` `mahallas` da nullable (`05` §2.1) — bo'sh bo'lsa UZ."""
        if lang == "ru" and self.name_ru:
            return self.name_ru
        return self.name_uz


@dataclass(frozen=True)
class MahallaCoverage:
    """Mahalla darajasidagi qamrovning vitrinaga chiqadigan kesimi."""

    #: Mintaqada mahalla qatori bormi. `total == 0` bilan bir xil emas:
    #: joriy kesim bo'sh bo'lsa ham spravochnik to'ldirilgan bo'lishi
    #: mumkin va bu ikki holat turli xulosaga olib keladi.
    available: bool
    #: Joriy kesimdagi mahallalar soni.
    total: int
    #: Ulardan nechtasida `territory_stats` qatori bor.
    measured: int
    #: O'lchangan mahallalar bo'yicha **o'rtacha** indeks — `region_index`
    #: bilan bir xil sabab: bitta yaxshi qamralgan mahalla butun
    #: kesimni «ishonchli» qilib ko'rsatmasligi kerak.
    index: coverage.CoverageIndex
    #: Pog'onalar bo'yicha taqsimot (`01` §21 dashboardi uchun). O'rtacha
    #: yashirib qo'yadigan narsa shu yerda ko'rinadi: `medium` o'rtacha
    #: yarim `high` va yarim `none` dan ham chiqishi mumkin.
    bands: dict[str, int]
    #: Ro'yxat `STATS_MAX_MAHALLAS` bilan kesildimi.
    truncated: bool
    items: tuple[MahallaFact, ...]

    @property
    def warnings(self) -> list[str]:
        """Vitrinada majburiy chiqadigan ogohlantirishlar (i18n kalitlari)."""
        if not self.available:
            return [WARNING_MISSING]
        if self.total > 0 and self.measured / self.total < MIN_MEASURED_RATIO:
            return [WARNING_PARTIAL]
        return []


def _mean_index(
    indexes: list[coverage.CoverageIndex], *, unmeasured: int
) -> coverage.CoverageIndex:
    """O'lchangan mahallalar bo'yicha o'rtacha indeks.

    `service.region_index` ning aynan takrori emas: u yerda `unknown`
    tumanlar ham o'rtachaga kiradi (tuman har doim mavjud va uning
    statistikasi yo'qligi — faktning o'zi). Mahallada esa `unknown`
    qatorlar **qiymatdan** chiqarib tashlanadi va ularning soni
    `measured` da alohida ko'rsatiladi: E17 dan keyin spravochnik
    to'lganda ham `territory_stats` mahallalar uchun **taxminiy** to'ladi
    (`06` §3.1 proksisi) va nollar bilan aralashtirilgan o'rtacha butun
    kesimni ma'nosiz qilardi.

    **Lekin sifatdan chiqarib tashlanmaydi** va bu yerdagi yagona
    nozik qaror shu. O'lchanmagan mahalla o'rtachaning **qiymatiga**
    qo'shilmaydi, ammo uning mavjudligi o'rtachaning **to'liqligi**
    haqidagi fakt: bitta o'lchanmagan qator qolgan bo'lsa ham «mahalla
    darajasida qamrov yuqori» degan da'vo chiqarib bo'lmaydi. Aks holda
    ikkitadan bittasi o'lchangan mintaqa `high` pog'onasini olardi va
    `measured` ni hech kim o'qimay qo'yardi — `service.region_index`
    dagi bilan bir xil qoida (`06` §5.4), faqat boshqa manbadan.
    """
    if not indexes:
        return coverage.unknown()
    mean = round(sum(i.index for i in indexes) / len(indexes))
    qualities = {i.data_quality for i in indexes}
    if unmeasured:
        qualities.add(QUALITY_UNKNOWN)
    quality = QUALITY_UNKNOWN if QUALITY_UNKNOWN in qualities else min(qualities)
    raw = coverage.band_of(mean)
    band = coverage.cap(raw, coverage.CoverageBand.LOW) if quality == QUALITY_UNKNOWN else raw
    return coverage.CoverageIndex(
        index=mean,
        band=band,
        raw_band=raw,
        sufficiency=sum(i.sufficiency for i in indexes) / len(indexes),
        spread=None,
        penetration=None,
        data_quality=quality,
        limiting_factor="mahalla_mean",
    )


def summarize(
    facts: list[MahallaFact], *, available: bool, truncated: bool = False
) -> MahallaCoverage:
    """Mahalla faktlaridan javobning `mahallas` blokini yig'adi.

    `available` **tashqaridan** keladi va ro'yxatdan hosila emas: joriy
    kesim bo'sh bo'lsa ham spravochnikda bekor qilingan qatorlar bo'lishi
    mumkin, ya'ni «hech qachon to'ldirilmagan» degan xulosani ro'yxatning
    o'zidan chiqarib bo'lmaydi.

    Pog'ona taqsimoti **barcha** mahallalar bo'yicha, o'lchanganlari
    bo'yicha emas: o'lchanmagan mahalla `none` chelagida emas, o'zining
    `unknown` sifati bilan `none` pog'onasida turadi va uni taqsimotdan
    chiqarib tashlash «hammasi o'lchangan» degan taassurot qoldirardi.
    Farqni `measured` soni ochib beradi.
    """
    bands = {str(band): 0 for band in coverage.BAND_ORDER}
    for fact in facts:
        bands[str(fact.index.band)] += 1

    measured = [f.index for f in facts if f.index.data_quality != QUALITY_UNKNOWN]
    return MahallaCoverage(
        available=available,
        total=len(facts),
        measured=len(measured),
        index=_mean_index(measured, unmeasured=len(facts) - len(measured)),
        bands=bands,
        truncated=truncated,
        items=tuple(facts),
    )


def missing() -> MahallaCoverage:
    """Spravochnik umuman to'ldirilmagan mintaqa (E17 gacha — har doim).

    Bo'sh `summarize([])` bilan bir xil emas edi deb o'ylash oson, lekin
    farq aynan `available` da va u javobda ko'rinadi: bu funksiya
    «spravochnik yo'q» deydi, `summarize([], available=True)` esa
    «spravochnik bor, joriy kesimda qator yo'q».
    """
    return summarize([], available=False)
