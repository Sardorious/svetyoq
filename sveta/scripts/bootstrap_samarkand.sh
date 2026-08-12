#!/usr/bin/env bash
# =============================================================================
# Sveta.Net — Samarqand shahri uchun boshlang'ich konfiguratsiya.
# Deploydan KEYIN, serverda bir marta ishga tushiriladi (odam).
#
# Nima qiladi (E19 tartibi — `tools/region_admin.py` docstringi):
#   1. `samarkand` mintaqasini yaratadi (bbox, til=uz, `region_config` seed);
#   2. OSM dan tuman chegaralarini import qiladi (survey → stage → promote,
#      ADR-07: qaysi admin_level shahar tumanlari ekanini ODAM tanlaydi);
#   3. mintaqani faollashtiradi.
#
# Ishlatish:
#   bash scripts/bootstrap_samarkand.sh            # yo'l-yo'riqli to'liq oqim
#   bash scripts/bootstrap_samarkand.sh add        # faqat mintaqa yaratish
#   bash scripts/bootstrap_samarkand.sh survey     # faqat OSM darajalarini ko'rish
#   bash scripts/bootstrap_samarkand.sh stage 6    # tanlangan darajani yuklash
#   REFERENCE_REF=r123456 bash scripts/bootstrap_samarkand.sh stage 6
#                                                  # etalon relation id bo'yicha
#   bash scripts/bootstrap_samarkand.sh promote <BATCH-UUID>
#   bash scripts/bootstrap_samarkand.sh activate
#
# ⚠️ Mahalla poligonlari haqida (E17): `import_boundaries` hozircha faqat
# TUMAN darajasini yuklaydi. OSM da ayrim Samarqand mahallalari boundary
# obyektlari sifatida bor, lekin qamrov TO'LIQ EMAS (👤 qaror 2026-08-11:
# qisman qamrov bilan boshlash mumkin) — mahalla importi alohida ish (E17-a),
# hozircha xarita va statistika tuman + H3 kesimida ishlaydi.
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."   # -> sveta/

REGION_CODE="samarkand"
# Samarqand shahri + yaqin atrof (min_lat,min_lon,max_lat,max_lon).
# Ataylab kengroq: bbox — dag'al filtr, aniq biriktirish poligon bo'yicha.
BBOX="39.58,66.82,39.75,67.08"

# Overpass serveri. Asosiysi (overpass-api.de) tez-tez 504 beradi —
# unda oynani almashtiring:
#   OVERPASS_URL=https://overpass.kumi.systems/api/interpreter \
#       bash scripts/bootstrap_samarkand.sh survey
# Boshqa oynalar: https://overpass.osm.ch/api/interpreter
# Asbobning o'zi ham 429/502/503/504 da uch marta qayta urinadi (5/20/60 s).
OVERPASS_URL="${OVERPASS_URL:-}"

# Overpass javoblarini saqlash katalogi (konteyner ichida). Bo'sh bo'lsa —
# kesh ishlatilmaydi. Kesh yoqilganda muvaffaqiyatli javob faylga tushadi
# va keyingi urinish tarmoqqa **umuman chiqmaydi** — 504 seriyasida quvurni
# oldinga surishning yagona ishonchli yo'li (118-run).
#   CACHE_DIR=/tmp/osm bash scripts/bootstrap_samarkand.sh stage 6
# Yangi ma'lumot kerak bo'lsa katalogni tozalang:
#   docker compose exec -T api rm -rf /tmp/osm
CACHE_DIR="${CACHE_DIR:-}"

declare -a CACHE_ARGS=()

set_cache() {  # $1 — kesh fayli nomi (buyruq + daraja bo'yicha, aralashmasin)
    CACHE_ARGS=()
    [[ -z "${CACHE_DIR}" ]] && return 0
    docker compose exec -T api mkdir -p "${CACHE_DIR}" >/dev/null
    CACHE_ARGS=(--cache "${CACHE_DIR}/$1.json")
}

run() {  # konteyner ichida — DATABASE_URL compose dan keladi
    local tool="$1"; shift
    if [[ "${tool}" == "import_boundaries" && -n "${OVERPASS_URL}" ]]; then
        docker compose exec -T api python -m tools.import_boundaries \
            --overpass-url "${OVERPASS_URL}" "$@"
    else
        docker compose exec -T api python -m tools."${tool}" "$@"
    fi
}

cmd_add() {
    echo "== 1. Mintaqa yaratish: ${REGION_CODE} =="
    if run region_admin list | grep -q "\b${REGION_CODE}\b"; then
        echo "Mintaqa allaqachon bor — o'tkazib yuborildi."
    else
        run region_admin add \
            --code "${REGION_CODE}" \
            --name-uz "Samarqand" --name-ru "Самарканд" \
            --bbox "${BBOX}" --lang uz
        echo "Yaratildi (nofaol holda; region_config seed qilindi)."
    fi
}

cmd_survey() {
    echo "== 2. OSM darajalarini ko'rish (ADR-07 — tanlov SIZNIKI) =="
    # `survey` `out tags;` bilan so'raydi, `stage` esa `out geom;` — kesh
    # fayllari aralashmasligi uchun nomlar alohida.
    set_cache "survey"
    run import_boundaries survey --region "${REGION_CODE}" \
        ${CACHE_ARGS[@]+"${CACHE_ARGS[@]}"}
    echo
    echo "Yuqoridagi ro'yxatdan shahar TUMANLARIGA mos admin_level ni tanlang"
    echo "(O'zbekistonda shahar tumanlari odatda admin_level=8; viloyat=4,"
    echo " tuman/shahar=6). Keyin:  bash scripts/bootstrap_samarkand.sh stage <N>"
}

cmd_stage() {
    local level="${1:?admin_level kerak, masalan: stage 6}"
    echo "== 3. Staging: admin_level=${level} =="
    # Etalon: `REFERENCE_REF` berilsa — relation id bo'yicha (aniq hudud),
    # aks holda eski xulq-atvor (daraja bo'yicha). bbox to'rtburchak bo'lgani
    # uchun daraja bo'yicha etalon qo'shni hududlarni ham tortadi — id
    # afzalroq. Id larni `survey` chiqaradi.
    #   REFERENCE_REF=r123456 bash scripts/bootstrap_samarkand.sh stage 6
    set_cache "stage-${level}"
    if [[ -n "${REFERENCE_REF:-}" ]]; then
        run import_boundaries stage \
            --region "${REGION_CODE}" \
            --admin-level "${level}" --reference-ref "${REFERENCE_REF}" \
            ${CACHE_ARGS[@]+"${CACHE_ARGS[@]}"}
    else
        run import_boundaries stage \
            --region "${REGION_CODE}" \
            --admin-level "${level}" --reference-level 6 \
            ${CACHE_ARGS[@]+"${CACHE_ARGS[@]}"}
    fi
    echo
    echo "Sifat hisobotini ko'rib chiqing. Hammasi joyida bo'lsa:"
    echo "  bash scripts/bootstrap_samarkand.sh promote <BATCH-UUID>"
}

cmd_promote() {
    local batch="${1:?batch UUID kerak (stage chiqargan)}"
    echo "== 4. Promote: ${batch} =="
    run import_boundaries promote --batch "${batch}"
}

cmd_activate() {
    echo "== 5. Faollashtirish =="
    run region_admin activate --code "${REGION_CODE}"
    echo
    echo "✅ Samarqand faol. Tekshirish:"
    echo "   curl http://127.0.0.1:\${API_PORT:-8000}/api/v1/regions"
    echo "   Veb-xarita: http://<server>:\${WEB_PORT:-8080}/?region=${REGION_CODE}"
}

case "${1:-all}" in
    add)      cmd_add ;;
    survey)   cmd_survey ;;
    stage)    shift; cmd_stage "$@" ;;
    promote)  shift; cmd_promote "$@" ;;
    activate) cmd_activate ;;
    all)
        cmd_add
        cmd_survey
        echo
        read -r -p "admin_level kiriting (bo'sh = to'xtash): " LEVEL
        [[ -z "${LEVEL}" ]] && { echo "To'xtatildi — keyin stage bilan davom eting."; exit 0; }
        cmd_stage "${LEVEL}"
        echo
        read -r -p "BATCH-UUID kiriting (bo'sh = to'xtash): " BATCH
        [[ -z "${BATCH}" ]] && { echo "To'xtatildi — keyin promote bilan davom eting."; exit 0; }
        cmd_promote "${BATCH}"
        cmd_activate
        ;;
    *) echo "Noma'lum buyruq: $1 (add|survey|stage|promote|activate|all)"; exit 2 ;;
esac
