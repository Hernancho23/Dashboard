# ## ¿DÓNDE INTERVENIR? ##

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import procesamiento as pr
from comun import (cargarResultados, encabezado, cifras, caja, estiloGrafico, numero, pvalor, colorGrupo,
                   coral, verde, ambar, carbon, grisCalido)

exploratorio, modelado = cargarResultados()
m = modelado
baseModelo = pr.traducir(m["baseModelo"])

# Filtros de la barra lateral que aplican a la base de modelado
estado = st.session_state
if estado.get("fPaises"): baseModelo = baseModelo[baseModelo["Pais"].isin(estado["fPaises"])]
if estado.get("fProductos"): baseModelo = baseModelo[baseModelo["Producto"].isin(estado["fProductos"])]
if estado.get("fTipos"): baseModelo = baseModelo[baseModelo["Tipo"].isin(estado["fTipos"])]

encabezado("", "¿Dónde intervenir?",
           "resultados del modelado sobre 144 combinaciones país-producto (mediana 2010–2023)")

# Qué influye en ser punto crítico (prueba Chi²)
asociaciones = m["asociaciones"].set_index("Variable")
tendenciaPP = pr.traducir(m["tendenciaPaisProducto"])
cifras([
    ("Tipo de producto", "Sí influye", f"Chi² · p {pvalor(asociaciones.loc['Tipo', 'p-valor'])}", coral),
    ("Calidad del dato", "Sí influye", f"Chi² · p {pvalor(asociaciones.loc['Calidad', 'p-valor'])}", ambar),
    ("Subregión del país", "No influye", f"Chi² · p {pvalor(asociaciones.loc['Region', 'p-valor'])}", grisCalido),
    ("Combinaciones empeorando", f"{(tendenciaPP['Tendencia'] == 'Creciente').sum()}",
     f"de {len(tendenciaPP)} con tendencia creciente significativa", coral),
])

# Mapa de prioridades: perfil K-means de cada país-producto
if baseModelo.empty:
    st.warning("No hay combinaciones con los filtros seleccionados.")
    st.stop()
codigos = {"Pérdida alta": 2, "Exportadores": 1, "Bajo volumen": 0}
matrizGrupo = baseModelo.pivot_table(index="Pais", columns="Producto", values="NombreGrupo", aggfunc="first")
matrizTasa = baseModelo.pivot_table(index="Pais", columns="Producto", values="TasaPerdida", aggfunc="first")
matrizCritico = baseModelo.pivot_table(index="Pais", columns="Producto", values="Critico", aggfunc="first")
ordenFilas = (baseModelo.assign(Alta=baseModelo["NombreGrupo"].eq("Pérdida alta"))
              .groupby("Pais")[["Alta", "TasaPerdida"]].agg({"Alta": "sum", "TasaPerdida": "median"})
              .sort_values(["Alta", "TasaPerdida"], ascending=False).index)
ordenColumnas = baseModelo.groupby("Producto")["TasaPerdida"].median().sort_values(ascending=False).index
matrizGrupo, matrizTasa, matrizCritico = (x.reindex(index=ordenFilas, columns=ordenColumnas)
                                          for x in (matrizGrupo, matrizTasa, matrizCritico))
z = matrizGrupo.apply(lambda col: col.map(codigos)).astype(float).values
texto = np.where(matrizCritico.values == 1, np.char.add("★ ", np.vectorize(lambda v: numero(v))(matrizTasa.fillna(0).values)),
                 np.vectorize(lambda v: numero(v))(matrizTasa.fillna(0).values))
texto = np.where(np.isnan(z), "", texto)
detalle = np.where(np.isnan(z), "", np.char.add(matrizGrupo.fillna("").values.astype(str),
                   np.where(matrizCritico.values == 1, " · punto crítico", "")))

with caja("Mapa de prioridades", "color = perfil encontrado con K-means · ★ = punto crítico (tasa ≥ 10%) · número = tasa de pérdida (%)"):
    escala = [[0, colorGrupo["Bajo volumen"]], [0.33, colorGrupo["Bajo volumen"]],
              [0.34, colorGrupo["Exportadores"]], [0.66, colorGrupo["Exportadores"]],
              [0.67, colorGrupo["Pérdida alta"]], [1, colorGrupo["Pérdida alta"]]]
    fig = go.Figure(go.Heatmap(z=z, x=list(ordenColumnas), y=list(ordenFilas), zmin=0, zmax=2, colorscale=escala,
                               showscale=False, xgap=2, ygap=2, opacity=.85, text=texto, texttemplate="%{text}",
                               textfont=dict(color=carbon, size=12), customdata=detalle,
                               hovertemplate="%{y} · %{x}<br>%{customdata}<br>Tasa: %{text}%<extra></extra>"))
    for grupo, rol in [("Pérdida alta", "prioridad"), ("Exportadores", "modelo a seguir"), ("Bajo volumen", "bajo impacto")]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=f"{grupo} ({rol})",
                                 marker=dict(size=12, symbol="square", color=colorGrupo[grupo])))
    fig.update_xaxes(side="top", showgrid=False)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    estiloGrafico(fig, 140 + 34 * len(ordenFilas))
    fig.update_layout(legend=dict(orientation="h", y=-0.01, yanchor="top", x=0), margin=dict(t=40, b=50))
    st.plotly_chart(fig, width="stretch", theme=None)

izquierda, derecha = st.columns([1, 1.15])

# Fuerza de la asociación de cada característica con ser crítico
with izquierda:
    with caja("¿Qué está asociado con ser punto crítico?", "estadístico Chi² · color = asociación significativa (p < 0,05)"):
        nombres = {"Tipo": "Tipo de producto", "Calidad": "Calidad del dato", "Rendimiento": "Nivel de rendimiento",
                   "Comercio": "Tipo de comercio", "Region": "Subregión"}
        chi = m["asociaciones"].assign(Variable=lambda d: d["Variable"].map(nombres)).sort_values("Chi²")
        chi["Significativa"] = np.where(chi["p-valor"] < 0.05, "Sí", "No")
        chi["Etiqueta"] = [f"χ² = {numero(c, 1)} · p {pvalor(p)}" for c, p in zip(chi["Chi²"], chi["p-valor"])]
        fig = px.bar(chi, x="Chi²", y="Variable", orientation="h", color="Significativa", text="Etiqueta",
                     color_discrete_map={"Sí": coral, "No": "#C9C4B6"}, labels={"Chi²": "", "Variable": ""},
                     category_orders={"Significativa": ["Sí", "No"]})
        fig.update_traces(textposition="outside", marker_cornerradius=4, hovertemplate="%{y}: %{text}<extra></extra>")
        fig.update_xaxes(range=[0, chi["Chi²"].max() * 2.1], showticklabels=False)
        fig.update_layout(legend_title_text="¿Significativa?")
        st.plotly_chart(estiloGrafico(fig, 420), width="stretch", theme=None)

# Correspondencias múltiples: qué categorías aparecen junto a "Crítico"
with derecha:
    with caja("¿Qué características aparecen junto a «Crítico»?",
              f"análisis de correspondencias múltiples · {numero(sum(m['inerciaMCA']))}% de la inercia en 2 dimensiones"):
        coordenadas = m["coordenadasMCA"].copy()
        coordenadas["Variable"] = [c.split("__")[0] for c in coordenadas.index]
        coordenadas["Categoría"] = [c.split("__")[1] for c in coordenadas.index]
        coordenadas["Grupo"] = np.where(coordenadas["Variable"] == "Condicion", "Condición",
                                np.where(coordenadas["Dim1"] > 0, "Del lado de Crítico", "Del lado de No crítico"))
        fig = px.scatter(coordenadas, x="Dim1", y="Dim2", text="Categoría", color="Grupo",
                         color_discrete_map={"Condición": carbon, "Del lado de Crítico": coral,
                                             "Del lado de No crítico": verde},
                         labels={"Dim1": "Dimensión 1", "Dim2": "Dimensión 2"})
        fig.update_traces(textposition="top center", marker=dict(size=11, line=dict(width=1, color="white")),
                          textfont_size=11, hovertemplate="%{text}<extra></extra>")
        fig.add_hline(y=0, line_color="#ddd", line_width=1); fig.add_vline(x=0, line_color="#ddd", line_width=1)
        x0, x1 = coordenadas["Dim1"].min(), coordenadas["Dim1"].max()
        fig.update_layout(xaxis=dict(range=[x0 - 0.45, x1 + 0.3], showticklabels=False),
                          yaxis=dict(showticklabels=False))
        st.plotly_chart(estiloGrafico(fig, 420), width="stretch", theme=None)

# Dónde está empeorando y dónde mejorando (tendencias significativas por país-producto)
with caja("¿Dónde está empeorando la pérdida?",
          "pendiente de la regresión lineal de la tasa sobre el año (p.p. por año) · solo tendencias significativas (p < 0,05)"):
    significativas = tendenciaPP[tendenciaPP["Tendencia"].isin(["Creciente", "Decreciente"])]
    if estado.get("fPaises"): significativas = significativas[significativas["Pais"].isin(estado["fPaises"])]
    if estado.get("fProductos"): significativas = significativas[significativas["Producto"].isin(estado["fProductos"])]
    extremos = pd.concat([significativas.nlargest(6, "Pendiente"), significativas.nsmallest(6, "Pendiente")])
    extremos = extremos.drop_duplicates().sort_values("Pendiente")
    extremos["Combinación"] = extremos["Producto"] + " · " + extremos["Pais"]
    colores = [coral if v > 0 else verde for v in extremos["Pendiente"]]
    fig = px.bar(extremos, x="Pendiente", y="Combinación", orientation="h", text="Pendiente",
                 labels={"Pendiente": "", "Combinación": ""})
    fig.update_traces(marker_color=colores, marker_cornerradius=4, texttemplate="%{text:+.2f}", textposition="outside",
                      hovertemplate="%{y}: %{x:+.2f} p.p. por año<extra></extra>")
    fig.update_yaxes(categoryorder="array", categoryarray=extremos["Combinación"].tolist())
    rango = extremos["Pendiente"].abs().max() * 1.25 if len(extremos) else 1
    fig.update_xaxes(range=[-rango, rango], zeroline=True, zerolinecolor="#999", showticklabels=False)
    st.plotly_chart(estiloGrafico(fig, 120 + 30 * max(len(extremos), 1)), width="stretch", theme=None)
