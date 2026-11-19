# ## PREDICCIÓN Y SIMULADOR ##

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import procesamiento as pr
from comun import (cargarResultados, encabezado, cifras, caja, estiloGrafico, numero, coral, verde, ambar, carbon,
                   bosque, grisCalido)

exploratorio, modelado = cargarResultados()
m = modelado
niveles = pr.niveles
colorNivel = {"Bajo": verde, "Medio": "#A7C957", "Alto": ambar, "Crítico": coral}

# Base de prueba (2020-2023) con la predicción, en español y con los filtros de país, producto y tipo
basePrueba = pr.traducir(m["basePrueba"])
perecederosEs = [pr.productosEspanol[p] for p in pr.perecederos]
basePrueba["Tipo"] = np.where(basePrueba["Producto"].isin(perecederosEs), "Perecedero", "Grano")
estado = st.session_state
if estado.get("fPaises"): basePrueba = basePrueba[basePrueba["Pais"].isin(estado["fPaises"])]
if estado.get("fProductos"): basePrueba = basePrueba[basePrueba["Producto"].isin(estado["fProductos"])]
if estado.get("fTipos"): basePrueba = basePrueba[basePrueba["Tipo"].isin(estado["fTipos"])]

encabezado("", "Predicción y simulador",
           f"nivel de pérdida esperado con {m['nombreMejor']} · entrenado con 2010–2019 y evaluado en 2020–2023")

if basePrueba.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# Cifras principales del modelo y de los hotspots de 2023
anioFinal = basePrueba["Año"].max()
baseFinal = basePrueba[basePrueba["Año"] == anioFinal]
criticos = baseFinal["Prediccion"] == "Crítico"
porcentajeValor = baseFinal.loc[criticos, "PerdidaUSD"].sum() / baseFinal["PerdidaUSD"].sum() * 100
cifras([
    ("Aciertos del modelo", f"{numero(m['exactitudPrueba'] * 100, 0)}%",
     f"nivel correcto en 2020–2023 · Kappa {numero(m['kappaPrueba'], 2)}", bosque),
    ("Críticos detectados", f"{numero(m['porClase'].loc['Crítico', 'Sensibilidad'] * 100, 0)}%",
     "de los casos con tasa ≥ 10%", coral),
    (f"Hotspots críticos {anioFinal}", f"{criticos.sum()}", f"de {len(baseFinal)} combinaciones país-producto", coral),
    ("Valor en hotspots críticos", f"{numero(porcentajeValor, 0)}%", f"de la pérdida en USD de {anioFinal}", ambar),
])

# Mapa de calor de los hotspots: nivel predicho por país y producto
with caja(f"Mapa de hotspots {anioFinal}",
          "color = nivel de pérdida predicho por el modelo · número = tasa de pérdida real (%)"):
    codigo = {nivel: i for i, nivel in enumerate(niveles)}
    matrizNivel = baseFinal.pivot_table(index="Pais", columns="Producto", values="Prediccion", aggfunc="first")
    matrizTasa = baseFinal.pivot_table(index="Pais", columns="Producto", values="TasaPerdida", aggfunc="first")
    matrizReal = baseFinal.pivot_table(index="Pais", columns="Producto", values="Nivel", aggfunc="first")
    ordenFilas = (baseFinal.assign(Codigo=baseFinal["Prediccion"].map(codigo)).groupby("Pais")["Codigo"].mean()
                  .sort_values(ascending=False).index)
    ordenColumnas = (baseFinal.assign(Codigo=baseFinal["Prediccion"].map(codigo)).groupby("Producto")["Codigo"].mean()
                     .sort_values(ascending=False).index)
    matrizNivel, matrizTasa, matrizReal = (x.reindex(index=ordenFilas, columns=ordenColumnas)
                                           for x in (matrizNivel, matrizTasa, matrizReal))
    z = matrizNivel.apply(lambda col: col.map(codigo)).astype(float).values
    texto = np.where(np.isnan(z), "", np.vectorize(lambda v: numero(v))(matrizTasa.fillna(0).values))
    detalle = np.where(np.isnan(z), "", np.char.add(np.char.add("Predicho: ", matrizNivel.fillna("").values.astype(str)),
                                                    np.char.add(" · Real: ", matrizReal.fillna("").values.astype(str))))
    escala = []
    for i, nivel in enumerate(niveles):
        escala += [[i / 4, colorNivel[nivel]], [(i + 1) / 4 - 0.001, colorNivel[nivel]]]
    escala[-1][0] = 1
    fig = go.Figure(go.Heatmap(z=z, x=list(ordenColumnas), y=list(ordenFilas), zmin=-0.5, zmax=3.5, colorscale=escala,
                               showscale=False, xgap=2, ygap=2, opacity=.85, text=texto, texttemplate="%{text}",
                               textfont=dict(color=carbon, size=12), customdata=detalle,
                               hovertemplate="%{y} · %{x}<br>%{customdata}<br>Tasa real: %{text}%<extra></extra>"))
    for nivel in niveles:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=nivel,
                                 marker=dict(size=12, symbol="square", color=colorNivel[nivel])))
    fig.update_xaxes(side="top", showgrid=False)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    estiloGrafico(fig, 140 + 34 * len(ordenFilas))
    fig.update_layout(legend=dict(orientation="h", y=-0.01, yanchor="top", x=0), margin=dict(t=40, b=50))
    st.plotly_chart(fig, width="stretch", theme=None)

izquierda, derecha = st.columns(2)

# Nivel esperado de una combinación país-producto
with izquierda:
    with caja("Nivel esperado por país-producto", "probabilidad de cada nivel según el modelo · 2020–2023"):
        # Por defecto se muestra el hotspot crítico de mayor valor perdido
        ordenValor = baseFinal.assign(EsCritico=baseFinal["Prediccion"] == "Crítico")
        mayorValor = ordenValor.sort_values(["EsCritico", "PerdidaUSD"], ascending=False).iloc[0]
        a, b = st.columns(2)
        paises = sorted(basePrueba["Pais"].unique())
        pais = a.selectbox("País", paises, index=paises.index(mayorValor["Pais"]), key="predPais")
        productos = sorted(basePrueba.loc[basePrueba["Pais"] == pais, "Producto"].unique())
        producto = b.selectbox("Producto", productos, key="predProducto",
                               index=productos.index(mayorValor["Producto"]) if mayorValor["Producto"] in productos else 0)
        seleccion = basePrueba[(basePrueba["Pais"] == pais) & (basePrueba["Producto"] == producto)].sort_values("Año")
        largo = seleccion.melt(id_vars=["Año"], value_vars=[f"Prob {n}" for n in niveles],
                               var_name="Nivel", value_name="Probabilidad")
        largo["Nivel"] = largo["Nivel"].str.replace("Prob ", "")
        largo["Probabilidad"] = largo["Probabilidad"] * 100
        fig = px.bar(largo, x="Año", y="Probabilidad", color="Nivel", color_discrete_map=colorNivel,
                     category_orders={"Nivel": niveles}, labels={"Probabilidad": "Probabilidad (%)", "Año": ""})
        fig.update_traces(marker_cornerradius=3, hovertemplate="%{fullData.name}: %{y:.0f}%<extra></extra>")
        for _, fila in seleccion.iterrows():
            simbolo = "✓" if fila["Acierto"] else "✗"
            fig.add_annotation(x=int(fila["Año"]), y=104, showarrow=False, font=dict(size=12, color=carbon),
                               text=f"Real: {fila['Nivel']} {simbolo}")
        fig.update_yaxes(range=[0, 112])
        fig.update_xaxes(tickvals=sorted(seleccion["Año"].unique()), tickformat="d")
        fig.update_layout(barmode="stack", margin=dict(t=60))
        st.plotly_chart(estiloGrafico(fig, 380), width="stretch", theme=None)

# Simulador de reducción de pérdidas
with derecha:
    with caja("Simulador de reducción de pérdidas", f"¿qué se recupera si los hotspots de {anioFinal} reducen su pérdida?"):
        a, b = st.columns([1, 1.3])
        reduccion = a.slider("Reducción de la pérdida (%)", 0, 50, 20, step=5, key="simReduccion")
        foco = b.multiselect("Niveles a intervenir", niveles, default=["Alto", "Crítico"], key="simNiveles")
        intervenidas = baseFinal[baseFinal["Prediccion"].isin(foco)].copy()
        intervenidas["Toneladas"] = intervenidas["Perdida"] * reduccion / 100
        intervenidas["USD"] = intervenidas["PerdidaUSD"] * reduccion / 100
        tasaAntes = baseFinal["Perdida"].sum() / baseFinal["Oferta"].sum() * 100
        tasaDespues = (baseFinal["Perdida"].sum() - intervenidas["Toneladas"].sum()) / baseFinal["Oferta"].sum() * 100
        resultados = [("Toneladas recuperadas", f"{numero(intervenidas['Toneladas'].sum() / 1e6, 2)} M t", coral),
                      ("Valor recuperado", f"US$ {numero(intervenidas['USD'].sum() / 1e6, 0)} M", ambar),
                      ("Tasa de pérdida", f"{numero(tasaAntes, 2)}% → {numero(tasaDespues, 2)}%", verde)]
        for columna, (nombre, valor, acento) in zip(st.columns(3), resultados):
            columna.markdown(f"<div style='border-left:4px solid {acento};padding:2px 0 2px 10px;margin:6px 0 4px 0'>"
                             f"<div style='font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:{grisCalido};"
                             f"font-weight:700'>{nombre}</div><div style='font-size:1.25rem;font-weight:800;color:{carbon}'>"
                             f"{valor}</div></div>", unsafe_allow_html=True)
        if intervenidas.empty:
            st.info("No hay combinaciones en los niveles seleccionados.")
            st.stop()
        mayores = intervenidas.nlargest(8, "USD").sort_values("USD")
        mayores["Combinación"] = mayores["Producto"] + " · " + mayores["Pais"]
        mayores["Millones"] = mayores["USD"] / 1e6
        fig = px.bar(mayores, x="Millones", y="Combinación", orientation="h", color="Prediccion",
                     color_discrete_map=colorNivel, text="Millones", labels={"Millones": "", "Combinación": ""})
        fig.update_traces(texttemplate="%{text:,.0f} M", textposition="outside", marker_cornerradius=4,
                          hovertemplate="%{y}: US$ %{x:,.1f} M<extra></extra>")
        fig.update_yaxes(categoryorder="array", categoryarray=mayores["Combinación"].tolist())
        fig.update_xaxes(range=[0, max(mayores["Millones"].max(), 1) * 1.3], showticklabels=False)
        fig.update_layout(legend_title_text="")
        st.plotly_chart(estiloGrafico(fig, 300), width="stretch", theme=None)
