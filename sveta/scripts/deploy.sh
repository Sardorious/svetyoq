#!/usr/bin/env bash
# =============================================================================
# Sveta.Net — server deploy skripti (odam ishga tushiradi, agent emas).
#
# Nima qiladi:
#   1. .env ni tekshiradi (yo'q bo'lsa .env.example dan yaratadi);
#   2. MAP_TILE_URL bo'sh bo'lsa OSM qiymatini yozadi (👤 ADR-08, 2026-08-11);
#   3. git pull (--no-git bilan o'chiriladi);
#   4. docker compose build + up -d (db, migrate, api, jobs, web);
#   5. sog'liqni tekshiradi (API /health va web).
#
# Ishlatish (server, repo ildizidan bir daraja ichkarida — sveta/):
#   bash scripts/deploy.sh              # to'liq deploy
#   bash scripts/deploy.sh --no-git     # git pull siz (kod allaqachon yangi)
#
# Bot ataylab ko'tarilmaydi: token yo'q (E3 kutmoqda). Token paydo
# bo'lganda: TELEGRAM_BOT_TOKEN ni .env ga yozib,
#   docker compose --profile bot up -d bot
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."   # -> sveta/

NO_GIT=0
[[ "${1:-}" == "--no-git" ]] && NO_GIT=1

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

# --- 3. Kod ---
if [[ "$NO_GIT" -eq 0 ]]; then
    if [[ -f .git/index.lock || -f ../.git/index.lock ]]; then
        echo "⚠️  .git/index.lock topildi — avval uni o'chiring (del .git\\index.lock)."
        exit 1
    fi
    git pull --ff-only
fi

# --- 4. Build + up ---
# `jobs` profili MAJBURIY: usiz xarita snapshoti qurilmaydi (xarita bo'sh
# qoladi), bildirishnomalar yuborilmaydi, Coverage Index doim `unknown`.
docker compose build api migrate jobs
docker compose --profile jobs up -d db migrate api jobs web

# --- 5. Sog'liq ---
API_PORT="$(grep -E '^API_PORT=' .env | cut -d= -f2)"; API_PORT="${API_PORT:-8000}"
WEB_PORT="$(grep -E '^WEB_PORT=' .env | cut -d= -f2)"; WEB_PORT="${WEB_PORT:-8080}"

echo "-- migratsiya holati --"
docker compose logs migrate --tail 3 || true

echo "-- API sog'lig'i --"
for i in $(seq 1 20); do
    # ⚠️ Ildiz sathida `/health` YO'Q — u `/api/v1/health/live` da
    # (`app/api/router.py` `api_router` ni `settings.api_prefix` bilan ulaydi).
    # Eski `${API_PORT}/health` 404 qaytarardi va bu tekshiruv hech qachon
    # o'tmasdi (122-run topdi).
    if curl -fsS "http://127.0.0.1:${API_PORT}/api/v1/health/live" >/dev/null 2>&1; then
        echo "API OK (port ${API_PORT})"; break
    fi
    [[ "$i" -eq 20 ]] && { echo "❌ API 20 urinishda javob bermadi"; exit 1; }
    sleep 3
done

echo "-- Veb-xarita --"
if curl -fsS "http://127.0.0.1:${WEB_PORT}/" | grep -q "<html"; then
    echo "Web OK (port ${WEB_PORT})"
else
    echo "❌ web xizmati javob bermadi"; exit 1
fi

echo
echo "✅ Deploy tugadi."
echo "   Veb-xarita:  http://<server>:${WEB_PORT}/"
echo "   API:         http://<server>:${API_PORT}/api/v1/..."
echo
echo "Birinchi ishga tushirishda mintaqani sozlang:"
echo "   bash scripts/bootstrap_samarkand.sh"
