# ## PUNTOS CRÍTICOS ##

import plotly.express as px
import streamlit as st

from comun import (basesFiltradas, resumenFiltros, sinDatos, caja, estiloGrafico, nota, verTabla, numero,
                   tarjetas, rojo, naranja, verdeOscuro, colorTipo)

perdidasF, maestraF = basesFiltradas()
sinDatos(perdidasF)

st.title("Puntos críticos")
st.caption(resumenFiltros())

# Mapa de calor país × producto
mapaCalor = perdidasF.pivot_table(index="Pais", columns="Producto", values="TasaPerdida", aggfunc="median")
ordenColumnas = perdidasF.groupby("Producto")["TasaPerdida"].median().sort_values(ascending=False).index
mapaCalor = mapaCalor.loc[mapaCalor.mean(axis=1).sort_values(ascending=False).index, ordenColumnas]
top = mapaCalor.stack().sort_values(ascending=False).head(4)

# Tarjetas con los cuatro casos más altos
colores = [rojo, naranja, "#B7862E", verdeOscuro]
tarjetas([(f"{numero(v)}%", f"{producto} · {pais}", c, "🔥") for ((pais, producto), v), c in zip(top.items(), colores)])

with caja("Mapa de puntos críticos: tasa de pérdida mediana por país y producto"):
    fig = px.imshow(mapaCalor.round(1), text_auto=".1f", aspect="auto", color_continuous_scale="YlOrRd",
                    zmin=0, zmax=20, labels=dict(color="Tasa (%)", x="", y=""))
    fig.update_traces(hovertemplate="%{y} · %{x}<br>Tasa mediana: %{z:.1f}%<extra></extra>")
    st.plotly_chart(estiloGrafico(fig, 60 + 34 * len(mapaCalor)), width="stretch")
    nota("Cada celda es la mediana del periodo filtrado. La escala se corta en 20% para que se vean las diferencias; "
         "los casos más altos son el tomate de Venezuela, el tomate de Chile, el banano de Paraguay y la papa de Perú.")
    verTabla(mapaCalor.round(1).reset_index())

izquierda, derecha = st.columns(2)

# Volumen vs tasa: el tamaño del punto es la pérdida económica
with izquierda:
    with caja("Oferta vs pérdida (tamaño = pérdida económica)"):
        dispersion = maestraF.merge(perdidasF[["Pais", "Producto", "Año", "Oferta", "TasaPerdida"]],
                                    on=["Pais", "Producto", "Año"])
        dispersion = dispersion[dispersion["Perdida"] > 0]
        fig = px.scatter(dispersion, x="Oferta", y="Perdida", size="PerdidaUSD", color="Tipo",
                         color_discrete_map=colorTipo, log_x=True, log_y=True, size_max=28, opacity=.6,
                         hover_name="Pais", hover_data={"Producto": True, "Año": True, "TasaPerdida": ":.1f",
                                                        "PerdidaUSD": ":,.0f", "Tipo": False},
                         labels={"Oferta": "Oferta (t, escala log)", "Perdida": "Pérdida (t, escala log)",
                                 "TasaPerdida": "Tasa (%)", "PerdidaUSD": "Pérdida USD"})
        st.plotly_chart(estiloGrafico(fig, 430), width="stretch")
        nota("Los puntos más grandes son la soya y el maíz de Brasil: el impacto económico depende del volumen, "
             "no de la tasa de pérdida.")

# Ranking de combinaciones por tasa mediana
with derecha:
    with caja("Combinaciones país-producto con mayor tasa de pérdida"):
        ranking = (perdidasF.groupby(["Pais", "Producto", "Tipo"])["TasaPerdida"].median()
                   .sort_values(ascending=False).head(15).reset_index())
        ranking["Combinación"] = ranking["Producto"] + " · " + ranking["Pais"]
        fig = px.bar(ranking.iloc[::-1], x="TasaPerdida", y="Combinación", orientation="h", color="Tipo",
                     color_discrete_map=colorTipo, text="TasaPerdida",
                     labels={"TasaPerdida": "Tasa de pérdida mediana (%)", "Combinación": ""})
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_cornerradius=4,
                          hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
        fig.add_vline(x=10, line_dash="dot", line_color="#888", annotation_text="Umbral 10%",
                      annotation_position="top right", annotation_yshift=18)
        fig.update_xaxes(range=[0, ranking["TasaPerdida"].max() * 1.18])
        fig.update_yaxes(categoryorder="array", categoryarray=ranking["Combinación"].iloc[::-1].tolist())
        st.plotly_chart(estiloGrafico(fig, 430), width="stretch")
        nota("La línea punteada es el umbral de 10% que usamos para definir un punto crítico en el modelado.")
