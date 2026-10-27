# ## PRODUCTOS Y TENDENCIAS ##

import plotly.express as px
import streamlit as st

from comun import (basesFiltradas, resumenFiltros, sinDatos, caja, estiloGrafico, nota, verTabla, numero,
                   colorTipo, rojo, verdeOscuro)

perdidasF, maestraF = basesFiltradas()
sinDatos(perdidasF)

st.title("Productos y tendencias")
st.caption(resumenFiltros())
orden = perdidasF.groupby("Producto")["TasaPerdida"].median().sort_values(ascending=False).index.tolist()

izquierda, derecha = st.columns(2)

# Distribución de la tasa por producto
with izquierda:
    with caja("Distribución de la tasa de pérdida por producto"):
        fig = px.box(perdidasF, x="TasaPerdida", y="Producto", color="Tipo", color_discrete_map=colorTipo,
                     category_orders={"Producto": orden}, points="outliers", hover_data=["Pais", "Año"],
                     labels={"TasaPerdida": "Tasa de pérdida (% de la oferta)", "Producto": ""})
        fig.update_layout(boxmode="overlay")
        st.plotly_chart(estiloGrafico(fig, 450), width="stretch")
        nota("Los perecederos (rojo) pierden una proporción mayor de su oferta que los granos (amarillo), "
             "y su dispersión es mayor: dependen más de las condiciones de cada país.")
        medianas = perdidasF.groupby(["Producto", "Tipo"])["TasaPerdida"].median().round(1).reset_index()
        verTabla(medianas.rename(columns={"TasaPerdida": "Tasa mediana (%)"}).sort_values("Tasa mediana (%)", ascending=False))

# Rendimiento vs tasa de pérdida (Spearman)
with derecha:
    with caja("Relación entre rendimiento y tasa de pérdida"):
        productoRend = st.selectbox("Producto", orden, index=orden.index("Banano") if "Banano" in orden else 0)
        datosRend = perdidasF[perdidasF["Producto"] == productoRend].dropna(subset=["IndiceRendimiento"])
        if len(datosRend) > 2:
            rho = datosRend["IndiceRendimiento"].corr(datosRend["TasaPerdida"], method="spearman")
            fig = px.scatter(datosRend, x="IndiceRendimiento", y="TasaPerdida", hover_data=["Pais", "Año"],
                             color_discrete_sequence=[rojo],
                             labels={"IndiceRendimiento": "Índice de rendimiento (100 = mediana regional)",
                                     "TasaPerdida": "Tasa de pérdida (%)"},
                             title=f"Spearman = {numero(rho, 2)}")
            fig.add_vline(x=100, line_dash="dot", line_color="#999")
            fig.update_traces(marker=dict(size=9, line=dict(width=1, color="white")))
            st.plotly_chart(estiloGrafico(fig, 365), width="stretch")
        nota("Spearman cercano a 0 indica que el rendimiento por sí solo no explica la pérdida; "
             "solo el banano muestra una relación fuerte (−0,61).")

# Evolución temporal por producto
with caja("Tasa de pérdida regional por producto, 2010–2023"):
    evolucion = (perdidasF.groupby(["Año", "Producto"])[["Perdida", "Oferta"]].sum()
                 .assign(TasaRegional=lambda d: d["Perdida"] / d["Oferta"] * 100).reset_index())
    fig = px.line(evolucion, x="Año", y="TasaRegional", facet_col="Producto", facet_col_wrap=5,
                  category_orders={"Producto": orden}, markers=True, color_discrete_sequence=[rojo],
                  labels={"TasaRegional": "Tasa (%)", "Año": ""})
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=13, color=verdeOscuro)))
    fig.update_yaxes(matches=None, showticklabels=True)
    fig.update_traces(line_width=2, marker_size=5, hovertemplate="%{x}: %{y:.2f}%<extra></extra>")
    st.plotly_chart(estiloGrafico(fig, 170 + 220 * ((len(orden) - 1) // 5 + 1)), width="stretch")
    nota("Cada producto tiene su propia escala. La mayoría es estable; la papa sube y la soya salta en 2019 "
         "porque Brasil cambió su forma de reporte (no es un aumento real).")
    verTabla(evolucion.round(2))
