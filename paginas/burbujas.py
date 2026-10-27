# ## DIAGRAMA DE BURBUJAS ##

import plotly.express as px
import streamlit as st

import procesamiento as pr
from comun import (cargarResultados, caja, estiloGrafico, nota, colorTipo, colorGrupo, numero)

exploratorio, modelado = cargarResultados()
baseModelo = pr.traducir(modelado["baseModelo"])

st.title("Diagrama de burbujas")
st.caption("Cada burbuja es una combinación país-producto (mediana 2010–2023). Elige qué mostrar en cada eje.")

# Filtros de la barra lateral que aplican a esta base
estado = st.session_state
if estado.get("fPaises"): baseModelo = baseModelo[baseModelo["Pais"].isin(estado["fPaises"])]
if estado.get("fProductos"): baseModelo = baseModelo[baseModelo["Producto"].isin(estado["fProductos"])]
if estado.get("fTipos"): baseModelo = baseModelo[baseModelo["Tipo"].isin(estado["fTipos"])]

# Variables disponibles
numericas = {"Tasa de pérdida (%)": "TasaPerdida", "Pérdida (t)": "Perdida", "Pérdida económica (USD)": "PerdidaUSD",
             "Oferta (t)": "Oferta", "Precio al productor (USD/t)": "Precio", "Índice de rendimiento": "IndiceRendimiento",
             "Dependencia importadora (%)": "DependenciaImportadora",
             "Orientación exportadora (%)": "OrientacionExportadora"}
categoricas = {"Tipo de producto": "Tipo", "Grupo K-means": "NombreGrupo", "Condición": "Condicion",
               "Calidad del dato": "Calidad", "Subregión": "Region", "Producto": "Producto"}
escalaLog = ["Perdida", "PerdidaUSD", "Oferta", "Precio"]

with caja("Controles"):
    c1, c2, c3, c4 = st.columns(4)
    ejeX = c1.selectbox("Eje X", list(numericas), index=list(numericas).index("Oferta (t)"))
    ejeY = c2.selectbox("Eje Y", list(numericas), index=0)
    tamano = c3.selectbox("Tamaño", list(numericas), index=list(numericas).index("Pérdida económica (USD)"))
    colorPor = c4.selectbox("Color por", list(categoricas), index=1)

with caja(f"{ejeY} vs {ejeX}"):
    x, y, s, c = numericas[ejeX], numericas[ejeY], numericas[tamano], categoricas[colorPor]
    datos = baseModelo.dropna(subset=[x, y, s]).assign(Combinacion=lambda d: d["Pais"] + " · " + d["Producto"])
    mapaColor = colorGrupo if c == "NombreGrupo" else (colorTipo if c == "Tipo" else
                {"Crítico": "#c0392b", "No crítico": "#95a5a6"} if c == "Condicion" else None)
    fig = px.scatter(datos, x=x, y=y, size=s, color=c, color_discrete_map=mapaColor, size_max=40, opacity=.7,
                     category_orders={"NombreGrupo": list(colorGrupo), "Tipo": list(colorTipo)},
                     log_x=x in escalaLog, log_y=y in escalaLog, hover_name="Combinacion",
                     hover_data={x: ":,.1f", y: ":,.1f", s: ":,.0f", c: True},
                     labels={**{v: k for k, v in numericas.items()}, **{v: k for k, v in categoricas.items()}})
    fig.update_traces(marker=dict(sizemin=4, line=dict(width=1, color="white")))
    st.plotly_chart(estiloGrafico(fig, 560), width="stretch")
    if x in escalaLog or y in escalaLog:
        st.caption("Las variables de volumen, valor y precio se muestran en escala logarítmica.")
    rho = datos[x].corr(datos[y], method="spearman")
    nota(f"Correlación de Spearman entre {ejeX.lower()} y {ejeY.lower()}: <b>{numero(rho, 2)}</b> "
         f"({len(datos)} combinaciones). Pasa el mouse por las burbujas para ver cada combinación.")
