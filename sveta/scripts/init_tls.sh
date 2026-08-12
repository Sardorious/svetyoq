#!/usr/bin/env bash
# =============================================================================
# Sveta.Net — birinchi TLS sertifikati (odam ishga tushiradi, agent emas).
#
# ⚠️ FAQAT xostda nginx BO'LMAGAN serverda. Joriy serverda xost nginx
# droneguard.uz ni xizmat qilyapti va 80/443 band — u yerda sertifikat
# xostdagi certbot bilan olinadi:
#     sudo certbot --nginx -d bormitok.uz -d www.bormitok.uz
# (`deploy-server/bormitok.uz.nginx.conf` ga qarang).
#
# Muammo: nginx `ssl_certificate` fayli yo'q bo'lsa UMUMAN ko'tarilmaydi,
# certbot esa tekshiruv faylini berish uchun ishlayotgan nginx ni talab
# qiladi. Klassik tuxum-tovuq. Yechim uch qadamda:
#   1. vaqtinchalik o'z-o'zini imzolagan sertifikat qo'yiladi;
#   2. nginx ko'tariladi (80 va 443 ochiladi);
#   3. certbot HTTP-01 bilan haqiqiy sertifikatni oladi va nginx qayta
#      yuklanadi.
#
# Ishlatish (server, `sveta/` papkasidan):
#   bash scripts/init_tls.sh --email siz@example.com
#   bash scripts/init_tls.sh --email siz@example.com --staging   # sinov uchun
#
# ⚠️ Oldindan: DNS `bormitok.uz` (va `www`) shu serverga ko'rsatishi, 80 va
# 443 portlari band bo'lmasligi kerak (`ss -lntp | grep -E ':80|:443'`).
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."   # -> sveta/

DOMAIN=bormitok.uz
WWW_DOMAIN=www.bormitok.uz
EMAIL=""
STAGING=0
COMPOSE=(docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml)

while [[ $# -gt 0 ]]; do
    case "$1" in
        --email) EMAIL="${2:-}"; shift 2 ;;
        --staging) STAGING=1; shift ;;
        *) echo "noma'lum argument: $1"; exit 2 ;;
    esac
done

if [[ -z "$EMAIL" ]]; then
    echo "❌ --email kerak (Let's Encrypt muddat tugashi haqida shu manzilga yozadi)"
    exit 2
fi

echo "== TLS: $DOMAIN =="

# --- 1. Vaqtinchalik sertifikat ---
# `certbot/certbot` rasmi ichida openssl bor, ya'ni serverga hech narsa
# o'rnatilmaydi. Yo'l konteyner ichidagi volume ga yoziladi.
echo "-- vaqtinchalik sertifikat --"
"${COMPOSE[@]}" run --rm --entrypoint /bin/sh certbot -c "
    set -e
    mkdir -p /etc/letsencrypt/live/$DOMAIN
    if [ ! -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
        openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
            -keyout /etc/letsencrypt/live/$DOMAIN/privkey.pem \
            -out   /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
            -subj '/CN=$DOMAIN'
        echo 'vaqtinchalik sertifikat qo'\''yildi'
    else
        echo 'sertifikat allaqachon bor — o'\''tkazib yuborildi'
    fi
"

# --- 2. nginx ---
echo "-- web ko'tarilmoqda --"
"${COMPOSE[@]}" up -d web
sleep 3

# --- 3. Haqiqiy sertifikat ---
echo "-- Let's Encrypt --"
STAGING_ARG=""
[[ "$STAGING" -eq 1 ]] && STAGING_ARG="--staging"

"${COMPOSE[@]}" run --rm --entrypoint certbot certbot \
    certonly --webroot -w /var/www/certbot \
    -d "$DOMAIN" -d "$WWW_DOMAIN" \
    --email "$EMAIL" --agree-tos --no-eff-email \
    --force-renewal $STAGING_ARG

echo "-- nginx qayta yuklanmoqda --"
"${COMPOSE[@]}" exec web nginx -s reload

# --- 4. Tekshirish ---
echo "-- tekshiruv --"
curl -fsS -o /dev/null -w "https://%{host} -> %{http_code}\n" "https://$DOMAIN/" \
    || echo "⚠️  HTTPS javob bermadi — 'docker compose logs web --tail 50' ni ko'ring"
curl -fsS "https://$DOMAIN/health" && echo " <- API sog'lig'i"

cat <<EOF

✅ Tayyor. Endi:
   1. .env ga yozing:
        MAP_PUBLIC_URL=https://$DOMAIN
        TELEGRAM_WEBHOOK_URL=https://$DOMAIN/telegram/webhook
        TELEGRAM_WEBHOOK_SECRET=<tasodifiy satr>
        TELEGRAM_MODE=webhook
   2. Polling rejimidagi botni TO'XTATING (aks holda Telegram update larni
      ikkiga bo'ladi):  docker compose stop bot
   3. API ni qayta ishga tushiring: docker compose up -d api
      (webhook manzili ishga tushishda Telegram ga o'zi e'lon qilinadi —
       app/main.py -> setup_webhook)
   4. Tekshiring: curl -s "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
EOF
