#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo
echo "============================================================"
echo "QuantLab Dependency Audit"
echo "============================================================"

echo
echo "------------------------------------------------------------"
echo "Python"
echo "------------------------------------------------------------"

cd "${ROOT_DIR}/backend"

python3 --version

echo
echo "Backend direct dependencies:"
echo

cat requirements.txt

echo
echo "Installed backend versions:"
echo

python3 - <<'PY'
from importlib import metadata

packages = [
    "fastapi",
    "uvicorn",
    "numpy",
    "scipy",
    "pydantic",
    "requests",
]

for package in packages:
    try:
        version = metadata.version(package)
    except metadata.PackageNotFoundError:
        version = "NOT INSTALLED"

    print(f"{package:15} {version}")
PY

echo
echo "------------------------------------------------------------"
echo "Node / npm"
echo "------------------------------------------------------------"

cd "${ROOT_DIR}/frontend"

node --version
npm --version

echo
echo "Frontend package versions:"
echo

node <<'JS'
const packageJson = require("./package.json");

const names = [
  "next",
  "react",
  "react-dom",
  "recharts",
];

for (const name of names) {
  const version =
    packageJson.dependencies?.[name] ??
    packageJson.devDependencies?.[name] ??
    "NOT DECLARED";

  console.log(`${name.padEnd(15)} ${version}`);
}
JS

echo
echo "------------------------------------------------------------"
echo "Lockfiles"
echo "------------------------------------------------------------"

cd "${ROOT_DIR}"

for file in \
  frontend/package-lock.json \
  frontend/pnpm-lock.yaml \
  frontend/yarn.lock \
  backend/requirements.txt
do
  if [ -f "${file}" ]; then
    echo "✓ ${file}"
  else
    echo "  ${file} not present"
  fi
done

echo
echo "============================================================"
echo "Audit complete"
echo "============================================================"