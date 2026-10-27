# ## RESUMEN ##

import streamlit as st

from comun import (cargarResultados, basesFiltradas, resumenFiltros, sinDatos, tarjetas, numero, nota,
                   verdeOscuro, naranja, rojo, azul, gris)

exploratorio, modelado = cargarResultados()
perdidasF, maestraF = basesFiltradas()
sinDatos(perdidasF)

# Título y pregunta de investigación
st.markdown(f"<h1 style='color:{verdeOscuro};margin-bottom:0'>¿Dónde se pierden los alimentos?</h1>",
            unsafe_allow_html=True)
st.markdown("##### Detección de puntos críticos de pérdida de alimentos en América Latina, 2010–2023")
st.write("**Pregunta:** ¿Cómo han evolucionado las pérdidas de alimentos en América Latina entre 2010 y 2023, "
         "y qué países y productos presentan los mayores niveles de pérdida?")
st.caption(f"{resumenFiltros()} · {len(perdidasF)} registros país-producto-año")

# Tarjetas que cambian con los filtros
tasa = perdidasF["Perdida"].sum() / perdidasF["Oferta"].sum() * 100
dependencia = perdidasF["Importaciones"].sum() / perdidasF["Oferta"].sum() * 100
pctOficial = (perdidasF["Calidad"] == "Oficial").mean() * 100
pctAtipicos = perdidasF["AtipicoTasa"].mean() * 100
tarjetas([
    (perdidasF["Pais"].nunique(), "Países", verdeOscuro, "🌎"),
    (perdidasF["Producto"].nunique(), "Productos", "#2E7D5B", "🌽"),
    (f"{numero(perdidasF['Perdida'].sum() / 1e6)} M t", "Pérdida total", "#5D4E8C", "⚖️"),
    (f"{numero(tasa)}%", "Tasa de pérdida", rojo, "📉"),
    (f"{numero(maestraF['PerdidaUSD'].sum() / 1e9)} mil M", "Pérdida económica (USD)", naranja, "💵"),
    (f"{numero(dependencia)}%", "Dependencia importadora", azul, "🚢"),
    (f"{numero(pctOficial)}%", "Datos de pérdida oficiales", "#B7862E", "📑"),
    (f"{numero(pctAtipicos)}%", "Registros atípicos (IQR)", gris, "⚠️"),
])

# Resultados del modelado (con las 144 combinaciones)
st.markdown("#### Resultados del modelado multivariado")
baseModelo = modelado["baseModelo"]
grupoAlto = modelado["perfilGrupos"].loc["Pérdida alta"]
tarjetas([
    (f"{baseModelo['Critico'].sum()} de {len(baseModelo)}", "Puntos críticos (tasa ≥ 10%)", rojo, "🔥"),
    (f"OR = {numero(modelado['tablaOR'].loc['Perecedero', 'OR'])}", "Perecedero vs grano", naranja, "🍅"),
    (f"{numero(modelado['rSinSoya'].slope, 3)}", "Tendencia sin soya (p.p./año)", azul, "⏱️"),
    (f"{numero(modelado['proyeccion2030'])}% vs {numero(modelado['meta2030'])}%", "Proyección 2030 vs meta ODS",
     verdeOscuro, "🎯"),
])

# Hallazgos principales
st.markdown("#### Hallazgos principales")
st.markdown(f"""
1. **El tipo de producto es el principal factor.** Un perecedero tiene una odds unas
   **{numero(modelado['tablaOR'].loc['Perecedero', 'OR'])} veces** mayor de ser punto crítico que un grano.
2. **Perder mucho en toneladas no es lo mismo que perder mucho en proporción:** en el PCA son dimensiones distintas.
3. **K-means separó un grupo de pérdida alta** ({int(grupoAlto['Combinaciones'])} combinaciones, tasa de
   {numero(grupoAlto['TasaPerdida'])}%) sin conocer cuáles eran críticos.
4. **La calidad del dato condiciona la lectura:** solo una parte pequeña de los datos de pérdida es oficial.
5. **La región no llegaría a la meta ODS 12.3** al ritmo actual.
""")
nota("Los filtros de la barra lateral cambian las tarjetas y las gráficas del análisis exploratorio. "
     "Los modelos se calcularon con las 144 combinaciones país-producto y no cambian con los filtros.")
