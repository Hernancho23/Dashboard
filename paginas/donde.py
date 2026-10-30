# ## ¿DÓNDE SE PIERDE? ##

import plotly.express as px
import streamlit as st

from comun import (basesFiltradas, sinDatos, textoFiltros, encabezado, cifras, caja, estiloGrafico, numero,
                   escalaPerdida, colorTipo, coral, ambar, verde, bosque)

perdidasF, maestraF = basesFiltradas()
sinDatos(perdidasF)

encabezado("Paso 1 · Ubicar el problema", "¿Dónde se pierde?", textoFiltros())

# Mapa de calor país × producto (mediana de la tasa de pérdida)
mapaCalor = perdidasF.pivot_table(index="Pais", columns="Producto", values="TasaPerdida", aggfunc="median")
ordenColumnas = perdidasF.groupby("Producto")["TasaPerdida"].median().sort_values(ascending=False).index
mapaCalor = mapaCalor.loc[mapaCalor.mean(axis=1).sort_values(ascending=False).index, ordenColumnas]

# Los cuatro casos más altos
top = mapaCalor.stack().sort_values(ascending=False).head(4)
cifras([(f"{producto} · {pais}", f"{numero(v)}%", "de la oferta se pierde", color)
        for ((pais, producto), v), color in zip(top.items(), [coral, coral, ambar, ambar])])

with caja("Mapa de puntos críticos", "tasa de pérdida mediana por país y producto (%)"):
    fig = px.imshow(mapaCalor.round(1), text_auto=".1f", aspect="auto", color_continuous_scale=escalaPerdida,
                    zmin=0, zmax=20, labels=dict(color="Tasa (%)", x="", y=""))
    fig.update_traces(hovertemplate="%{y} · %{x}<br>Tasa mediana: %{z:.1f}%<extra></extra>", xgap=2, ygap=2)
    fig.update_xaxes(side="top")
    fig.update_layout(coloraxis_colorbar=dict(thickness=12))
    st.plotly_chart(estiloGrafico(fig, 70 + 34 * len(mapaCalor)), width="stretch", theme=None)

izquierda, derecha = st.columns(2)

# Ranking de combinaciones
with izquierda:
    with caja("Las 12 combinaciones con mayor tasa de pérdida", "mediana del periodo · línea = umbral crítico de 10%"):
        ranking = (perdidasF.groupby(["Pais", "Producto", "Tipo"])["TasaPerdida"].median()
                   .sort_values(ascending=False).head(12).reset_index())
        ranking["Combinación"] = ranking["Producto"] + " · " + ranking["Pais"]
        fig = px.bar(ranking, x="TasaPerdida", y="Combinación", orientation="h", color="Tipo",
                     color_discrete_map=colorTipo, text="TasaPerdida",
                     labels={"TasaPerdida": "", "Combinación": ""})
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_cornerradius=4,
                          hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
        fig.update_yaxes(categoryorder="array", categoryarray=ranking["Combinación"].iloc[::-1].tolist())
        fig.add_vline(x=10, line_dash="dot", line_color="#999")
        fig.update_xaxes(range=[0, ranking["TasaPerdida"].max() * 1.18], showticklabels=False)
        st.plotly_chart(estiloGrafico(fig, 460), width="stretch", theme=None)

# Tasa vs impacto económico
with derecha:
    with caja("Eficiencia vs impacto económico", "cada punto es un país-producto-año · tamaño = valor perdido"):
        dispersion = maestraF.merge(perdidasF[["Pais", "Producto", "Año", "Oferta", "TasaPerdida"]],
                                    on=["Pais", "Producto", "Año"])
        dispersion = dispersion[dispersion["Perdida"] > 0]
        fig = px.scatter(dispersion, x="Oferta", y="TasaPerdida", size="PerdidaUSD", color="Tipo",
                         color_discrete_map=colorTipo, log_x=True, size_max=30, opacity=.55,
                         hover_name="Pais", hover_data={"Producto": True, "Año": True, "TasaPerdida": ":.1f",
                                                        "PerdidaUSD": ":,.0f", "Tipo": False, "Oferta": ":,.0f"},
                         labels={"Oferta": "Oferta disponible (t, escala log)", "TasaPerdida": "Tasa de pérdida (%)",
                                 "PerdidaUSD": "Valor perdido (USD)"})
        fig.update_traces(marker=dict(line=dict(width=.5, color="white"), sizemin=3))
        st.plotly_chart(estiloGrafico(fig, 460), width="stretch", theme=None)
