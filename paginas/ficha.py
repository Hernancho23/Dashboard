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
            "Elemento": ["Fuente", "Cobertura", "Unidad de modelado", "Unidad del modelo predictivo", "Punto crítico",
                         "Niveles de pérdida", "Tasa de pérdida"],
            "Detalle": ["FAOSTAT: SUA, Producción, Precios al productor y Comercio",
                        "17 países de América Latina · 10 productos · 2010–2023",
                        "144 combinaciones país-producto (mediana del periodo)",
                        f"1.537 registros país-producto-año ({m['nEntrenamiento']} de 2010–2019 y {m['nPrueba']} de 2020–2023)",
                        "Tasa de pérdida mediana ≥ 10%",
                        "Bajo < 3% · Medio 3–6% · Alto 6–10% · Crítico ≥ 10%",
                        "Pérdida / (producción + importaciones)"]}).set_index("Elemento").rename_axis(None))
with derecha:
    with caja("Técnicas y resultado principal"):
        st.table(pd.DataFrame({
            "Técnica": ["Análisis factorial (PCA)", "Regresión logística", "Random Forest", "K-means",
                        "Chi² y correspondencias", "Regresión lineal", f"Modelo predictivo ({m['nombreMejor']})"],
            "Resultado": [f"KMO {numero(m['kmoGlobal'], 2)} · Bartlett p {pvalor(m['pB'])} · "
                          f"{numero(m['acumulada'][m['nComponentes'] - 1] * 100)}% con {m['nComponentes']} componentes",
                          f"OR perecedero {numero(m['tablaOR'].loc['Perecedero', 'OR'])} · AUC "
                          f"{numero(metricas.loc['Regresión logística', 'AUC'], 3)}",
                          f"AUC {numero(metricas.loc['Random Forest', 'AUC'], 3)} · sensibilidad "
                          f"{numero(metricas.loc['Random Forest', 'Sensibilidad'] * 100)}%",
                          "3 perfiles: pérdida alta, exportadores y bajo volumen",
                          f"Tipo de producto y calidad del dato asociados (p < 0,05) · MCA {numero(sum(m['inerciaMCA']))}%",
                          f"{numero(m['rSinSoya'].slope, 3)} p.p./año sin soya (p {pvalor(m['rSinSoya'].pvalue)})",
                          f"Exactitud {numero(m['exactitudPrueba'] * 100)}% en 2020–2023 · Kappa {numero(m['kappaPrueba'], 2)}"]
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
        ["H5", "El modelo predice el nivel de pérdida mejor que la clase más frecuente", pvalor(m["pNIR"]),
         "Se acepta" if m["pNIR"] < 0.05 else "Se rechaza"],
    ], columns=["#", "Hipótesis", "p-valor", "Decisión"]).set_index("#").rename_axis(None))

# Desempeño de los modelos de clasificación
with caja("Clasificación de puntos críticos (validación cruzada de 5 particiones)"):
    st.table(pd.DataFrame({
        "Exactitud": metricas["Exactitud"].map(lambda v: f"{numero(v * 100)}%"),
        "AUC": metricas["AUC"].map(lambda v: numero(v, 3)),
        "Sensibilidad": metricas["Sensibilidad"].map(lambda v: f"{numero(v * 100)}%"),
        "Especificidad": metricas["Especificidad"].map(lambda v: f"{numero(v * 100)}%")}).rename_axis(None))

# Modelo predictivo: comparación de los clasificadores en 2020-2023
comparacion = m["comparacion"]
with caja("Modelo predictivo del nivel de pérdida",
          f"entrenamiento 2010–2019 · prueba 2020–2023 · exactitud del mejor modelo "
          f"{numero(m['exactitudPrueba'] * 100)}% (IC 95%: {numero(m['icExactitud'][0] * 100)}%–"
          f"{numero(m['icExactitud'][1] * 100)}%) frente a {numero(m['tasaNoInformacion'] * 100)}% de la clase más frecuente"):
    st.table(pd.DataFrame({
        "Exactitud VC 2010–2019": comparacion["Exactitud VC"].map(lambda v: f"{numero(v * 100)}%"),
        "Exactitud 2020–2023": comparacion["Exactitud"].map(lambda v: f"{numero(v * 100)}%"),
        "F1 macro": comparacion["F1 macro"].map(lambda v: numero(v, 3)),
        "Kappa": comparacion["Kappa"].map(lambda v: numero(v, 3)),
        "Críticos detectados": comparacion["Sensibilidad Crítico"].map(lambda v: f"{numero(v * 100)}%"),
    }).set_axis(comparacion["Modelo"]).rename_axis(None))

izquierda, derecha = st.columns(2)

# Validación y sesgos del modelo predictivo
with izquierda:
    with caja("Validación y sesgos del modelo", "exactitud según cómo se evalúa y según la calidad del dato"):
        validaciones = m["validaciones"]
        calidad = m["porCalidad"]
        filas = [[e, f"{numero(v * 100)}%"] for e, v in zip(validaciones["Evaluación"], validaciones["Exactitud"])]
        plural = {"Estimado": "estimados", "Imputado": "imputados", "Oficial": "oficiales"}
        filas += [[f"Datos {plural.get(c, c)} ({n} registros)", f"{numero(v * 100)}%"]
                  for c, n, v in zip(calidad.index, calidad["Registros"], calidad["Exactitud"])]
        st.table(pd.DataFrame(filas, columns=["Evaluación", "Exactitud"]).set_index("Evaluación").rename_axis(None))
        st.caption("La exactitud es mayor donde el dato es imputado por la FAO y menor donde es oficial. "
                   "Repetir el último nivel conocido acierta casi igual: la pérdida cambia poco de un año a otro.")

# Metodología CRISP-DM
with derecha:
    with caja("Metodología CRISP-DM", "fases del proyecto"):
        st.table(pd.DataFrame([
            ["Fase 1: Comprensión del negocio", "Pregunta, objetivo, usuario y 6 KPIs"],
            ["Fase 2: Comprensión de los datos", "4 bases FAOSTAT, faltantes, calidad del dato y atípicos"],
            ["Fase 3: Preparación de los datos", "Limpieza, unión por país + producto + año y bases de modelado"],
            ["Fase 4: Modelado", "PCA, logística, Random Forest, K-means, Chi², MCA, tendencias y modelo predictivo"],
            ["Fase 5: Evaluación", "Validación cruzada, prueba temporal, métricas, hipótesis y sesgos"],
            ["Fase 6: Despliegue", "Este dashboard (Streamlit Community Cloud)"],
        ], columns=["Fase", "Qué se hizo"]).set_index("Fase").rename_axis(None))
