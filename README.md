# Superstore · Dashboard interactivo (Python + Plotly + HTML)

Dashboard web sobre el dataset *Sample – Superstore* (2014–2017), generado con **Python (pandas + Plotly)** sobre una plantilla **HTML**. Tiene filtros por año y región y una lectura interpretativa (insight) debajo de cada visualización.

**Ver online:** https://alext09.github.io/superstore-dashboard-html/

![Captura del dashboard](assets/dashboard_screenshot.png)

## Contenido

- **KPIs**: ventas, utilidad, margen, pedidos y ticket medio, con variación frente al año anterior.
- **Evolución mensual** de ventas y utilidad.
- **Categorías**, **utilidad por subcategoría** e **impacto del descuento en el margen**.
- **Mapa de margen por estado** (`px.choropleth`, `USA-states`), animado por año con `animation_frame`.
- **Regiones** y **estacionalidad**.
- **Calidad de datos**: faltantes, duplicados y atípicos por IQR, informados al pie del dashboard.

## Estructura

```
├── data/superstore_transformado.csv   # dataset
├── src/plantilla.html                 # diseño del dashboard (HTML + CSS)
├── scripts/generar.py                 # pandas + Plotly: KPIs, gráficos e insights
├── docs/_build/html/index.html        # dashboard final
├── assets/dashboard_screenshot.png    # captura
├── requirements.txt
└── publish.sh                         # publica en GitHub Pages
```

## Cómo generarlo

```bash
pip install -r requirements.txt
python scripts/generar.py
```

Abre `docs/_build/html/index.html` en el navegador. Requiere conexión a internet, porque Plotly.js y la tipografía se cargan desde CDN.

Los gráficos se calculan en Python; se pre-genera una vista por cada combinación Año × Región y la plantilla solo muestra la que coincide con los filtros.
