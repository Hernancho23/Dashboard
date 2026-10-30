# ## FICHA TÉCNICA ##

import pandas as pd
import streamlit as st

from comun import cargarResultados, encabezado, caja, numero, pvalor

exploratorio, modelado = cargarResultados()
m = modelado
metricas = m["metricas"].set_index("Modelo")

encabezado("", "Ficha técnica", "métodos y validación del análisis")

izquierda, derecha = st.columns(2)

# Datos y método
with izquierda:
    with caja("Datos"):
        st.table(pd.DataFrame({
            "Elemento": ["Fuente", "Cobertura", "Unidad de modelado", "Punto crítico", "Tasa de pérdida"],
            "Detalle": ["FAOSTAT: SUA, Producción, Precios al productor y Comercio",
                        "17 países de América Latina · 10 productos · 2010–2023",
                        "144 combinaciones país-producto (mediana del periodo)",
                        "Tasa de pérdida mediana ≥ 10%",
                        "Pérdida / (producción + importaciones)"]}).set_index("Elemento").rename_axis(None))
with derecha:
    with caja("Técnicas y resultado principal"):
        st.table(pd.DataFrame({
            "Técnica": ["Análisis factorial (PCA)", "Regresión logística", "Random Forest", "K-means",
                        "Chi² y correspondencias", "Regresión lineal"],
            "Resultado": [f"KMO {numero(m['kmoGlobal'], 2)} · Bartlett p {pvalor(m['pB'])} · "
                          f"{numero(m['acumulada'][m['nComponentes'] - 1] * 100)}% con {m['nComponentes']} componentes",
                          f"OR perecedero {numero(m['tablaOR'].loc['Perecedero', 'OR'])} · AUC "
                          f"{numero(metricas.loc['Regresión logística', 'AUC'], 3)}",
                          f"AUC {numero(metricas.loc['Random Forest', 'AUC'], 3)} · sensibilidad "
                          f"{numero(metricas.loc['Random Forest', 'Sensibilidad'] * 100)}%",
                          "3 perfiles: pérdida alta, exportadores y bajo volumen",
                          f"Tipo de producto y calidad del dato asociados (p < 0,05) · MCA {numero(sum(m['inerciaMCA']))}%",
                          f"{numero(m['rSinSoya'].slope, 3)} p.p./año sin soya (p {pvalor(m['rSinSoya'].pvalue)})"]
        }).set_index("Técnica").rename_axis(None))

# Prueba de hipótesis
pCalidad = m["asociaciones"].set_index("Variable").loc["Calidad", "p-valor"]
with caja("Hipótesis (α = 0,05)"):
    st.table(pd.DataFrame([
        ["H1", "Los indicadores están correlacionados y se resumen en pocas dimensiones", pvalor(m["pB"]), "Se acepta"],
        ["H2", "Ser perecedero aumenta la probabilidad de ser punto crítico",
         pvalor(m["tablaOR"].loc["Perecedero", "p-valor Wald"]), "Se acepta"],
        ["H3", "La calidad del dato está asociada con ser punto crítico", pvalor(pCalidad), "Se acepta"],
        ["H4", "La tasa regional cambió entre 2010 y 2023 (sin soya)", pvalor(m["rSinSoya"].pvalue), "Se acepta"],
    ], columns=["#", "Hipótesis", "p-valor", "Decisión"]).set_index("#").rename_axis(None))

# Desempeño de los modelos de clasificación
with caja("Clasificación de puntos críticos (validación cruzada de 5 particiones)"):
    st.table(pd.DataFrame({
        "Exactitud": metricas["Exactitud"].map(lambda v: f"{numero(v * 100)}%"),
        "AUC": metricas["AUC"].map(lambda v: numero(v, 3)),
        "Sensibilidad": metricas["Sensibilidad"].map(lambda v: f"{numero(v * 100)}%"),
        "Especificidad": metricas["Especificidad"].map(lambda v: f"{numero(v * 100)}%")}).rename_axis(None))
