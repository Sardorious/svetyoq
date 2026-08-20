#!/usr/bin/env bash
# =============================================================================
# Sveta.Net — server deploy skripti (odam ishga tushiradi, agent emas).
#
# Nima qiladi:
#   1. .env ni tekshiradi (yo'q bo'lsa .env.example dan yaratadi);
#   2. MAP_TILE_URL bo'sh bo'lsa OSM qiymatini yozadi (👤 ADR-08, 2026-08-11);
#   3. git pull (--no-git bilan o'chiriladi);
#   4. rasmlarni yig'adi;
#   5. `db` ni KO'TARADI, LEKIN QAYTA YARATMAYDI (sozlamasi o'zgarmagan
#      bo'lsa compose ishlab turgan konteynerga umuman tegmaydi);
#   6. migratsiyani FAQAT KERAK BO'LSA yurgizadi — bazadagi
#      `alembic_version` repodagi head dan farq qilganda;
#   7. ilova konteynerlarini (`api`, `jobs`, `web`) HAR DOIM o'chirib,
#      yangisini yaratadi (`--force-recreate`);
#   8. sog'liqni tekshiradi (API /api/v1/health/live va web).
#
# ## Nega `db` va `migrate` alohida
#
# Eski skript `docker compose up -d db migrate api jobs web` deb bitta
# qatorda hammasini ko'tarardi. Ikkita natijasi bor edi:
#
#   * `migrate` HAR deployda qayta yurardi. `alembic upgrade head`
#     idempotent, ya'ni zarari yo'q — lekin u `db` ga ulanadi, qulf
#     oladi va deployni sekinlashtiradi; muhimi — logda «migratsiya
#     bajarildi» degan qator har safar chiqib, haqiqiy migratsiyani
#     shovqin ichida yashirardi.
#   * `api`/`jobs`/`web` esa TESKARISI: compose konteyner sozlamasi va
#     rasm ID si o'zgarmagan bo'lsa uni **qayta yaratmaydi**. Yangi kod
#     bilan rasm qayta yig'ilganda ID o'zgaradi va bu odatda ishlaydi,
#     lekin kesh tufayli ID o'zgarmay qolgan holatlarda eski konteyner
#     jimgina ishlab turaverardi va deploy «muvaffaqiyatli» ko'rinardi.
#
# Shuning uchun endi teskari: ilova konteynerlari **majburan** qayta
# yaratiladi, `db` esa **tegilmaydi**. `db` — yagona holat saqlaydigan
# xizmat (`pgdata` volume); uni sababsiz qayta yaratish downtime va
# xavf, foyda esa nol.
#
# Ishlatish (server, repo ildizidan bir daraja ichkarida — sveta/):
#   bash scripts/deploy.sh                 # to'liq deploy
#   bash scripts/deploy.sh --no-git        # git pull siz (kod allaqachon yangi)
#   bash scripts/deploy.sh --no-build      # rasmlarni qayta yig'masdan
#   bash scripts/deploy.sh --force-migrate # migratsiyani baribir yurgiz
#   bash scripts/deploy.sh --recreate-db   # `db` ni ham qayta yarat (ehtiyot!)
#
# Bot ataylab ko'tarilmaydi: token yo'q (E3 kutmoqda). Token paydo
# bo'lganda: TELEGRAM_BOT_TOKEN ni .env ga yozib,
#   docker compose --profile bot up -d bot
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."   # -> sveta/

NO_GIT=0
NO_BUILD=0
FORCE_MIGRATE=0
RECREATE_DB=0

for arg in "$@"; do
    case "$arg" in
        --no-git)        NO_GIT=1 ;;
        --no-build)      NO_BUILD=1 ;;
        --force-migrate) FORCE_MIGRATE=1 ;;
        --recreate-db)   RECREATE_DB=1 ;;
        -h|--help)       sed -n '1,50p' "$0"; exit 0 ;;
        *) echo "❌ noma'lum argument: $arg (--help)"; exit 2 ;;
    esac
done

echo "== Sveta.Net deploy: $(date -Is) =="

# --- 1. .env ---
if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "⚠️  .env yo'q edi — .env.example dan yaratildi."
    echo "⚠️  Sirlarni (TELEGRAM_BOT_TOKEN, ADMIN_* va h.k.) qo'lda to'ldiring!"
fi

# --- 2. ADR-08: MAP_TILE_URL bo'sh bo'lsa OSM (👤 qaror 2026-08-11) ---
if grep -qE '^MAP_TILE_URL=$' .env; then
    sed -i 's|^MAP_TILE_URL=$|MAP_TILE_URL=https://tile.openstreetmap.org/{z}/{x}/{y}.png|' .env
    echo "MAP_TILE_URL: OSM qiymati yozildi (ADR-08)."
fi
if grep -qE '^MAP_TILE_ATTRIBUTION=$' .env; then
    sed -i 's|^MAP_TILE_ATTRIBUTION=$|MAP_TILE_ATTRIBUTION=© OpenStreetMap contributors|' .env
    echo "MAP_TILE_ATTRIBUTION: OSM attributsiyasi yozildi."
fi

env_value() {
    # `.env` dan bitta qiymat; yo'q bo'lsa sukut qiymat.
    local key="$1" fallback="$2" found
    found="$(grep -E "^${key}=" .env | tail -1 | cut -d= -f2- || true)"
    echo "${found:-$fallback}"
}

PG_USER="$(env_value POSTGRES_USER sveta)"
PG_DB="$(env_value POSTGRES_DB sveta)"
API_PORT="$(env_value API_PORT 8000)"
WEB_PORT="$(env_value WEB_PORT 8080)"

# --- 3. Kod ---
if [[ "$NO_GIT" -eq 0 ]]; then
    if [[ -f .git/index.lock || -f ../.git/index.lock ]]; then
        echo "⚠️  .git/index.lock topildi — avval uni o'chiring (del .git\\index.lock)."
        exit 1
    fi
    git pull --ff-only
fi

# --- 4. Rasmlar ---
if [[ "$NO_BUILD" -eq 0 ]]; then
    docker compose build api migrate jobs
else
    echo "-- build o'tkazib yuborildi (--no-build) --"
fi

# --- 5. Baza: ko'tariladi, lekin sababsiz QAYTA YARATILMAYDI ---
# `up -d db` — idempotent: compose xizmatning sozlama xeshini solishtiradi
# va u o'zgarmagan bo'lsa ishlab turgan konteynerga **tegmaydi**. Ya'ni
# `docker-compose.yml` ning `db:` bloki va uning `.env` dagi
# o'zgaruvchilari (POSTGRES_*) o'zgarmasa — konteyner o'sha-o'sha qoladi.
if [[ "$RECREATE_DB" -eq 1 ]]; then
    echo "⚠️  --recreate-db: baza konteyneri MAJBURAN qayta yaratilmoqda."
    echo "⚠️  Ma'lumot pgdata volume da qoladi, lekin ulanishlar uziladi."
    docker compose up -d --force-recreate db
else
    docker compose up -d db
fi

echo "-- baza tayyor bo'lishini kutish --"
for i in $(seq 1 30); do
    if docker compose exec -T db pg_isready -h 127.0.0.1 -U "$PG_USER" -d "$PG_DB" >/dev/null 2>&1; then
        echo "DB OK"; break
    fi
    [[ "$i" -eq 30 ]] && { echo "❌ baza 30 urinishda javob bermadi"; exit 1; }
    sleep 2
done

# --- 6. Migratsiya: faqat kerak bo'lsa ---
# «Kerakmi» degan savolga javobni **baza** beradi, git emas: bazadagi
# `alembic_version` repodagi head bilan solishtiriladi. Bu `--no-git`
# bilan ham, qo'lda ko'chirilgan kod bilan ham to'g'ri ishlaydi, va
# oldingi deploy yarmida uzilib qolgan holatni ham ko'radi.
#
# ⚠️ Quyidagi `echo` larda `${VAR:-<matn>}` ning sukut qismida APOSTROF
# ishlatilmaydi (`<yo'q>`, `<bo'sh>` — YO'Q). Qo'shtirnoq ichidagi
# `${...:-...}` ning sukut qismini bash ALOHIDA parse qiladi va
# o'sha yerdagi `'` haqiqiy qo'shtirnoqni **ochadi** — butun fayl
# `unexpected EOF while looking for matching` bilan yiqiladi, xato esa
# faylning oxirgi qatorida ko'rsatiladi. Bu `.ps1` dagi uzun tire
# minasining bash ko'rinishi (CLAUDE.md §2).
repo_heads() {
    # Head — hech bir faylda `down_revision` sifatida uchramaydigan
    # reviziya. Fayl nomiga tayanilmaydi: nom o'zgarsa ham javob to'g'ri.
    local revs downs
    revs="$(grep -hoE '^revision[^=]*= *"[^"]+"' alembic/versions/*.py \
            | sed -E 's/.*"([^"]+)".*/\1/' | sort -u)"
    downs="$(grep -hoE '^down_revision[^=]*= *"[^"]+"' alembic/versions/*.py \
            | sed -E 's/.*"([^"]+)".*/\1/' | sort -u)"
    comm -23 <(echo "$revs") <(echo "$downs")
}

db_heads() {
    # Jadval yo'q bo'lsa (birinchi deploy) — bo'sh javob.
    docker compose exec -T db psql -U "$PG_USER" -d "$PG_DB" -tAc \
        "SELECT version_num FROM alembic_version ORDER BY 1" 2>/dev/null \
        | tr -d '\r' | sed '/^$/d' | sort -u
}

REPO_HEAD="$(repo_heads | paste -sd, -)"
DB_HEAD="$(db_heads | paste -sd, - || true)"

echo "-- migratsiya: repo=${REPO_HEAD:-<NONE>} baza=${DB_HEAD:-<EMPTY>} --"

NEED_MIGRATE=0
if [[ "$FORCE_MIGRATE" -eq 1 ]]; then
    NEED_MIGRATE=1
    echo "   --force-migrate: baribir yurgiziladi."
elif [[ -z "$REPO_HEAD" ]]; then
    # Head topilmadi (masalan reviziyalar halqa yasagan) — taxmin
    # qilmaymiz, alembic o'zi hal qilsin.
    NEED_MIGRATE=1
    echo "   ⚠️  repodagi head aniqlanmadi — migratsiya baribir yurgiziladi."
elif [[ "$REPO_HEAD" != "$DB_HEAD" ]]; then
    NEED_MIGRATE=1
fi

if [[ "$NEED_MIGRATE" -eq 1 ]]; then
    echo "-- alembic upgrade head --"
    docker compose run --rm --no-deps -T migrate
    NEW_HEAD="$(db_heads | paste -sd, - || true)"
    echo "   baza endi: ${NEW_HEAD:-<EMPTY>}"
else
    echo "   o'zgarish yo'q — migratsiya O'TKAZIB YUBORILDI."
fi

# --- 7. Ilova konteynerlari: har doim yangidan ---
# `--force-recreate` — eski konteyner to'xtatiladi, o'chiriladi va
# o'rniga yangisi yaratiladi (rasm ID si o'zgarmagan bo'lsa ham).
# `--no-deps` MAJBURIY: usiz compose `depends_on` bo'yicha `migrate` ni
# qayta yurgizar va yuqoridagi qaror bekor bo'lardi; `db` ni ham
# tekshiruvga tortardi.
echo "-- ilova konteynerlari qayta yaratilmoqda --"
docker compose --profile jobs up -d --force-recreate --no-deps api jobs web

# --- 8. Sog'liq ---
echo "-- API sog'lig'i --"
for i in $(seq 1 20); do
    # ⚠️ Ildiz sathida `/health` YO'Q — u `/api/v1/health/live` da
    # (`app/api/router.py` `api_router` ni `settings.api_prefix` bilan ulaydi).
    # Eski `${API_PORT}/health` 404 qaytarardi va bu tekshiruv hech qachon
    # o'tmasdi (122-run topdi).
    if curl -fsS "http://127.0.0.1:${API_PORT}/api/v1/health/live" >/dev/null 2>&1; then
        echo "API OK (port ${API_PORT})"; break
    fi
    [[ "$i" -eq 20 ]] && {
        echo "❌ API 20 urinishda javob bermadi"
        docker compose logs api --tail 30 || true
        exit 1
    }
    sleep 3
done

echo "-- Veb-xarita --"
if curl -fsS "http://127.0.0.1:${WEB_PORT}/" | grep -q "<html"; then
    echo "Web OK (port ${WEB_PORT})"
else
    echo "❌ web xizmati javob bermadi"
    docker compose logs web --tail 30 || true
    exit 1
fi

echo
echo "✅ Deploy tugadi."
if [[ "$NEED_MIGRATE" -eq 1 ]]; then
    echo "   Migratsiya:   yurgizildi (${DB_HEAD:-<EMPTY>} -> ${REPO_HEAD})"
else
    echo "   Migratsiya:   kerak bo'lmadi (${REPO_HEAD})"
fi
if [[ "$RECREATE_DB" -eq 1 ]]; then
    echo "   db:           MAJBURAN qayta yaratildi (--recreate-db)"
else
    echo "   db:           tegilmadi (sozlamasi o'zgarmagan bo'lsa o'sha konteyner)"
fi
echo "   api/jobs/web: o'chirilib, yangidan yaratildi (--force-recreate)"
echo "   Veb-xarita:  http://<server>:${WEB_PORT}/"
echo "   API:         http://<server>:${API_PORT}/api/v1/..."
echo
echo "Birinchi ishga tushirishda mintaqani sozlang:"
echo "   bash scripts/bootstrap_samarkand.sh"
