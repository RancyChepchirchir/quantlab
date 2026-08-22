#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo
echo "============================================================"
echo "QuantLab Release Check"
echo "============================================================"
echo
echo "Repository:"
echo "  ${ROOT_DIR}"
echo

echo "============================================================"
echo "1. Backend compile check"
echo "============================================================"

cd "${ROOT_DIR}/backend"

python3 -m compileall -q app

echo "✓ Backend Python compilation passed."

echo
echo "============================================================"
echo "2. Backend tests"
echo "============================================================"

PYTHONPATH=. pytest -v --tb=short

echo
echo "✓ Backend test suite passed."

echo
echo "============================================================"
echo "3. Frontend lint"
echo "============================================================"

cd "${ROOT_DIR}/frontend"

npm run lint

echo
echo "✓ Frontend lint passed."

echo
echo "============================================================"
echo "4. Frontend production build"
echo "============================================================"

npm run build

echo
echo "✓ Frontend production build passed."

echo
echo "============================================================"
echo "5. Secret-file safety check"
echo "============================================================"

cd "${ROOT_DIR}"

TRACKED_ENV_FILES="$(
  git ls-files \
    | grep -E '(^|/)\.env($|\.)' \
    | grep -v '\.env\.example$' \
    || true
)"

if [ -n "${TRACKED_ENV_FILES}" ]; then
  echo
  echo "✗ Potential environment files are tracked by Git:"
  echo
  echo "${TRACKED_ENV_FILES}"
  echo
  echo "Remove them from Git before releasing."
  exit 1
fi

echo "✓ No non-example .env files are tracked."

echo
echo "============================================================"
echo "6. Python source syntax"
echo "============================================================"

cd "${ROOT_DIR}/backend"

python3 -m py_compile \
  app/services/market_data/errors.py \
  app/services/market_data/cache.py \
  app/services/market_data/service.py \
  app/services/market_data/providers/massive.py \
  app/services/svi.py \
  app/api/market_data.py \
  app/api/volatility_surface.py

echo "✓ Critical backend modules compile."

echo
echo "============================================================"
echo "7. Git working tree"
echo "============================================================"

cd "${ROOT_DIR}"

git status --short

echo
echo "Note:"
echo "  A non-empty status is allowed during development."
echo "  The release commit itself should eventually be clean."

echo
echo "============================================================"
echo "QuantLab Release Check Summary"
echo "============================================================"
echo
echo "✓ Backend compilation"
echo "✓ Backend tests"
echo "✓ Frontend lint"
echo "✓ Frontend production build"
echo "✓ Environment-file safety"
echo "✓ Critical source compilation"
echo
echo "QUANTLAB RELEASE CHECK PASSED"
echo