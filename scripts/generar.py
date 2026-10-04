"""
Genera index.html (dashboard Superstore) con Python + Plotly.

    python scripts/generar.py

Lee superstore_transformado.csv, calcula KPIs, gráficos e insights con
pandas/plotly y los inserta en plantilla.html (mismo diseño que el dashboard
original). Se pre-genera una vista por cada combinación Año x Región; el HTML
solo muestra la que coincide con los filtros.

    Se realiza:
  - Revisión de calidad: faltantes, duplicados y atípicos por IQR.
  - Mapa animado por año con animation_frame.
  - Mapa coroplético por estado (px.choropleth, locationmode="USA-states").
  - Bandas de Bollinger (media móvil ± k desviaciones) sobre las ventas mensuales.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------- datos
ROOT = Path(__file__).resolve().parent.parent          # raíz del repositorio
SALIDA = ROOT / "docs" / "_build" / "html" / "index.html"

df = pd.read_csv(ROOT / "data" / "superstore_transformado.csv").rename(columns={
    "Order ID": "pedido", "Region": "region", "State": "estado", "Category": "categoria",
    "Sub-Category": "subcategoria", "Sales": "ventas", "Profit": "utilidad", "Discount": "descuento",
})


# ---------------------------------------------------------------- calidad de datos
def atipicos_iqr(serie):
    """Cuenta valores fuera de [Q1 - 1.5·IQR, Q3 + 1.5·IQR]"""
    q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
    iqr = q3 - q1
    return int(((serie < q1 - 1.5 * iqr) | (serie > q3 + 1.5 * iqr)).sum())


faltantes = df.isna().sum()
CALIDAD = dict(filas=len(df), faltantes=int(faltantes.sum()), duplicados=int(df.duplicated().sum()),
               at_ventas=atipicos_iqr(df["ventas"]), at_utilidad=atipicos_iqr(df["utilidad"]))
print("Calidad de datos:", CALIDAD)
if CALIDAD["faltantes"]:
    print("  Faltantes por columna:", faltantes[faltantes > 0].to_dict())
# Solo se detecta e informa: en ventas un pedido grande es real, no un error, así que no se elimina.

df["mes"] = df["Order_Date"].str[:7]          # "YYYY-MM"
df["anio"] = df["mes"].str[:4].astype(int)
df["m"] = df["mes"].str[5:7].astype(int)

# Código de dos letras por estado (lo pide locationmode="USA-states", igual que state_code en el módulo)
STATE_CODES = {
    "Alabama": "AL", "Arizona": "AZ", "Arkansas": "AR", "California": "CA", "Colorado": "CO",
    "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC", "Florida": "FL",
    "Georgia": "GA", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA",
    "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
    "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}
df["state_code"] = df["estado"].map(STATE_CODES)
assert df["state_code"].notna().all(), "Falta el código de algún estado en STATE_CODES"

ANIOS = sorted(df["anio"].unique())
REGIONES = sorted(df["region"].unique())
CATEGORIAS = sorted(df["categoria"].unique())
MES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
BANDS = ["0%", "1–20%", "21–40%", ">40%"]

# Paleta del dashboard original
K = dict(ink="#161b22", navy="#1f4e5f", steel="#6d8f99", mist="#c3d1d5",
         acc="#3a3f47", neg="#8e2c3a", grid="#efefec")
NAVY_A = "rgba(31,78,95,.85)"
FONT = 'Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif'
CONFIG = {"displayModeBar": False, "responsive": True}


# ---------------------------------------------------------------- formatos
def fmt_money(v):
    a, s = abs(v), "-" if v < 0 else ""
    if a >= 1e6:
        return f"{s}${a / 1e6:.2f}M"
    if a >= 1e3:
        return f"{s}${a / 1e3:.1f}K"
    return f"{s}${a:.0f}"


def fmt_n(v):
    return f"{v:,}".replace(",", ".")


def pct(v):
    return f"{v:.1f}%"


def lista(items):
    items = list(items)
    return ", ".join(items[:-1]) + " y " + items[-1] if len(items) > 1 else items[0]


def agg(d):
    s, p, o = d["ventas"].sum(), d["utilidad"].sum(), d["pedido"].nunique()
    return dict(s=s, p=p, o=o, m=p / s * 100 if s else 0, t=s / o if o else 0, n=len(d))


def banda(x):
    return "0%" if x == 0 else "1–20%" if x <= 0.2 else "21–40%" if x <= 0.4 else ">40%"


df["banda"] = df["descuento"].map(banda)


# ---------------------------------------------------------------- estilo plotly
def estilo(fig, height, **layout):
    """Aplica el look de las tarjetas (fondo transparente, grid suave, leyenda arriba)."""
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=30, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=11.5, color="#667085"), bargap=0.3,
        hoverlabel=dict(bgcolor=K["ink"], bordercolor=K["ink"], font=dict(family=FONT, color="#fff", size=12)),
        legend=dict(orientation="h", x=1, xanchor="right", y=1.02, yanchor="bottom"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showline=True, linecolor="#d0d5dd",
                     automargin=True, fixedrange=True)
    fig.update_yaxes(gridcolor=K["grid"], zeroline=False, automargin=True, fixedrange=True)
    fig.update_layout(**layout)
    return fig


def money_hover(label, valores):
    """Tooltip con el mismo formato de dinero que los KPIs."""
    return dict(customdata=[fmt_money(v) for v in valores],
                hovertemplate=label + ": %{customdata}<extra></extra>")


def y2(**kw):
    return dict(overlaying="y", side="right", showgrid=False, zeroline=False,
                automargin=True, fixedrange=True, **kw)


def html_fig(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, config=CONFIG, auto_play=False)


# ---------------------------------------------------------------- gráficos
def bbands(price, window_size=6, num_of_std=2):
    """Bandas de Bollinger (misma función que en el Módulo 5, ventana de 6 meses y ±2σ)."""
    rolling_mean = price.rolling(window=window_size, min_periods=3).mean()
    rolling_std = price.rolling(window=window_size, min_periods=3).std()
    upper_band = rolling_mean + rolling_std * num_of_std
    lower_band = (rolling_mean - rolling_std * num_of_std).clip(lower=0)  # las ventas no son negativas
    return rolling_mean, upper_band, lower_band


def fig_tendencia(d, base):
    m = d.groupby("mes")[["ventas", "utilidad"]].sum().sort_index()
    # Las bandas se calculan sobre la serie completa (todos los años) para que un año
    # filtrado también tenga bandas desde enero; luego se recortan a los meses visibles.
    serie = base.groupby("mes")["ventas"].sum().sort_index()
    media, sup, inf = (b.reindex(m.index) for b in bbands(serie))
    x = [MES[int(k[5:]) - 1] + " " + k[2:4] for k in m.index]
    fuera = (m["ventas"] > sup) | (m["ventas"] < inf)
    fig = go.Figure([
        go.Bar(name="Ventas", x=x, y=m["ventas"], marker_color=NAVY_A, **money_hover("Ventas", m["ventas"])),
        go.Scatter(name="Banda sup.", x=x, y=sup, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"),
        go.Scatter(name="Banda ±2σ", x=x, y=inf, mode="lines", line=dict(width=0), fill="tonexty",
                   fillcolor="rgba(109,143,153,.18)", hoverinfo="skip"),
        go.Scatter(name="Media móvil 6m", x=x, y=media, mode="lines",
                   line=dict(color=K["steel"], dash="dash", width=2), **money_hover("Media móvil", media)),
        go.Scatter(name="Utilidad", x=x, y=m["utilidad"], mode="lines",
                   line=dict(color=K["acc"], width=2, shape="spline", smoothing=0.6), **money_hover("Utilidad", m["utilidad"])),
        go.Scatter(name="Fuera de banda", x=[v for v, f in zip(x, fuera) if f], y=m["ventas"][fuera],
                   mode="markers", marker=dict(symbol="diamond", size=9, color=K["ink"], line=dict(color="#fff", width=1)),
                   hoverinfo="skip"),
    ])
    estilo(fig, 290, hovermode="x unified")
    fig.update_xaxes(type="category", nticks=16, tickangle=0, fixedrange=False)  # zoom horizontal permitido
    fig.update_yaxes(tickformat="$~s")
    return fig, m["ventas"].tolist(), [lab for lab, f in zip(x, fuera) if f]


def fig_categorias(d, A):
    cat = pd.DataFrame([dict(c=c, n=(d["categoria"] == c).sum() / len(d) * 100,
                             s=d.loc[d["categoria"] == c, "ventas"].sum() / (A["s"] or 1) * 100)
                        for c in CATEGORIAS if (d["categoria"] == c).any()])
    fig = go.Figure([
        go.Bar(name="% pedidos", x=cat["c"], y=cat["n"], marker_color=K["mist"], hovertemplate="% pedidos: %{y:.1f}%<extra></extra>"),
        go.Bar(name="% ventas", x=cat["c"], y=cat["s"], marker_color=K["navy"], hovertemplate="% ventas: %{y:.1f}%<extra></extra>"),
    ])
    estilo(fig, 290, barmode="group", hovermode="x unified")
    fig.update_yaxes(ticksuffix="%", rangemode="tozero")
    return fig, cat


def fig_subcategorias(d):
    sub = d.groupby("subcategoria")["utilidad"].sum().sort_values(ascending=False)
    fig = go.Figure(go.Bar(orientation="h", x=sub.values, y=sub.index,
                           marker_color=[K["neg"] if v < 0 else NAVY_A for v in sub.values],
                           **money_hover("Utilidad", sub.values)))
    estilo(fig, 360, showlegend=False, margin=dict(l=8, r=8, t=8, b=8), bargap=0.25)
    fig.update_xaxes(tickformat="$~s", showgrid=True, gridcolor=K["grid"], showline=False,
                     zeroline=True, zerolinecolor="#d0d5dd")
    fig.update_yaxes(autorange="reversed", showgrid=False, showline=True, linecolor="#d0d5dd", tickfont_size=11)
    return fig, sub


def fig_descuento(d):
    bm = pd.DataFrame([dict(b=b, **agg(d[d["banda"] == b])) for b in BANDS if (d["banda"] == b).any()])
    fig = go.Figure([
        go.Bar(name="Margen %", x=bm["b"], y=bm["m"], marker_color=[K["neg"] if v < 0 else NAVY_A for v in bm["m"]],
               hovertemplate="Margen: %{y:.1f}%<extra></extra>"),
        go.Scatter(name="Ventas", x=bm["b"], y=bm["s"], yaxis="y2", mode="lines+markers",
                   line=dict(color=K["acc"], width=2), marker=dict(size=8, color=K["acc"]), **money_hover("Ventas", bm["s"])),
    ])
    estilo(fig, 360, hovermode="x unified", yaxis2=y2(tickformat="$~s", rangemode="tozero"))
    fig.update_xaxes(type="category", title_text="Tramo de descuento")
    fig.update_layout(yaxis=dict(ticksuffix="%", title_text="Margen %"))
    return fig, bm


def fig_regiones(d):
    reg = pd.DataFrame([dict(r=r, **agg(d[d["region"] == r])) for r in REGIONES if (d["region"] == r).any()])
    reg = reg.sort_values("s", ascending=False)
    fig = go.Figure([
        go.Bar(name="Ventas", x=reg["r"], y=reg["s"], marker_color=NAVY_A, **money_hover("Ventas", reg["s"])),
        go.Scatter(name="Margen %", x=reg["r"], y=reg["m"], yaxis="y2", mode="markers",
                   marker=dict(symbol="diamond", size=13, color=K["acc"]), hovertemplate="Margen: %{y:.1f}%<extra></extra>"),
    ])
    estilo(fig, 290, hovermode="x unified", yaxis2=y2(ticksuffix="%", rangemode="tozero"))
    fig.update_xaxes(type="category")
    fig.update_layout(yaxis=dict(tickformat="$~s"))
    return fig, reg


def por_estado(d):
    st = (d.groupby(["estado", "state_code"]).agg(s=("ventas", "sum"), p=("utilidad", "sum"))
          .reset_index())
    st["m"] = st["p"] / st["s"] * 100
    st["s_txt"], st["p_txt"] = st["s"].map(fmt_money), st["p"].map(fmt_money)
    return st


def fig_mapa(d, animar=False):
    """Mapa coroplético de margen por estado (px.choropleth, Módulos 3 y 5).

    Con animar=True agrega animation_frame (como el mapa animado del Módulo 3):
    el primer cuadro es el total del periodo y luego un cuadro por año.
    """
    st = por_estado(d)
    datos = st
    if animar:
        datos = pd.concat([st.assign(periodo="2014–2017")] +
                          [por_estado(d[d["anio"] == a]).assign(periodo=str(a)) for a in sorted(d["anio"].unique())])
    lim = min(40, max(5, datos["m"].abs().max()))  # escala simétrica alrededor de 0 %, fija en todos los cuadros
    fig = px.choropleth(
        datos, locationmode="USA-states", locations="state_code", scope="usa", color="m",
        color_continuous_scale=[[0, K["neg"]], [0.5, "#f1efe9"], [1, K["navy"]]],
        range_color=(-lim, lim), custom_data=["estado", "s_txt", "p_txt"],
        animation_frame="periodo" if animar else None,
    )
    trazo = dict(marker_line_color="#fff", marker_line_width=0.8,
                 hovertemplate="<b>%{customdata[0]}</b><br>Ventas: %{customdata[1]}"
                               "<br>Utilidad: %{customdata[2]}<br>Margen: %{z:.1f}%<extra></extra>")
    fig.update_traces(**trazo)
    for cuadro in fig.frames:                    # los cuadros de la animación guardan sus propias trazas
        for tr in cuadro.data:
            tr.update(**trazo)
    estilo(fig, 420, margin=dict(l=0, r=0, t=0, b=0),
           geo=dict(bgcolor="rgba(0,0,0,0)", landcolor="#f7f7f5", subunitcolor="#fff", showlakes=False),
           coloraxis_colorbar=dict(title="Margen", ticksuffix="%", thickness=10, len=0.7))
    if animar:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1200
        fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 300
        fig.layout.updatemenus[0].update(pad=dict(r=10, t=10), font=dict(size=11))
        fig.layout.sliders[0].update(currentvalue=dict(prefix="Periodo: ", font=dict(size=12, color=K["ink"])),
                                     pad=dict(t=10, b=0), font=dict(size=11))
    return fig, st


def fig_estacionalidad(d, A):
    bym = d.groupby("m")["ventas"].sum().reindex(range(1, 13), fill_value=0)
    seas = (bym / A["s"] * 100 if A["s"] else bym * 0).tolist()
    mx = max(seas)
    fig = go.Figure(go.Bar(x=MES, y=seas, marker_color=[K["navy"] if v >= mx * 0.8 else K["mist"] for v in seas],
                           hovertemplate="%{x}: %{y:.1f}% de las ventas<extra></extra>"))
    estilo(fig, 290, showlegend=False, margin=dict(l=8, r=8, t=12, b=8))
    fig.update_xaxes(type="category")
    fig.update_yaxes(ticksuffix="%")
    return fig, seas, mx


# ---------------------------------------------------------------- piezas HTML
def insight(*lineas):
    t = [x for x in lineas if x]
    body = "".join(f"<p>{x}</p>" for x in t) or "<p>Sin datos suficientes para esta combinación de filtros.</p>"
    return f'<div class="insight"><span class="tag">Insight</span>{body}</div>'


def card(cls, titulo, sub, fig, ins, ch=""):
    return (f'<div class="card {cls}"><h3>{titulo}</h3><div class="sub">{sub}</div>'
            f'<div class="ch {ch}">{html_fig(fig)}</div>{ins}</div>')


def delta(cur, prev, label, es_pct=False):
    if prev is None:
        return '<div class="d"></div>'
    diff = cur - prev if es_pct else ((cur - prev) / abs(prev) * 100 if prev else 0)
    txt = f"{abs(diff):.1f} pp" if es_pct else f"{abs(diff):.1f}%"
    return f'<div class="d {"pos" if diff >= 0 else "neg"}">{"▲" if diff >= 0 else "▼"} {txt} {label}</div>'


def kpis(A, cur, prev, lbl):
    def k(nombre, valor, key, es_pct=False):
        d = delta(cur[key], prev[key], lbl, es_pct) if prev else '<div class="d"></div>'
        return f'<div class="kpi"><div class="l">{nombre}</div><div class="v">{valor}</div>{d}</div>'
    return ('<section class="kpis">'
            + k("Ventas", fmt_money(A["s"]), "s") + k("Utilidad", fmt_money(A["p"]), "p")
            + k("Margen", pct(A["m"]), "m", True) + k("Pedidos", fmt_n(A["o"]), "o")
            + k("Ticket medio", fmt_money(A["t"]), "t") + "</section>")


# ---------------------------------------------------------------- una vista (Año x Región)
def vista(anio, region):
    base = df if region is None else df[df["region"] == region]   # sin filtro de año (para comparar)
    d = base if anio is None else base[base["anio"] == anio]
    key = f'{anio or "all"}|{region or "all"}'
    if d.empty:
        return f'<div class="vista" data-key="{key}">{insight()}</div>'
    A = agg(d)

    # comparación: año seleccionado vs anterior; sin año -> 2017 vs 2016
    cur = prev = None
    lbl = ""
    if anio and anio > ANIOS[0]:
        cur, prev, lbl = A, agg(base[base["anio"] == anio - 1]), f"vs {anio - 1}"
    elif anio is None:
        cur, prev, lbl = agg(base[base["anio"] == ANIOS[-1]]), agg(base[base["anio"] == ANIOS[-2]]), f"{ANIOS[-1]} vs {ANIOS[-2]}"
    if prev and not prev["n"]:
        prev = None

    f_trend, mS, fuera = fig_tendencia(d, base)
    f_cat, cat = fig_categorias(d, A)
    f_sub, sub = fig_subcategorias(d)
    f_disc, bm = fig_descuento(d)
    f_reg, reg = fig_regiones(d)
    f_map, st = fig_mapa(d, animar=anio is None)
    f_seas, seas, mx = fig_estacionalidad(d, A)

    # --- insights
    third = max(1, len(mS) // 3)
    avg = lambda a: sum(a) / (len(a) or 1)
    up, down = avg(mS[-third:]) > avg(mS[:third]) * 1.05, avg(mS[-third:]) < avg(mS[:third]) * 0.95
    i_trend = insight(
        "Las ventas tienden a arrancar el año con menos fuerza y a repuntar hacia el cierre, un ritmo que se repite de un año a otro.",
        (f"Dentro del año seleccionado, la trayectoria {'parece ganar impulso con el paso de los meses' if up else 'da señales de moderarse hacia el final' if down else 'luce relativamente estable'}; la utilidad acompaña con oscilaciones más contenidas.")
        if anio else
        (f"La tendencia {'se ve pausada al inicio del periodo y parece tomar impulso en la segunda mitad' if up else 'sugiere cierta pérdida de ritmo hacia el final del periodo' if down else 'luce relativamente estable a lo largo del periodo'}; la utilidad se mueve de forma más contenida que las ventas."),
        f"{'Los meses' if len(fuera) > 1 else 'El mes'} {lista(fuera[:4])}{'…' if len(fuera) > 4 else ''} {'quedan' if len(fuera) > 1 else 'queda'} fuera de la banda de Bollinger (media móvil de 6 meses ± 2σ): son ventas atípicas frente al ritmo reciente."
        if fuera else "Todas las ventas mensuales quedan dentro de la banda de Bollinger (media móvil de 6 meses ± 2σ): no hay meses atípicos.")

    if len(cat) > 1:
        by_n = cat.sort_values("n", ascending=False).iloc[0]["c"]
        val = cat.assign(g=cat["s"] - cat["n"]).sort_values("g", ascending=False).iloc[0]["c"]
        i_cat = insight(
            f"<b>{by_n}</b> concentra el grueso de los pedidos, mientras que <b>{val}</b> pesa más en ventas que en número de pedidos: su aporte parece venir de pedidos de mayor valor más que de la frecuencia."
            if by_n != val else f"<b>{by_n}</b> destaca tanto en pedidos como en ventas; las demás categorías aportan un valor más repartido.",
            "La categoría parece diferenciar el valor del pedido con más claridad que la región o el segmento.")
    else:
        i_cat = insight(f"Con el filtro activo solo se observa <b>{cat.iloc[0]['c']}</b>; la comparación entre volumen y valor requiere ver varias categorías.")

    losers = sub[sub < 0].sort_values().index.tolist()
    leaders = sub.head(2)[sub.head(2) > 0].index.tolist()
    i_sub = insight(
        leaders and f"Buena parte de la utilidad parece apoyarse en pocas subcategorías, con <b>{lista(leaders)}</b> al frente.",
        f"<b>{lista(losers[:3])}</b> {'dan' if len(losers) > 1 else 'da'} señales de erosionar la rentabilidad; podría valer la pena mirar sus precios y descuentos con más detalle."
        if losers else "Con estos filtros no se aprecian subcategorías que resten utilidad.")

    low = d["banda"].isin(["0%", "1–20%"]).sum()
    i_disc = insight(
        "La mayor parte de los pedidos ocurre con descuentos bajos o nulos." if low >= len(d) / 2
        else "Con estos filtros los descuentos altos tienen una presencia inusual.",
        len(bm) > 1 and "A medida que el descuento crece, el margen tiende a deteriorarse sin que las ventas respondan en la misma medida: la relación no luce lineal.")

    rm = reg.sort_values("m", ascending=False)
    i_reg = insight(
        len(reg) > 1 and f"Las diferencias entre regiones parecen más leves que entre categorías. <b>{rm.iloc[0]['r']}</b> tiende a combinar buen volumen con mejor margen, mientras <b>{rm.iloc[-1]['r']}</b> parece rezagarse en rentabilidad.",
        len(reg) == 1 and f"Con el filtro activo solo se observa <b>{reg.iloc[0]['r']}</b>; el mapa muestra cómo se reparte entre sus estados.")

    neg = st[st["p"] < 0].sort_values("p")
    top = st.sort_values("p", ascending=False)
    i_map = insight(
        f"<b>{len(neg)} de {len(st)}</b> estados operan con utilidad negativa; las mayores pérdidas se concentran en <b>{lista(neg['estado'].head(3))}</b>; conviene revisar sus descuentos y la mezcla de productos."
        if len(neg) else f"Ninguno de los {len(st)} estados opera con utilidad negativa en esta selección.",
        top.iloc[0]["p"] > 0 and f"<b>{lista(top['estado'].head(2))}</b> {'aportan' if len(top) > 1 else 'aporta'} la mayor utilidad; el color indica el margen, no el volumen.",
        anio is None and "Con ▶ o el deslizador se recorre el margen por estado año a año.")

    peaks = [MES[i].lower() for i, v in enumerate(seas) if v >= mx * 0.8]
    i_seas = insight(
        f"El último tramo del año parece concentrar buena parte de la actividad, con {lista(peaks)} como {'meses' if len(peaks) > 1 else 'mes'} más {'fuertes' if len(peaks) > 1 else 'fuerte'}; el inicio del año suele ser más tranquilo.",
        "Anticipar inventario y campañas hacia el cierre podría acompañar mejor ese ritmo.")

    return f'''<div class="vista" data-key="{key}">
{kpis(A, cur, prev, lbl)}
<div class="section-title">Desempeño comercial</div>
<section class="grid">
{card("s8", "Evolución mensual", "Ventas (barras), media móvil con banda de Bollinger ±2σ y utilidad por mes", f_trend, i_trend)}
{card("s4", "Categorías: volumen vs. valor", "Participación en pedidos y en ventas", f_cat, i_cat)}
</section>
<div class="section-title">Rentabilidad</div>
<section class="grid">
{card("s6", "Utilidad por subcategoría", "Resaltadas, las subcategorías con utilidad negativa", f_sub, i_sub, ch="tall")}
{card("s6", "Impacto del descuento en el margen", "Margen (%) y ventas por tramo de descuento", f_disc, i_disc, ch="tall")}
</section>
<div class="section-title">Geografía y estacionalidad</div>
<section class="grid">
{card("s12", "Margen por estado", "Utilidad / ventas por estado; en borgoña, los estados con pérdida", f_map, i_map, ch="map")}
</section>
<section class="grid">
{card("s6", "Regiones: ventas vs. margen", "Ventas (barras) y margen % (marcadores)", f_reg, i_reg)}
{card("s6", "Estacionalidad", "Participación de cada mes en las ventas; resaltados, los meses más fuertes", f_seas, i_seas)}
</section>
</div>'''


# ---------------------------------------------------------------- armar el HTML
if __name__ == "__main__":
    vistas = [vista(a, r) for a in [None, *ANIOS] for r in [None, *REGIONES]]
    html = (open(ROOT / "src" / "plantilla.html", encoding="utf-8").read()
            .replace("{{N_LINEAS}}", fmt_n(len(df)))
            .replace("{{CALIDAD}}",
                     f'<b>Calidad de datos:</b> {fmt_n(CALIDAD["filas"])} filas · {fmt_n(CALIDAD["faltantes"])} faltantes · '
                     f'{fmt_n(CALIDAD["duplicados"])} duplicados · {fmt_n(CALIDAD["at_ventas"])} atípicos en ventas y '
                     f'{fmt_n(CALIDAD["at_utilidad"])} en utilidad (IQR), conservados en el análisis por ser pedidos reales.')
            .replace("{{OPC_ANIO}}", '<option value="">Todos</option>' + "".join(f"<option>{a}</option>" for a in ANIOS))
            .replace("{{OPC_REGION}}", '<option value="">Todas</option>' + "".join(f"<option>{r}</option>" for r in REGIONES))
            .replace("{{VISTAS}}", "\n".join(vistas)))
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{SALIDA.relative_to(ROOT)} generado: {len(vistas)} vistas, {len(html) / 1e6:.1f} MB")
