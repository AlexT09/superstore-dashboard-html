# Superstore · Dashboard interactivo (HTML)

Dashboard web sobre el dataset *Sample – Superstore*, con filtros por año, región, categoría y segmento, y una lectura interpretativa debajo de cada visualización.

![Captura del dashboard](assets/dashboard_screenshot.png)

```
├── data/superstore_transformado.csv   # dataset limpio
├── src/template.html                  # plantilla del dashboard (HTML + CSS + JS)
├── src/chart.umd.js                   # Chart.js, se incrusta en el HTML final
├── scripts/build_dashboard.py         # genera el sitio a partir del CSV
├── docs/_build/html/index.html        # dashboard final autocontenido
├── assets/dashboard_screenshot.png    # captura
└── publish.sh                         # publica en GitHub Pages
```
