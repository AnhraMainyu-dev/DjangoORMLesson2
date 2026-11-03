#!/bin/bash
set -Eeuo pipefail

cd /opt/starburger/DjangoORMLesson2

git pull
venv/bin/pip install -r requirements.txt
npm ci --dev
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./" --no-source-maps
venv/bin/python manage.py collectstatic --noinput
venv/bin/python manage.py migrate --noinput
systemctl restart starburger
systemctl reload nginx

ROLLBAR_ACCESS_TOKEN=

curl --fail -X POST https://api.rollbar.com/api/1/deploy \
  -F access_token="$ROLLBAR_ACCESS_TOKEN" \
  -F environment=production \
  -F revision="$(git rev-parse HEAD)"

echo "I live again"