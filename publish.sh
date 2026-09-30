#!/usr/bin/env bash
# Publica este repositorio en GitHub (privado) y el sitio en GitHub Pages (rama gh-pages).
# Requisitos: git, Python con ghp-import (pip install ghp-import) y, opcional, GitHub CLI (gh).
set -euo pipefail
USUARIO="${1:-AlexT09}"
REPO="superstore-dashboard-html"

# 0) (Opcional) crear el repo privado en GitHub con la CLI. Si ya existe, se omite.
if command -v gh >/dev/null 2>&1; then
  gh repo view "$USUARIO/$REPO" >/dev/null 2>&1 || gh repo create "$USUARIO/$REPO" --private \
    --description "Dashboard Superstore (HTML interactivo) con insights automáticos"
fi

# 1) Inicializar el repositorio
[ -d .git ] || git init

# 2) Conectar con el repositorio remoto en GitHub
git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$USUARIO/$REPO.git"

# 3) Crear y cambiar a la rama principal
git checkout -B main
git add -A
git commit -m "Dashboard Superstore" || true
git push -u origin main

# 4) Publicar el sitio en la rama gh-pages
ghp-import -n -p -f docs/_build/html

# 5) Configurar GitHub Pages (una sola vez) en Settings → Pages:
#    Source → Deploy from a branch · Branch → gh-pages → /(root)
#    (Pages en repos privados requiere GitHub Pro, Team o Enterprise.)
echo "Listo: https://$USUARIO.github.io/$REPO/"
