"""Davomiylik kesimi — `03` §R1.2 ning **uchinchi** kesimi (E14).

`03` §R1.2 vitrinani «hudud, davr, **davomiylik** kesimlarida» deb
belgilaydi. Birinchi ikkitasi bor edi: hudud — `districts`, davr —
`period`. Uchinchisining o'rnida esa bitta son turardi, `avg_duration_min`.
O'rtacha — kesim emas: u taqsimotni ko'rsatmaydi, uni yashiradi.

**Nima uchun aynan mediana va P90.** `01` §4 ikkita kuzatiladigan
ko'rsatkichni nomi bilan sanaydi: «Медианная длительность отключения»
(Toshkent bazasi — 44 daq) va «P90 длительности» (4 soat 11 daq).
Ikkalasi ham «target emas, kuzatiladigan qiymat» deb belgilangan, ya'ni
mahsulot ularni **o'lchay olishi** shart. O'rtachadan esa na mediana, na
P90 chiqadi. Ustiga, o'sha ikki bazaviy sonning o'zi taqsimot qanchalik
qiya ekanini ko'rsatadi: mediana 44 daqiqada, P90 esa undan olti barobar
uzoqda. Bunday taqsimotda o'rtacha mediananing ancha ustida yotadi va
**birorta ham** odatdagi uzilishni tasvirlamaydi.

`avg_duration_min` olib tashlanmadi: u javobda qoladi (mijozlar unga
tayangan bo'lishi mumkin), lekin endi yolg'iz emas.

**Uch xil hodisa — uch xil bilim.** Modul davomiylikni bitta ro'yxatga
qo'shib yubormaydi, chunki uchta holat bir xil ishonchga ega emas:

1. **O'lchangan** — hodisa yopilgan va yopilish vaqti kuzatilgan.
   Mediana va P90 **faqat** shulardan hisoblanadi.
2. **Davom etayotgan** (`ongoing`) — hodisa hali ochiq, davomiyligi
   yo'q. Uni «hozirgacha» deb hisoblash o'rtachani so'rov vaqtiga bog'lab
   qo'yardi (`aggregate.OutageFact.duration_min` shu sababdan `None`
   qaytaradi). Lekin u **yo'qolmaydi** ham: `unassigned` bilan bir xil
   qoida — kesimdan tushib qolgan narsa ko'rinib turishi kerak. Sababi
   statistik: ochiq qolganlar aynan **eng uzun** uzilishlar, ya'ni ular
   namunadan chiqib ketsa mediana pastga siljiydi.
3. **Taymer bilan yopilgan** (`timeout_closed`) — quyida.

**Taymer artefakti.** `05` §4.2 bo'yicha hodisa oxirgi xabardan
`autoclose_after` o'tgach o'z-o'zidan yopiladi. Bunday hodisaning
`resolved_at` i — **kuzatuv emas, taymer**: haqiqiy tiklanish oxirgi
xabar bilan taymer orasidagi qayerdadir bo'lgan va uni hech kim
ko'rmagan. Agar shunday hodisalar ko'p bo'lsa, «mediana davomiyligi»
degan raqam aslida `autoclose_after` ning aksi bo'lib qoladi va uni
o'lchov sifatida nashr etish yolg'on bo'lardi. Shuning uchun ularning
ulushi kesimda ochiq turadi va chegaradan oshsa ogohlantirish chiqadi.

Belgisi **saqlanmaydi, chiqariladi**: `resolved_at - last_report_at`
`autoclose_after` dan katta yoki teng bo'lsa — taymer. Bu
`app.clustering.status.evaluate_status` dagi shartning aynan o'zi, ya'ni
yangi ustun ham, `06` §10 ro'yxatidan chetlashish ham kerak emas.
⚠️ **Chegarasi:** baholash kechikib yurgizilsa (fon vazifasi to'xtab
qolgan bo'lsa), `restored` yoki `faded` bilan yopilgan hodisa ham shu
oraliqqa tushib qolishi mumkin. Ya'ni son — taymer bilan yopilganlarning
**yuqori** bahosi, aniq soni emas.

Modul **toza**: bazaga ham, konfiguratsiyaga ham murojaat qilmaydi.
Taymer chegarasi chaqiruvchidan keladi (`aggregate.build`), xuddi
`min_reports` kabi.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Narvonning ichki chegaralari, daqiqada. Beshta pog'ona hosil qiladi.
#:
#: Nima uchun aynan shular:
#:
#: - `30` — `01` §4 dagi bazaviy mediana (44 daq) dan **pastda**. Agar
#:   birinchi chegara mediananing ustida bo'lsa, hodisalarning yarmidan
#:   ko'pi bitta pog'onaga yig'ilardi va gistogramma hech narsa demasdi.
#: - `120` — standart `autoclose_after` (`05` §4.2) bilan bir xil qiymat:
#:   undan **pastdagi** yopilish taymer artefakti bo'lishi mumkin emas.
#: - `360` — bazaviy P90 (4 s 11 daq) dan **yuqorida**, ya'ni oxirgi
#:   o'ndan bir qism o'z pog'onasida qoladi.
#: - `1440` — sutka. Undan uzun uzilish boshqa hodisa: u avariya emas,
#:   uzoq ta'mirlash.
#:
#: Narvon **konfiguratsiyaga bog'lanmagan** va ataylab shunday. `120`
#: `autoclose_after` ning joriy qiymatiga teng bo'lsa ham, u sozlama
#: o'zgarganda siljimasligi kerak: aks holda ikki davrning gistogrammasi
#: turli narvonlarda qurilib, taqqoslab bo'lmas edi. Taymerning o'zi
#: alohida o'lchov — `timeout_closed`.
BAND_EDGES: tuple[int, ...] = (30, 120, 360, 1440)

#: Pog'ona kodlari — har doim shu tartibda va hammasi javobda, qiymati
#: nol bo'lsa ham (`aggregate.REPORTED_STATUSES` bilan bir xil sabab:
#: yo'q kalit «nol» dan boshqa narsani anglatardi).
BAND_CODES: tuple[str, ...] = (
    "under_30m",
    "30m_2h",
    "2h_6h",
    "6h_24h",
    "over_24h",
)

#: Davom etayotganlar shu ulushdan ko'p bo'lsa — mediana pastga siljigan.
MAX_ONGOING_RATIO = 0.20

#: Taymer bilan yopilganlar shu ulushdan ko'p bo'lsa — «davomiylik»
#: aslida `autoclose_after` ning aksi.
MAX_TIMEOUT_RATIO = 0.50

WARNING_ONGOING = "stats.warning.duration_ongoing"
WARNING_TIMEOUT = "stats.warning.duration_timeout"

#: Mediana va P90 shundan kam o'lchovda hisoblanmaydi. Uchta qiymatdan
#: chiqqan «P90» — eng katta qiymatning o'zi, ya'ni bitta hodisa haqidagi
#: ma'lumot statistika niqobida. `05` §7.3 ning ruhi shu.
MIN_SAMPLE = 5


def band_of(minutes: int) -> str:
    """Davomiylik qaysi pog'onaga tushadi.

    Chegara **pastki** pog'onaga tegishli emas: aynan 30 daqiqa —
    `30m_2h`. Aks holda «30 daqiqagacha» degan yorliq 30 ni ham o'z
    ichiga olardi.
    """
    for edge, code in zip(BAND_EDGES, BAND_CODES, strict=False):
        if minutes < edge:
            return code
    return BAND_CODES[-1]


def percentile(values: list[int], fraction: float) -> int | None:
    """Tartiblangan bo'lmagan ro'yxatdan persentil.

    Usul — PostgreSQL ning `percentile_cont` i: `rank = p*(n-1)`, ikkita
    qo'shni qiymat orasida chiziqli interpolyatsiya. Bu tanlov ixtiyoriy
    emas: `app.clustering.queries` dagi tasdiqlash kechikishi metrikasi
    ham `percentile_cont` bilan hisoblanadi, ya'ni mahsulotda «P90»
    so'zi bitta ma'noni anglatadi.

    Natija daqiqaga yaxlitlanadi: davomiylikning o'zi ham daqiqada.
    """
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = fraction * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    return round(ordered[low] + (ordered[high] - ordered[low]) * (rank - low))


@dataclass(frozen=True)
class DurationFact:
    """Bitta hodisaning davomiylik kesimi uchun neytral ko'rinishi.

    `aggregate.OutageFact` dan kichikroq: bu yerda na tuman, na status
    bor — davomiylik ularni ko'rmasligi kerak.
    """

    #: Yopilgan hodisaning davomiyligi; `None` — hali ochiq.
    duration_min: int | None
    #: Yopilishi taymer artefaktimi (`resolved_at - last_report_at`
    #: `autoclose_after` dan kam emas). Ochiq hodisada har doim `False`.
    closed_by_timeout: bool = False


@dataclass(frozen=True)
class DurationCut:
    """Vitrinaga chiqadigan davomiylik kesimi."""

    #: Davomiyligi o'lchangan hodisalar soni.
    measured: int
    #: Hali ochiq, ya'ni davomiyligi noma'lum hodisalar.
    ongoing: int
    #: O'lchanganlardan nechtasi taymer bilan yopilgan.
    timeout_closed: int
    median_min: int | None
    p90_min: int | None
    #: Pog'onalar bo'yicha taqsimot; kalitlar — `BAND_CODES`, hammasi bor.
    bands: dict[str, int]
    #: Namuna mediana va P90 uchun yetarlimi.
    sufficient: bool
    #: `MIN_SAMPLE` javobda ochiq turadi — `maturity` dagi `min_days`
    #: bilan bir xil sabab: mijoz chegarani o'zi ko'radi, o'ylab topmaydi.
    min_sample: int = MIN_SAMPLE

    @property
    def total(self) -> int:
        """Kesimga kirgan hodisalar soni: o'lchanganlar + ochiqlar.

        Bu `Bucket.outages_total` ga teng bo'lishi shart — davomiylik
        kesimi ham `03` §R1.2 ning «yig'indi umumiy natijaga teng»
        mezoniga bo'ysunadi.
        """
        return self.measured + self.ongoing

    @property
    def ongoing_ratio(self) -> float:
        return 0.0 if self.total == 0 else self.ongoing / self.total

    @property
    def timeout_ratio(self) -> float:
        """Taymer ulushi — **o'lchanganlar** ichida.

        Maxraj `total` emas: ochiq hodisa hali yopilmagan, ya'ni u
        taymer bilan yopilgan ham, kuzatilgan ham emas.
        """
        return 0.0 if self.measured == 0 else self.timeout_closed / self.measured

    @property
    def warnings(self) -> tuple[str, ...]:
        """Vitrinaga qo'yiladigan ogohlantirishlar.

        Namuna yetarli bo'lmaganda ogohlantirish **chiqmaydi**: mediana
        ham, P90 ham `None`, ya'ni ogohlantiradigan raqam yo'q.
        """
        if not self.sufficient:
            return ()
        keys: list[str] = []
        if self.ongoing_ratio > MAX_ONGOING_RATIO:
            keys.append(WARNING_ONGOING)
        if self.timeout_ratio > MAX_TIMEOUT_RATIO:
            keys.append(WARNING_TIMEOUT)
        return tuple(keys)


def summarize(facts: list[DurationFact]) -> DurationCut:
    """Faktlar ro'yxatidan davomiylik kesimi.

    Gistogramma **o'lchanganlar** bo'yicha quriladi: ochiq hodisaning
    pog'onasi yo'q va uni birortasiga qo'shish taqsimotni buzardi.
    Uning soni `ongoing` da alohida turadi.
    """
    durations: list[int] = []
    ongoing = 0
    timeout_closed = 0
    bands = dict.fromkeys(BAND_CODES, 0)

    for fact in facts:
        if fact.duration_min is None:
            ongoing += 1
            continue
        durations.append(fact.duration_min)
        if fact.closed_by_timeout:
            timeout_closed += 1
        bands[band_of(fact.duration_min)] += 1

    sufficient = len(durations) >= MIN_SAMPLE
    return DurationCut(
        measured=len(durations),
        ongoing=ongoing,
        timeout_closed=timeout_closed,
        median_min=percentile(durations, 0.5) if sufficient else None,
        p90_min=percentile(durations, 0.9) if sufficient else None,
        bands=bands,
        sufficient=sufficient,
    )
