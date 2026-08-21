/*
 * Sveta.Net veb-xaritasi (E9, `05` §7.1).
 *
 * Sahifa hech narsani hisoblamaydi: u `GET /api/v1/map` dan tayyor GeoJSON
 * oladi. Snapshot serverda 60 soniyada bir marta yig'iladi, javob esa
 * `ETag` + `Cache-Control: max-age=60` bilan keladi — ya'ni sahifani tez-tez
 * yangilash ham bazaga qo'shimcha yuk bermaydi.
 *
 * Matn: barcha satr `GET /api/v1/map/i18n` dan (`04` §6). Bu faylda
 * foydalanuvchiga ko'rinadigan qattiq kodlangan satr yo'q.
 *
 * Tayl manbasi: `GET /api/v1/map/config` dan. Bo'sh bo'lsa (ADR-08 hali
 * ochiq) fon rasmisiz, faqat nuqtalar ko'rsatiladi.
 */
(function () {
  "use strict";

  var API = (window.SVETA_API_BASE || "/api/v1").replace(/\/$/, "");
  var params = new URLSearchParams(window.location.search);
  var region = params.get("region") || "";
  /* Til uch bosqichda (`01` §16). Bu yerda faqat **ochiq** tanlov
     o'qiladi: `?lang=` yoki brauzer tili, agar u qo'llab-quvvatlansa.
     Aks holda `lang` bo'sh qoladi va tanlovni **server** qiladi —
     `/map/config` javobidagi `language` mintaqaning `default_language`
     idan keladi. Ilgari bu yerda `"uz"` qattiq yozilgan edi va ruscha
     mintaqadagi ingliz brauzeri o'zbekcha sahifani ochardi. */
  var lang = params.get("lang") || "";
  if (!lang) {
    var browser = (navigator.language || "").slice(0, 2).toLowerCase();
    if (browser === "uz" || browser === "ru") lang = browser;
  }
  if (lang !== "uz" && lang !== "ru") lang = "";

  var strings = {};
  var map = null;
  var config = null;
  var timer = null;
  var heatOn = false;

  function t(key, vars) {
    var value = strings[key];
    if (value === undefined) return "";
    if (!vars) return value;
    return value.replace(/\{(\w+)\}/g, function (whole, name) {
      return Object.prototype.hasOwnProperty.call(vars, name) ? vars[name] : whole;
    });
  }

  function applyStrings() {
    document.documentElement.lang = lang;
    var langSelect = document.getElementById("lang");
    langSelect.value = lang;
    /* Ikkala tanlagichning ham ko'rinadigan yorlig'i yo'q — ularning
       yagona nomi `aria-label`, ya'ni u ekran o'quvchi o'qiydigan
       **foydalanuvchi matni**. Shuning uchun ikkalasi ham katalogdan
       keladi va ikkalasi ham **shu yerda** qo'yiladi: `applyStrings`
       til almashganda qayta chaqiriladi.

       `#region` niki ilgari `fillRegions` da qo'yilardi — u esa faqat
       bir marta, sahifa qurilayotganda chaqiriladi, ya'ni til
       almashganda nom eskisida qolardi. Bu `tiles` uyasi bilan aynan
       bitta sinf (95-run): til almashganda qayta hisoblanmaydigan
       yagona matn. Atribut `lang` ning sof hosilasi, shuning uchun
       uni bu yerga ko'chirish xavfsiz va `fillRegions` faqat
       ro'yxatni quradi. */
    langSelect.setAttribute("aria-label", t("map.language"));
    document.getElementById("region").setAttribute("aria-label", t("map.region"));
    document.title = t("map.title");
    var nodes = document.querySelectorAll("[data-i18n]");
    for (var i = 0; i < nodes.length; i++) {
      nodes[i].textContent = t(nodes[i].getAttribute("data-i18n"));
    }
    /* Bannerning `tiles` uyasi ham shu yerda qayta hisoblanadi, chunki u
       — sahifadagi yagona i18n matni bo'lib, o'zidan keyin **hech qachon
       qayta yozilmaydi**: `map` uyasini `refresh()`, `heat` uyasini
       `refreshHeat()` har tikda yangilaydi, `tiles` esa faqat bir marta,
       xarita qurilayotganda qo'yilardi. Til almashganda (`#lang` ning
       `change` i `applyStrings` ni chaqiradi) qolgan ikkitasi yangi
       tilga o'tar, `tiles` esa eskisida qolardi — ya'ni ADR-08 ochiq
       bo'lgan bugungi holatda (tayl manbasi yo'q, demak bu uya deyarli
       doim to'la) banner **aralash tilda** ko'rinardi.

       Uya `config` ning sof hosilasi, shuning uchun uni qayta hisoblash
       xavfsiz: shart har chaqiruvda bir xil javob beradi. Shu sababdan
       `baseStyle()` endi bannerga umuman yozmaydi va sof funksiya
       bo'lib qoladi. */
    banner("tiles", config && !hasBase(config) ? t("map.tiles_missing") : "");
  }

  /* Bannerda ekranda bitta joy bor, unga yozadigan **mustaqil** manba esa
     uchta: tayl manbasining yo'qligi (`baseStyle`), xarita snapshotining
     holati (`refresh`) va zichlik qatlamining ogohlantirishi
     (`refreshHeat`). Ilgari uchalasi bitta argumentli `banner()` ni
     chaqirardi, ya'ni oxirgi chaqiruv oldingisini **jimgina o'chirardi**.
     Bu uchta yozilgan qoidani buzardi:

     1. `map.tiles_missing` xarita qurilayotganda qo'yiladi va birinchi
        `refresh()` (bir necha yuz millisekunddan keyin) uni o'chirardi —
        foydalanuvchi fonsiz xaritani sababsiz ko'rardi;
     2. `!data.sufficient` ogohlantirishi keyingi `refresh()` tikida
        (`refresh_s`, kamida 15 s) yo'qolardi, zichlik qatlami esa
        ko'rinishda qolardi — aynan quyidagi §`refreshHeat` izohi
        taqiqlagan holat: «kam ma'lumotli xaritani jimgina chizish undan
        noto'g'ri xulosa chiqarishga olib kelardi»;
     3. `setHeat(false)` ning `banner("")` i xaritaning o'z
        `map.empty` tushuntirishini o'chirardi (`01` §13 `UX-S3`).

     Endi har manbaning o'z uyasi bor va matn ulardan **yig'iladi**, ya'ni
     hech bir manba boshqasini o'chira olmaydi. `reload` tugmasi
     `refresh()` va `refreshHeat()` ni birga chaqiradi — uyalarsiz natija
     qaysi so'rov oldin tugashiga bog'liq, ya'ni noaniq edi.
     Bir xil matn (masalan ikkala so'rov ham `map.error` bergani)
     takrorlanmaydi. */
  var notices = { tiles: "", map: "", heat: "" };

  function banner(slot, message) {
    notices[slot] = message || "";
    var text = [notices.tiles, notices.map, notices.heat]
      .filter(function (part, i, all) {
        return part && all.indexOf(part) === i;
      })
      .join(" · ");
    var el = document.getElementById("banner");
    el.textContent = text;
    el.hidden = !text;
  }

  function qs(extra) {
    var q = new URLSearchParams();
    if (region) q.set("region", region);
    if (extra) for (var k in extra) q.set(k, extra[k]);
    var s = q.toString();
    return s ? "?" + s : "";
  }

  function getJson(path) {
    /* `lang` bo'sh bo'lsa sarlavha umuman yuborilmaydi — shunda server
       mintaqaning standart tilini tanlaydi. Bo'sh `Accept-Language`
       yuborish esa «hech qanday til yaramaydi» degani bo'lardi. */
    var headers = lang ? { "Accept-Language": lang } : {};
    return fetch(API + path, { headers: headers }).then(function (r) {
      if (!r.ok) throw new Error(String(r.status));
      return r.json();
    });
  }

  /* Fon rasmi bo'lmasa ham xarita ishlaydi: bo'sh (rasmsiz) style.
     Tushuntirish bannerga bu yerdan emas, `applyStrings()` dan
     yoziladi — sabab o'sha funksiyaning izohida. */
  /* Fon bormi. `baseStyle()` dan AYRI, chunki bir xil savolga ikkita
     joyda javob berilardi: banner `!cfg.tile_url` ni o'zi tekshirardi
     va `style_url` qo'shilgan kunda u fon bor bo'lgan xaritada
     `map.tiles_missing` deb yozib qo'yardi. Endi ikkovi ham shundan
     o'qiydi. */
  function hasBase(cfg) {
    return Boolean(cfg.style_url || cfg.tile_url);
  }

  function baseStyle(cfg) {
    /* Uchta holat, va ularning TARTIBI ma'noli:

       1. `style_url` — tayyor vektor stil (👤 ADR-08, 2026-08-21:
          OpenFreeMap Liberty). MapLibre `style` ga **satr** ni ham
          qabul qiladi va stilni o'zi yuklaydi; uni quyidagi rastr
          obyektiga o'rab bo'lmaydi, chunki style JSON `{z}/{x}/{y}`
          shabloni emas — ya'ni bu ikkita alohida yo'l, bitta
          sozlamaning ikki qiymati emas.
       2. `tile_url` — rastr shablon; style ni shu funksiya yasaydi.
       3. ikkovi ham bo'sh — bo'sh (rasmsiz) style.

       Ustunlik `style_url` da va u SERVERDA hal bo'ladi (`/map/config`
       ikkala maydonni ham beradi): tanlovni sahifaga qoldirish ikkita
       chiqishni (sahifa va sozlama) ikki xil javobga ajratardi. */
    if (cfg.style_url) {
      return cfg.style_url;
    }
    if (!cfg.tile_url) {
      return { version: 8, sources: {}, layers: [] };
    }
    return {
      version: 8,
      sources: {
        base: {
          type: "raster",
          tiles: [cfg.tile_url],
          tileSize: 256,
          attribution: cfg.tile_attribution || "",
        },
      },
      layers: [{ id: "base", type: "raster", source: "base" }],
    };
  }

  var EMPTY = { type: "FeatureCollection", features: [] };

  /* Zichlik shkalasi (E16). Pog'onalar serverdan `level` bo'lib keladi,
     ya'ni rangni sahifa emas, `app/stats/heatmap.py` hal qiladi — shkala
     ikki joyda ajralib ketmasligi uchun. */
  var HEAT_COLORS = ["#f6e8c3", "#f2c66b", "#e8a33d", "#e2703d", "#c9302c"];

  function addLayers() {
    /* Issiqlik qatlami hodisalardan PASTDA turadi: u fon, nuqtalar esa
       asosiy ma'lumot. Shu sababli avval qo'shiladi. */
    map.addSource("heatmap", { type: "geojson", data: EMPTY });
    map.addLayer({
      id: "heat-fill",
      type: "fill",
      source: "heatmap",
      layout: { visibility: "none" },
      paint: {
        "fill-color": [
          "step",
          ["get", "level"],
          HEAT_COLORS[0],
          2, HEAT_COLORS[1],
          3, HEAT_COLORS[2],
          4, HEAT_COLORS[3],
          5, HEAT_COLORS[4],
        ],
        "fill-opacity": 0.45,
      },
    });
    map.addLayer({
      id: "heat-outline",
      type: "line",
      source: "heatmap",
      layout: { visibility: "none" },
      paint: { "line-color": "#ffffff", "line-width": 0.5, "line-opacity": 0.5 },
    });
    map.on("click", "heat-fill", function (e) {
      var p = e.features[0].properties;
      var popup = new maplibregl.Popup({ closeButton: true }).setLngLat(e.lngLat);
      var box = document.createElement("div");
      box.className = "popup";
      var row = document.createElement("div");
      row.textContent = t("heatmap.cell", { count: p.reports, people: p.reporters });
      box.appendChild(row);
      popup.setDOMContent(box).addTo(map);
    });

    map.addSource("outages", { type: "geojson", data: EMPTY });

    /* Radius — metrda. `circle-radius` piksel bo'lgani uchun izni
       ko'rsatishga alohida qatlam kerak emas: nuqta o'lchami `radius_m`
       ga qarab o'sadi, aniq chegara esa baribir taxminiy. */
    map.addLayer({
      id: "outage-halo",
      type: "circle",
      source: "outages",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["get", "radius_m"], 0, 10, 3000, 46],
        "circle-color": [
          "match",
          ["get", "status"],
          "confirmed", "#e2483d",
          "#e8a33d",
        ],
        "circle-opacity": 0.22,
      },
    });
    /* `A11Y-06` (`01` §14: «Статус кодируется цветом **и** формой»,
       `UX-S7` orqali WCAG 2.1 AA).

       Bu yerda rang yagona tashuvchi bo'lishi haqiqiy xavf edi:
       `#e2483d` (tasdiqlangan) va `#e8a33d` (kutilmoqda) — qizil va
       sariq, ya'ni deyteranopiya/protanopiyada deyarli farqsiz, va
       ular aynan bir-biridan ajratilishi kerak bo'lgan ikki holat.
       Ilgari uchala status bir xil doira edi: `circle-radius` ham,
       `circle-stroke-*` ham konstanta.

       Shakllar **sprite siz** quriladi. Bu majburiy: ADR-08 hali ochiq,
       ya'ni `baseStyle()` bo'sh (rasmsiz) style qaytarishi mumkin va
       unda na ikonka atlasi, na glif serveri bor — `symbol` qatlami
       yoki `text-field` u yerda jimgina chizilmasdi.

       - tasdiqlangan — **to'ldirilgan** doira (`заливка`);
       - kutilmoqda — **ichi bo'sh** halqa (`пунктир` ning sprite siz
         muqobili: MapLibre ning `circle` konturi punktir bo'la olmaydi);
       - rasmiy e'lon — **halqa + markaz** (`иконка`), ikkinchi qatlam
         bilan.

       Rang ikkala shaklda ham qoladi, faqat boshqa xossada: to'ldirilgan
       doirada — to'ldirishda (kontur oq halo), ichi bo'sh halqada —
       konturning o'zida. Aks holda «rang **va** shakl» jimgina «faqat
       shakl» ga aylanardi. */
    var STATUS_COLOR = [
      "case",
      ["==", ["get", "layer"], "official"], "#3d6fe2",
      ["==", ["get", "status"], "confirmed"], "#e2483d",
      "#e8a33d",
    ];
    /* Bitta predikat uchala xossada: to'ldirish, kontur qalinligi va
       kontur rangi bir-biriga zid bo'lib qolmasligi kerak. Rasmiy e'lon
       `status` dan **ustun** — yuqoridagi rang ifodasidagi tartib ham
       shunday, ya'ni `official` + `confirmed` yozuvi ikkala xossada bir
       xil (rasmiy) shaklni oladi. */
    var SOLID = [
      "all",
      ["!=", ["get", "layer"], "official"],
      ["==", ["get", "status"], "confirmed"],
    ];
    map.addLayer({
      id: "outage-point",
      type: "circle",
      source: "outages",
      paint: {
        "circle-radius": 7,
        "circle-color": STATUS_COLOR,
        "circle-opacity": ["case", SOLID, 0.95, 0.12],
        "circle-stroke-width": ["case", SOLID, 2, 3],
        "circle-stroke-color": ["case", SOLID, "#ffffff", STATUS_COLOR],
      },
    });
    /* «Иконка» — halqa **va** markaz. Alohida qatlam, chunki bitta
       `circle` ikkita konsentrik shakl chiza olmaydi. Faqat rasmiy
       e'londa ko'rinadi, ya'ni u qolgan ikkala shakldan bir qarashda
       ajraladi. Bosish hodisasi bu qatlamga ulanmaydi: u `outages`
       manbasining o'sha nuqtasini chizadi, `outage-point` ning
       ishlovchisi esa baribir ishlaydi. */
    map.addLayer({
      id: "outage-official-core",
      type: "circle",
      source: "outages",
      filter: ["==", ["get", "layer"], "official"],
      paint: {
        "circle-radius": 2.5,
        "circle-color": "#3d6fe2",
      },
    });

    map.on("click", "outage-point", function (e) {
      var f = e.features[0];
      var p = f.properties;
      var lines = [
        t(p.status === "confirmed" ? "map.legend.confirmed" : "map.legend.pending"),
        t("outage.scale." + p.scale),
        t("map.reports", { count: p.report_count }),
        t("map.started", { time: shortTime(p.started_at) }),
        t("map.confidence", { value: p.confidence }),
      ].filter(Boolean);
      var popup = new maplibregl.Popup({ closeButton: true }).setLngLat(
        f.geometry.coordinates
      );
      var box = document.createElement("div");
      box.className = "popup";
      lines.forEach(function (line) {
        var row = document.createElement("div");
        row.textContent = line; /* textContent — HTML injection yo'q */
        box.appendChild(row);
      });
      popup.setDOMContent(box).addTo(map);
    });
    map.on("mouseenter", "outage-point", function () {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", "outage-point", function () {
      map.getCanvas().style.cursor = "";
    });
  }

  function shortTime(iso) {
    if (!iso) return "";
    var d = new Date(iso);
    if (isNaN(d.getTime())) return "";
    return d.toLocaleTimeString(lang, { hour: "2-digit", minute: "2-digit" });
  }

  function refresh() {
    return getJson("/map" + qs())
      .then(function (data) {
        banner(
          "map",
          data.stale ? t("map.stale") : data.features.length ? "" : t("map.empty")
        );
        var src = map && map.getSource("outages");
        if (src) src.setData(data);
        document.getElementById("updated").textContent = data.built_at
          ? t("map.updated", { time: shortTime(data.built_at) })
          : "";
      })
      .catch(function () {
        banner("map", t("map.error"));
      });
  }

  /* Zichlik qatlami (E16, `GET /api/v1/heatmap`).

     Alohida so'rov: snapshot 60 soniyada yangilanadi, zichlik esa
     davr bo'yicha hisoblanadi va serverda 15 daqiqa keshlanadi. Ularni
     bitta so'rovga qo'shish keshning ma'nosini yo'qotardi.

     `sufficient: false` bo'lsa qatlam baribir ko'rsatiladi, lekin
     bannerda ogohlantirish chiqadi: kam ma'lumotli xaritani jimgina
     chizish undan noto'g'ri xulosa chiqarishga olib kelardi. */
  /* Qamrov indeksi legendada (`03` §R1.2 — «har bir vitrina indeks
     bilan», `01` PG-S4 — 100%).

     Matn qattiq yozilmaydi: server pog'onaning i18n kalitini beradi
     (`coverage.message_key`), sahifa esa uni katalogdan oladi. Kalit
     kelmasa qator umuman ko'rsatilmaydi — «qamrov noma'lum» degan bo'sh
     yorliq indeksni bor deb ko'rsatgan yolg'on bo'lardi. */
  function showCoverage(coverage) {
    var box = document.getElementById("heat-coverage");
    var text = document.getElementById("heat-coverage-text");
    if (!box || !text) return;
    if (!coverage || !coverage.message_key) {
      box.hidden = true;
      return;
    }
    text.textContent = t(coverage.message_key) + " (" + coverage.index + "/100)";
    box.hidden = false;
  }

  /* Yosh mintaqa pometasi (`01` FR-S-901 P0, §23).

     Qamrov qatorining yonida, lekin undan mustaqil: mintaqa to'liq
     qamralgan bo'lib, ayni paytda ikki haftalik tarixga ega bo'lishi
     mumkin. Yetuk mintaqada qator yashiriladi — doimiy ogohlantirish
     ogohlantirish bo'lishdan to'xtaydi. */
  function showMaturity(maturity) {
    var box = document.getElementById("heat-maturity");
    var text = document.getElementById("heat-maturity-text");
    if (!box || !text) return;
    if (!maturity || !maturity.is_young) {
      box.hidden = true;
      return;
    }
    var reasons = (maturity.reason_keys || []).map(t).join("; ");
    text.textContent = t(maturity.message_key) + (reasons ? " — " + reasons : "");
    box.hidden = false;
  }

  function refreshHeat() {
    if (!heatOn || !map) return Promise.resolve();
    return getJson("/heatmap" + qs())
      .then(function (data) {
        var src = map.getSource("heatmap");
        if (src) src.setData(data);
        showCoverage(data.coverage);
        showMaturity(data.maturity);
        /* `else` shart: ogohlantirish o'z uyasida turgani uchun endi uni
           hech kim o'chirmaydi, ya'ni ma'lumot yetarli bo'lgan keyingi
           javobdan keyin u **yopishib qolardi**. Ilgari buni
           `refresh()` ning ustiga yozishi tasodifan qoplardi. */
        if (data.warning_texts && data.warning_texts.length && !data.sufficient) {
          banner("heat", data.warning_texts[data.warning_texts.length - 1]);
        } else {
          banner("heat", "");
        }
      })
      .catch(function () {
        banner("heat", t("map.error"));
      });
  }

  function setHeat(on) {
    heatOn = on;
    var visibility = on ? "visible" : "none";
    ["heat-fill", "heat-outline"].forEach(function (id) {
      if (map && map.getLayer(id)) map.setLayoutProperty(id, "visibility", visibility);
    });
    document.getElementById("heat-legend").hidden = !on;
    /* Faqat **o'z** uyasi tozalanadi: xaritaning `map.empty` yoki
       `map.stale` tushuntirishi qatlamni o'chirishga bog'liq emas. */
    if (on) refreshHeat();
    else banner("heat", "");
  }

  /*
   * Mintaqa tanlagichi (E19). Ro'yxat serverdan keladi; bitta mintaqa
   * bo'lsa tanlagich ko'rsatilmaydi — bo'sh tanlov faqat chalg'itardi.
   * Tanlov sahifani `?region=` bilan qayta ochadi: xarita, zichlik qatlami
   * va statistika hammasi shu parametrga bog'liq, ya'ni ularni joyida
   * almashtirishdan ko'ra qayta yuklash sodda va xatosizroq.
   */
  function fillRegions() {
    var select = document.getElementById("region");
    var rows = (config && config.regions) || [];
    /* `aria-label` bu yerdan olib tashlandi — u `applyStrings` da,
       qolgan barcha matn bilan bitta joyda (sabab o'sha yerda). */
    if (rows.length < 2) {
      select.hidden = true;
      return;
    }
    select.innerHTML = "";
    rows.forEach(function (row) {
      var option = document.createElement("option");
      option.value = row.code;
      option.textContent = row.name;
      select.appendChild(option);
    });
    select.value = config.region;
    select.hidden = false;
    select.addEventListener("change", function (e) {
      var next = new URLSearchParams(window.location.search);
      next.set("region", e.target.value);
      window.location.search = next.toString();
    });
  }

  function boot() {
    /* Tartib muhim: avval `/map/config`, u tilni **hal qiladi**, keyin
       shu til bilan katalog. Ikkalasini parallel so'rash mumkin emas
       edi — sahifa qaysi tilni so'rashini hali bilmaydi. */
    getJson("/map/config" + qs())
      .then(function (cfg) {
        config = cfg;
        if (!lang) lang = cfg.language;
        return getJson("/map/i18n" + qs({ locale: lang }));
      })
      .then(function (data) {
        strings = data;
        applyStrings();
        fillRegions();
        map = new maplibregl.Map({
          container: "map",
          style: baseStyle(config),
          center: [config.center_lon, config.center_lat],
          zoom: config.zoom,
          /* Atributsiya rastr yo'lida manbaning o'zida turadi
             (`baseStyle` dagi `attribution`), stil yo'lida esa uni
             faqat stilning ichidagi qiymat berardi — ya'ni bizning
             `MAP_TILE_ATTRIBUTION` imiz ekranga umuman chiqmasdi.
             Litsenziya talabi esa sozlamada yozilgan matnga tegishli,
             shuning uchun u stil yo'lida ochiq qo'shiladi. Rastr
             yo'lida qo'shilmaydi — ikki marta chiqardi. */
          attributionControl: config.style_url
            ? { customAttribution: config.tile_attribution || "" }
            : undefined,
        });
        map.addControl(new maplibregl.NavigationControl(), "top-right");
        map.on("load", function () {
          addLayers();
          refresh();
          if (timer) clearInterval(timer);
          timer = setInterval(refresh, Math.max(config.refresh_s, 15) * 1000);
        });
      })
      .catch(function () {
        banner("map", "…"); /* i18n hali yuklanmagan — neytral belgi */
      });
  }

  document.getElementById("reload").addEventListener("click", function () {
    refresh();
    refreshHeat();
  });
  document.getElementById("heat").addEventListener("change", function (e) {
    setHeat(e.target.checked);
  });
  /* Tanlagichning boshlang'ich qiymati serverdan kelgandan keyin
     qo'yiladi (`applyStrings`) — bu paytda `lang` hali bo'sh bo'lishi
     mumkin. */
  document.getElementById("lang").addEventListener("change", function (e) {
    lang = e.target.value;
    getJson("/map/i18n" + qs({ locale: lang })).then(function (data) {
      strings = data;
      applyStrings();
      refresh();
      refreshHeat();
    });
  });

  boot();
})();
