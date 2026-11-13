#!/bin/bash
set -Eeuo pipefail

cd /opt/starburger/DjangoORMLesson2

git pull

docker compose -f docker-compose.prod.yaml build
docker compose -f docker-compose.prod.yaml run --rm --no-deps backend python manage.py migrate --noinput
docker compose -f docker-compose.prod.yaml run --rm --no-deps backend python manage.py collectstatic --noinput
docker compose -f docker-compose.prod.yaml up -d

systemctl reload nginx

source /opt/starburger/DjangoORMLesson2/.env
curl --fail -sS -X POST https://api.rollbar.com/api/1/deploy \
  -F access_token="$ROLLBAR_ACCESS_TOKEN" \
  -F environment=production \
  -F revision="$(git rev-parse HEAD)"

echo "I live again"
