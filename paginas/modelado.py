# ## MODELADO MULTIVARIADO (SEGUNDA ENTREGA) ##

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import procesamiento as pr
from comun import (cargarResultados, numero, pvalor, nota, verTabla, estiloGrafico, lineaReferencia, caja,
                   colorTipo, colorGrupo, rojo, azul, gris, verdeOscuro, naranja)

exploratorio, modelado = cargarResultados()
m = modelado
baseModelo = pr.traducir(m["baseModelo"])

# Nombres legibles de las variables
nombresVariables = {
    "TasaPerdida": "Tasa de pérdida", "logPerdida": "Pérdida (t, log)",
    "logPerdidaUSD": "Pérdida económica (USD, log)", "IndiceRendimiento": "Índice de rendimiento",
    "DependenciaImportadora": "Dependencia importadora", "OrientacionExportadora": "Orientación exportadora",
    "logExportUSD": "Valor exportado (log)", "logImportUSD": "Valor importado (log)",
    "Perecedero": "Perecedero", "DatoEstimado": "Dato estimado", "Sudamerica": "Sudamérica",
    "logOferta": "Oferta (log)", "logPrecio": "Precio al productor (log)",
}
nombresDimension = {"PC1": "Escala de la pérdida y del comercio",
                    "PC2": "Pérdida relativa frente a orientación exportadora",
                    "PC3": "Dependencia importadora", "PC4": "Productividad"}

st.title("Modelado multivariado")
st.caption(f"Segunda entrega. Unidad de análisis: {len(baseModelo)} combinaciones país-producto "
           f"(mediana 2010–2023). Punto crítico = tasa de pérdida mediana ≥ 10% "
           f"({baseModelo['Critico'].sum()} combinaciones, {numero(baseModelo['Critico'].mean() * 100)}%).")

tabs = st.tabs(["Hipótesis", "Análisis factorial (PCA)", "Clasificación", "K-means", "Asociación", "Tendencias"])

# ## Hipótesis ##
with tabs[0]:
    pCalidad = m["asociaciones"].set_index("Variable").loc["Calidad", "p-valor"]
    pPerecedero = m["tablaOR"].loc["Perecedero", "p-valor Wald"]
    hipotesis = pd.DataFrame([
        ["H1", "Los indicadores están correlacionados y pueden resumirse en pocas dimensiones",
         f"Bartlett y KMO ({numero(m['kmoGlobal'], 2)})", pvalor(m["pB"]),
         "Se acepta" if m["pB"] < 0.05 and m["kmoGlobal"] >= 0.6 else "Se rechaza"],
        ["H2", "Ser perecedero aumenta la probabilidad de ser punto crítico",
         f"Wald, regresión logística (OR = {numero(m['tablaOR'].loc['Perecedero', 'OR'])})", pvalor(pPerecedero),
         "Se acepta" if pPerecedero < 0.05 and m["tablaOR"].loc["Perecedero", "OR"] > 1 else "Se rechaza"],
        ["H3", "La calidad del dato de pérdida está asociada con ser punto crítico", "Chi²", pvalor(pCalidad),
         "Se acepta" if pCalidad < 0.05 else "Se rechaza"],
        ["H4", "La tasa de pérdida regional cambió entre 2010 y 2023 (sin soya)",
         f"Pendiente de la regresión lineal ({numero(m['rSinSoya'].slope, 3)} p.p./año)", pvalor(m["rSinSoya"].pvalue),
         "Se acepta" if m["rSinSoya"].pvalue < 0.05 else "Se rechaza"],
    ], columns=["#", "Hipótesis (H1)", "Prueba", "p-valor", "Decisión"])
    with caja("Prueba de hipótesis (nivel de significancia 0,05)"):
        st.table(hipotesis.set_index("#"))
    nota("Si el p-valor es menor a 0,05, se rechaza H0 y se acepta la hipótesis. En H1 también se exige un "
         "KMO ≥ 0,6 (escala de Kaiser vista en clase: menos de 0,6 es inaceptable, de 0,6 a 0,8 es regular).")

# ## Análisis factorial (PCA) ##
with tabs[1]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("KMO global", numero(m["kmoGlobal"], 2), help="≥ 0,6: adecuado para el análisis (regular de 0,6 a 0,8)")
    c2.metric("Bartlett (p-valor)", pvalor(m["pB"]), help="H0: no hay correlación entre las variables")
    c3.metric("Componentes", m["nComponentes"], help="Criterio: explicar al menos el 80% de la varianza")
    c4.metric("Varianza explicada", f"{numero(m['acumulada'][m['nComponentes'] - 1] * 100)}%")
    if m["retiradas"]:
        st.caption("Variables retiradas por KMO individual < 0,5: " + ", ".join(
            f"{nombresVariables[v]} ({numero(k, 2)})" for v, k in m["retiradas"]))

    izquierda, derecha = st.columns([1, 1.3])

    # Curva de varianza acumulada
    with izquierda:
        with caja("Varianza acumulada por componente"):
            etiquetasPC = [f"PC{i + 1}" for i in range(len(m["acumulada"]))]
            fig = go.Figure(go.Scatter(x=etiquetasPC, y=m["acumulada"], mode="lines+markers+text",
                                       text=[numero(v, 2) for v in m["acumulada"]],
                                       textposition=["bottom right"] * (len(m["acumulada"]) - 2) + ["bottom center", "top center"],
                                       line=dict(color=rojo, width=2), marker=dict(size=9),
                                       hovertemplate="%{x}: %{y:.1%} acumulado<extra></extra>"))
            lineaReferencia(fig, 0.8, "80%")
            fig.update_layout(yaxis=dict(range=[0, 1.08], tickformat=".0%"), margin=dict(t=20))
            st.plotly_chart(estiloGrafico(fig, 440), width="stretch")

    # Biplot: puntos = país-producto, flechas = variables
    with derecha:
        with caja("Biplot: combinaciones (puntos) y variables (flechas)"):
            puntajes = pr.traducir(m["puntajes"])
            puntajes["Tipo"] = baseModelo["Perecedero"].map({1: "Perecedero", 0: "Grano"}).values
            puntajes["Combinación"] = puntajes["Pais"] + " · " + puntajes["Producto"]
            fig = px.scatter(puntajes, x="PC1", y="PC2", color="Tipo", color_discrete_map=colorTipo,
                             hover_name="Combinación", hover_data={"PC1": ":.2f", "PC2": ":.2f", "Tipo": False},
                             labels={"PC1": f"PC1 ({numero(m['varianza'][0] * 100)}%)",
                                     "PC2": f"PC2 ({numero(m['varianza'][1] * 100)}%)"})
            fig.update_traces(marker=dict(size=8, opacity=.6, line=dict(width=1, color="white")))
            escala = 4
            desplazamiento = {"logPerdida": 14, "logPerdidaUSD": -12}
            nombresCortos = {**nombresVariables, "logPerdida": "Pérdida t (log)", "logPerdidaUSD": "Pérdida USD (log)",
                             "logExportUSD": "Exportado (log)", "OrientacionExportadora": "Orient. exportadora",
                             "DependenciaImportadora": "Dep. importadora", "IndiceRendimiento": "Rendimiento"}
            for v in m["variablesPCA"]:
                x, y = m["cargas"].loc[v, "PC1"] * escala, m["cargas"].loc[v, "PC2"] * escala
                fig.add_annotation(x=x, y=y, ax=0, ay=0, xref="x", yref="y", axref="x", ayref="y",
                                   showarrow=True, arrowhead=2, arrowwidth=2, arrowcolor=verdeOscuro, text="")
                fig.add_annotation(x=x * 1.12, y=y * 1.12, text=f"<b>{nombresCortos[v]}</b>", showarrow=False,
                                   yshift=desplazamiento.get(v, 0), xanchor="left" if x >= 0 else "right",
                                   font=dict(size=11, color=verdeOscuro), bgcolor="rgba(255,255,255,.8)")
            for etiqueta in ["Venezuela · Tomate", "Brasil · Soya"]:
                fila = puntajes[puntajes["Combinación"] == etiqueta].iloc[0]
                fig.add_annotation(x=fila["PC1"], y=fila["PC2"], text=etiqueta, showarrow=True, arrowhead=0,
                                   ax=-60 if fila["PC1"] > 3 else 50, ay=-18, font=dict(size=11))
            fig.add_hline(y=0, line_color="#ccc", line_width=1); fig.add_vline(x=0, line_color="#ccc", line_width=1)
            fig.update_layout(xaxis=dict(range=[-4.5, 5.6]), margin=dict(t=20))
            st.plotly_chart(estiloGrafico(fig, 440), width="stretch")

    nota("La flecha de <b>tasa de pérdida</b> apunta hacia arriba y las de <b>pérdida en toneladas y en USD</b> "
         "hacia la derecha: no se mueven juntas. Por eso el tomate de Venezuela queda arriba (tasa alta) y la soya "
         "de Brasil a la derecha (mucho volumen, tasa baja). Pasa el mouse sobre los puntos para ver cada combinación.")

    # Cargas y Alfa de Cronbach por dimensión
    cargas = m["cargas"].copy()
    tablaDimensiones = []
    for pc in m["nombresPC"]:
        variables = cargas.index[cargas["Dimensión"] == pc]
        alfa = m["alfas"][pc]
        tablaDimensiones.append({
            "Componente": pc, "Dimensión": nombresDimension.get(pc, pc),
            "Variables (carga)": ", ".join(f"{nombresVariables[v]} ({numero(cargas.loc[v, pc], 2)})" for v in variables),
            "Alfa de Cronbach (IC 95%)": "No aplica" if alfa is None else
            f"{numero(alfa[0], 2)} [{numero(alfa[1][0], 2)}; {numero(alfa[1][1], 2)}]",
            "Lectura": "Una sola variable" if alfa is None else
            ("Adecuado" if alfa[0] >= 0.7 else ("Necesita ajustes" if alfa[0] >= 0.5 else "No es consistente"))})
    with caja("Dimensiones encontradas y Alfa de Cronbach"):
        st.table(pd.DataFrame(tablaDimensiones).set_index("Componente"))
        verTabla(cargas.rename(index=nombresVariables).round(2).reset_index(names="Variable"),
                 "Ver la tabla completa de cargas")

    # Controles: probar el PCA con otras variables (como los controles del ejemplo del profe)
    with caja("Prueba el PCA con otras variables"):
        candidatas = ["TasaPerdida", "logPerdida", "logPerdidaUSD", "logOferta", "logPrecio", "IndiceRendimiento",
                      "DependenciaImportadora", "OrientacionExportadora", "logExportUSD", "logImportUSD"]
        elegidas = st.multiselect("Variables numéricas para el PCA", candidatas, default=m["variablesPCA"],
                                  format_func=lambda v: nombresVariables[v])
        if len(elegidas) < 3:
            st.info("Elige al menos 3 variables.")
        else:
            datosPrueba = m["baseModelo"][elegidas].values
            kmoPrueba, kmoIndPrueba = pr.pruebaKMO(datosPrueba)
            _, _, pPrueba = pr.pruebaBartlett(datosPrueba)
            pcaPrueba = PCA().fit(StandardScaler().fit_transform(datosPrueba))
            acumuladaPrueba = pcaPrueba.explained_variance_ratio_.cumsum()
            nPrueba = int(np.argmax(acumuladaPrueba >= 0.80) + 1)
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("KMO global", numero(kmoPrueba, 2),
                      delta="cumple (≥ 0,6)" if kmoPrueba >= 0.6 else "no cumple (< 0,6)",
                      delta_color="normal" if kmoPrueba >= 0.6 else "inverse")
            p2.metric("Bartlett (p-valor)", pvalor(pPrueba))
            p3.metric("Componentes para el 80%", nPrueba)
            p4.metric("Varianza explicada", f"{numero(acumuladaPrueba[nPrueba - 1] * 100)}%")
            bajas = [nombresVariables[v] for v, k in zip(elegidas, kmoIndPrueba) if k < 0.5]
            if bajas:
                st.caption("Con KMO individual < 0,5 (se deberían quitar): " + ", ".join(bajas))
            nota("Agrega el precio, la oferta o el valor importado y mira cómo baja el KMO: por eso se quitaron. "
                 "Los resultados oficiales del proyecto son los de arriba.")

# ## Clasificación ##
with tabs[2]:
    with caja("Regresión logística (criterios de Hosmer-Lemeshow)"):
        izquierda, derecha = st.columns([1.1, 1])
        with izquierda:
            bivariado = m["bivariado"].assign(
                Variable=lambda d: d["Variable"].map(nombresVariables),
                **{"Chi²": lambda d: d["Chi²"].map(lambda v: numero(v, 2)),
                   "p-valor": lambda d: d["p-valor"].map(pvalor)})
            st.caption("Paso 1: análisis bivariado (pasan las variables con p < 0,25)")
            st.dataframe(bivariado, width="stretch", hide_index=True)
            if m["salidas"]:
                st.caption("Pasos 2–4, eliminación backward: salen " + ", ".join(
                    f"{nombresVariables[v]} (p = {numero(p, 3)})" for v, p in m["salidas"]))
        with derecha:
            tablaOR = m["tablaOR"].copy()
            tablaOR.index = ["Intercepto"] + [nombresVariables[v] for v in tablaOR.index[1:]]
            st.caption("Modelo final")
            st.dataframe(pd.DataFrame({
                "Variable": tablaOR.index, "β": tablaOR["Coeficiente"].map(lambda v: numero(v, 3)),
                "OR": tablaOR["OR"].map(lambda v: numero(v, 2)),
                "IC 95% del OR": [f"{numero(a, 2)} – {numero(b, 2)}" for a, b in zip(tablaOR["IC 95% inf"], tablaOR["IC 95% sup"])],
                "p-valor": tablaOR["p-valor Wald"].map(pvalor)}), width="stretch", hide_index=True)
            b = m["tablaOR"]["Coeficiente"]
            st.markdown(f"**ln[p / (1 − p)] = {numero(b['Intercept'], 3)} + {numero(b['Perecedero'], 3)} · Perecedero "
                        f"+ {numero(b['DatoEstimado'], 3)} · DatoEstimado**")

    # Calculadora de probabilidad con el modelo final
    with caja("Probabilidad de ser punto crítico según el modelo"):
        e1, e2, e3 = st.columns([1, 1, 1.4])
        tipoSel = e1.radio("Tipo de producto", ["Perecedero", "Grano"], horizontal=True)
        datoSel = e2.radio("Dato de pérdida", ["Estimado", "Imputado u oficial"], horizontal=True)
        escenario = m["escenarios"]
        probabilidad = escenario[(escenario["Perecedero"] == (tipoSel == "Perecedero")) &
                                 (escenario["DatoEstimado"] == (datoSel == "Estimado"))]["Probabilidad"].iloc[0]
        e3.metric("Probabilidad estimada", f"{numero(probabilidad * 100)}%")
    nota(f"Un perecedero tiene una odds unas <b>{numero(m['tablaOR'].loc['Perecedero', 'OR'])} veces</b> mayor de "
         f"ser crítico que un grano con la misma calidad de dato. El dato estimado (OR = "
         f"{numero(m['tablaOR'].loc['DatoEstimado', 'OR'])}) no es una causa: indica que la FAO usa coeficientes "
         "por defecto altos cuando estima.")

    # Variables con mayor evidencia estadística (−log10 del p-valor del paso 1)
    with caja("Variables con mayor evidencia estadística asociada a ser crítico"):
        evidencia = m["bivariado"].assign(Variable=lambda d: d["Variable"].map(nombresVariables),
                                          Evidencia=lambda d: -np.log10(d["p-valor"])).sort_values("Evidencia")
        fig = px.bar(evidencia, x="Evidencia", y="Variable", orientation="h", color="Tipo",
                     color_discrete_map={"Cualitativa": naranja, "Cuantitativa": verdeOscuro},
                     labels={"Evidencia": "−log10(p-valor)", "Variable": ""})
        fig.add_vline(x=-np.log10(0.05), line_dash="dot", line_color="#888", annotation_text="p = 0,05",
                      annotation_position="bottom right")
        fig.update_traces(marker_cornerradius=4, hovertemplate="%{y}: %{x:.2f}<extra></extra>")
        st.plotly_chart(estiloGrafico(fig, 340), width="stretch")
        st.caption("Mientras más larga la barra, menor el p-valor. Las que pasan la línea punteada son significativas al 5%.")

    # Evaluación con validación cruzada
    metricas = m["metricas"].set_index("Modelo")
    tablaMetricas = pd.DataFrame({
        "Métrica": ["Exactitud", "AUC-ROC", "Sensibilidad", "Especificidad"],
        **{modelo: [f"{numero(metricas.loc[modelo, 'Exactitud'] * 100)}%", numero(metricas.loc[modelo, "AUC"], 3),
                    f"{numero(metricas.loc[modelo, 'Sensibilidad'] * 100)}%", f"{numero(metricas.loc[modelo, 'Especificidad'] * 100)}%"]
           for modelo in metricas.index}}).set_index("Métrica")
    with caja("Evaluación: regresión logística vs Random Forest (validación cruzada de 5 particiones)"):
        g1, g2, g3 = st.columns([1, 1.15, 1])
        with g1:
            st.table(tablaMetricas)
            st.caption("Sensibilidad = críticos detectados. Especificidad = no críticos bien clasificados.")
        with g2:
            fig = go.Figure()
            for modelo, color in [("Regresión logística", azul), ("Random Forest", naranja)]:
                fpr, tpr = m["curvasROC"][modelo]
                fig.add_trace(go.Scatter(x=fpr, y=tpr, mode="lines", line=dict(color=color, width=2),
                                         name=f"{modelo} (AUC = {numero(metricas.loc[modelo, 'AUC'], 3)})",
                                         hovertemplate="1 − esp.: %{x:.2f}<br>Sensibilidad: %{y:.2f}<extra></extra>"))
            fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(color="#aaa", dash="dot"),
                                     name="Azar", hoverinfo="skip"))
            fig.update_layout(xaxis_title="1 − Especificidad", yaxis_title="Sensibilidad", margin=dict(t=20))
            st.plotly_chart(estiloGrafico(fig, 360), width="stretch")
        with g3:
            modeloMatriz = st.selectbox("Matriz de confusión", list(m["matrices"]))
            matriz = m["matrices"][modeloMatriz]
            fig = px.imshow(matriz, text_auto=True, color_continuous_scale="Reds",
                            x=["No crítico", "Crítico"], y=["No crítico", "Crítico"],
                            labels=dict(x="Predicho", y="Real", color="Casos"))
            fig.update_traces(hovertemplate="Real: %{y}<br>Predicho: %{x}<br>Casos: %{z}<extra></extra>",
                              textfont_size=18)
            fig.update_layout(coloraxis_showscale=False, margin=dict(t=10))
            st.plotly_chart(estiloGrafico(fig, 280), width="stretch")
    vn, fp, fn, vp = m["matrices"]["Regresión logística"].ravel()
    nota(f"La exactitud engaña: casi todo viene de los no críticos ({vn} de {vn + fp} bien clasificados). "
         f"La logística detecta {vp} de {vp + fn} críticos y el Random Forest la mitad, por eso se prefiere la logística: "
         "detecta más y se puede interpretar con los OR. En la curva ROC, la diagonal punteada es adivinar al azar.")
    with st.expander("Ver la importancia de variables del Random Forest"):
        importancia = m["importanciaRF"].rename(index=nombresVariables)
        fig = px.bar(x=importancia.values, y=importancia.index, orientation="h", color_discrete_sequence=[rojo],
                     labels={"x": "Importancia (reducción media de impureza)", "y": ""})
        fig.update_traces(hovertemplate="%{y}: %{x:.3f}<extra></extra>", marker_cornerradius=4)
        st.plotly_chart(estiloGrafico(fig, 320), width="stretch")
        st.caption("El Random Forest da más peso a las variables continuas porque ofrecen más puntos de corte, "
                   "pero esas variables no mejoraron la clasificación.")

# ## K-means ##
with tabs[3]:
    perfil = m["perfilGrupos"].loc[["Pérdida alta", "Exportadores", "Bajo volumen"]]
    columnas = st.columns(3)
    for col, (grupo, fila) in zip(columnas, perfil.iterrows()):
        col.markdown(
            f"<div style='border-left:6px solid {colorGrupo[grupo]};background:#F7F4EC;padding:10px 14px;"
            f"border-radius:6px;min-height:92px'><b style='font-size:1.1rem'>{grupo}</b> · "
            f"{int(fila['Combinaciones'])} combinaciones<br>Tasa {numero(fila['TasaPerdida'])}% · Pérdida USD "
            f"{numero(fila['PerdidaMillUSD'])} M<br>{numero(fila['PctCriticos'], 0)}% críticas · exportan "
            f"{numero(fila['OrientacionExportadora'])}% de su oferta</div>", unsafe_allow_html=True)
    st.write("")

    izquierda, derecha = st.columns([1.3, 1])
    grupos = baseModelo.assign(PC1=m["puntajes"]["PC1"].values, PC2=m["puntajes"]["PC2"].values,
                               Combinacion=lambda d: d["Pais"] + " · " + d["Producto"])
    with izquierda:
        with caja("Grupos K-means en el plano de componentes principales"):
            fig = px.scatter(grupos, x="PC1", y="PC2", color="NombreGrupo", color_discrete_map=colorGrupo,
                             category_orders={"NombreGrupo": list(colorGrupo)}, hover_name="Combinacion",
                             hover_data={"TasaPerdida": ":.1f", "Condicion": True, "NombreGrupo": False,
                                         "PC1": False, "PC2": False},
                             labels={"PC1": "PC1: escala de la pérdida y del comercio →",
                                     "PC2": "PC2: ↑ más tasa de pérdida · ↓ más exportación",
                                     "TasaPerdida": "Tasa (%)", "Condicion": "Condición"})
            fig.update_traces(marker=dict(size=9, opacity=.85, line=dict(width=1, color="white")))
            criticos = grupos[grupos["Critico"] == 1]
            fig.add_trace(go.Scatter(x=criticos["PC1"], y=criticos["PC2"], mode="markers", name="Punto crítico",
                                     marker=dict(symbol="circle-open", size=15, color="#222", line=dict(width=1.5)),
                                     hoverinfo="skip"))
            fig.add_hline(y=0, line_color="#ccc", line_width=1); fig.add_vline(x=0, line_color="#ccc", line_width=1)
            fig.update_layout(margin=dict(t=30))
            st.plotly_chart(estiloGrafico(fig, 470), width="stretch")
    with derecha:
        with caja("Perfil de los grupos (1 = máximo entre grupos)"):
            indicadores = {"TasaPerdida": "Tasa de<br>pérdida", "PerdidaMillUSD": "Pérdida<br>económica",
                           "IndiceRendimiento": "Rendimiento", "DependenciaImportadora": "Dependencia<br>importadora",
                           "OrientacionExportadora": "Orientación<br>exportadora", "PctPerecederos": "%<br>perecederos"}
            radar = perfil[list(indicadores)] / perfil[list(indicadores)].max()
            fig = go.Figure()
            for grupo, fila in radar.iterrows():
                etiquetas = list(indicadores.values())
                fig.add_trace(go.Scatterpolar(r=fila.tolist() + fila.tolist()[:1], theta=etiquetas + etiquetas[:1],
                                              name=grupo, fill="toself", opacity=.7,
                                              line=dict(color=colorGrupo[grupo], width=2),
                                              hovertemplate="%{theta}: %{r:.2f}<extra>" + grupo + "</extra>"))
            fig.update_layout(polar=dict(domain=dict(x=[0.16, 0.84], y=[0.04, 0.86]),
                                         radialaxis=dict(visible=True, range=[0, 1.05], showticklabels=False),
                                         angularaxis=dict(tickfont=dict(size=11), rotation=90)),
                              margin=dict(l=80, r=80, t=40, b=40))
            st.plotly_chart(estiloGrafico(fig, 470), width="stretch")

    nota("K-means es <b>no supervisado</b>: no conoce cuáles combinaciones son críticas (círculos negros). Aun así separó "
         "un grupo de pérdida alta, con perecederos de mercado interno, donde están el tomate de Venezuela y de Chile y "
         "la papa de Perú. Coincide con la regresión logística, lo que hace más confiable el resultado.")

    # Buscador de combinaciones
    with caja("¿En qué grupo está una combinación?"):
        b1, b2 = st.columns(2)
        listaPaises = sorted(grupos["Pais"].unique())
        paisBusca = b1.selectbox("País", listaPaises, index=listaPaises.index("Venezuela"))
        productosPais = sorted(grupos.loc[grupos["Pais"] == paisBusca, "Producto"].unique())
        productoBusca = b2.selectbox("Producto", productosPais,
                                     index=productosPais.index("Tomate") if "Tomate" in productosPais else 0)
        fila = grupos[(grupos["Pais"] == paisBusca) & (grupos["Producto"] == productoBusca)].iloc[0]
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Grupo", fila["NombreGrupo"])
        r2.metric("Tasa de pérdida mediana", f"{numero(fila['TasaPerdida'])}%",
                  help="Mediana de los años con precio y comercio (base de modelado)")
        r3.metric("Condición", fila["Condicion"])
        r4.metric("Calidad del dato", fila["Calidad"])

    with st.expander("Ver el método del codo"):
        fig = px.line(x=m["inercias"].index, y=m["inercias"].values, markers=True, color_discrete_sequence=[rojo],
                      labels={"x": "Número de grupos (k)", "y": "Inercia"})
        st.plotly_chart(estiloGrafico(fig, 300), width="stretch")
        st.caption("El codo no es muy marcado; se eligieron 3 grupos porque dan perfiles claros.")

# ## Asociación ##
with tabs[4]:
    nombresAsociacion = {"Tipo": "Tipo de producto", "Calidad": "Calidad del dato", "Region": "Subregión",
                         "Rendimiento": "Nivel de rendimiento", "Comercio": "Tipo de comercio"}
    izquierda, derecha = st.columns([1, 1.15])
    with izquierda:
        with caja("Prueba Chi² (H0: no hay asociación con ser crítico)"):
            asociaciones = m["asociaciones"].rename(columns={"¿Hay asociación? (p < 0,05)": "¿Asociación?"}).assign(
                Variable=lambda d: d["Variable"].map(nombresAsociacion),
                **{"Chi²": lambda d: d["Chi²"].map(lambda v: numero(v, 2)),
                   "p-valor": lambda d: d["p-valor"].map(pvalor)})
            st.dataframe(asociaciones, width="stretch", hide_index=True)
        with caja("Combinaciones críticas según la calidad del dato"):
            porCalidad = m["criticosCalidad"].reset_index()
            porCalidad.columns = ["Calidad del dato", "% críticas"]
            fig = px.bar(porCalidad, x="Calidad del dato", y="% críticas", text="% críticas",
                         color_discrete_sequence=[naranja])
            fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside", marker_cornerradius=4,
                              hovertemplate="%{x}: %{y:.1f}% críticas<extra></extra>")
            fig.update_yaxes(range=[0, max(porCalidad["% críticas"]) * 1.25], title="% de combinaciones críticas")
            fig.update_layout(margin=dict(t=20))
            st.plotly_chart(estiloGrafico(fig, 300), width="stretch")

    with derecha:
        with caja("Análisis de correspondencias múltiples (MCA)"):
            coordenadas = m["coordenadasMCA"].copy()
            coordenadas["Variable"] = [c.split("__")[0] for c in coordenadas.index]
            coordenadas["Categoría"] = [c.split("__")[1] for c in coordenadas.index]
            coordenadas["Variable"] = coordenadas["Variable"].map({**nombresAsociacion, "Condicion": "Condición"})
            coloresMCA = {"Condición": "#000000", "Tipo de producto": rojo, "Calidad del dato": gris,
                          "Subregión": azul, "Nivel de rendimiento": "#27ae60", "Tipo de comercio": "#8e44ad"}
            fig = px.scatter(coordenadas, x="Dim1", y="Dim2", color="Variable", text="Categoría",
                             color_discrete_map=coloresMCA,
                             labels={"Dim1": f"Dimensión 1 ({numero(m['inerciaMCA'][0])}%)",
                                     "Dim2": f"Dimensión 2 ({numero(m['inerciaMCA'][1])}%)"})
            fig.update_traces(textposition="top center", marker=dict(size=10, line=dict(width=1, color="white")),
                              textfont_size=11, hovertemplate="%{text}<extra></extra>")
            fig.add_hline(y=0, line_color="#ccc", line_width=1); fig.add_vline(x=0, line_color="#ccc", line_width=1)
            x0, x1 = coordenadas["Dim1"].min(), coordenadas["Dim1"].max()
            fig.update_layout(xaxis=dict(range=[x0 - 0.45, x1 + 0.3]), margin=dict(t=60))
            st.plotly_chart(estiloGrafico(fig, 560), width="stretch")

    nota("Solo el <b>tipo de producto</b> y la <b>calidad del dato</b> están asociados con ser crítico (p < 0,05). "
         "En el MCA, las categorías cercanas aparecen juntas: Crítico queda cerca de Perecedero, Estimado y Mercado "
         f"interno. Las dos dimensiones explican el {numero(sum(m['inerciaMCA']))}% de la inercia, por eso se usan para "
         "ver cercanías. Asociación no es causalidad.")

# ## Tendencias ##
with tabs[5]:
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Pendiente regional sin soya", f"{numero(m['rSinSoya'].slope, 3)} p.p./año",
              help=f"p-valor {pvalor(m['rSinSoya'].pvalue)} · R² = {numero(m['rSinSoya'].rvalue ** 2, 2)}")
    t2.metric("Con los 10 productos", f"{numero(m['rTotal'].slope, 3)} p.p./año",
              help=f"p-valor {numero(m['rTotal'].pvalue, 2)}: no significativa por el salto de la soya")
    t3.metric("Proyección a 2030", f"{numero(m['proyeccion2030'])}%")
    t4.metric("Meta ODS 12.3", f"{numero(m['meta2030'])}%", help="La mitad de la tasa de 2015 (sin soya)")

    with caja("Tasa de pérdida regional, recta de regresión y meta ODS 12.3"):
        serieTotal, serieSinSoya, rSinSoya = m["serieTotal"], m["serieSinSoya"], m["rSinSoya"]
        aniosRecta = np.arange(2010, 2031)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=serieTotal.index, y=serieTotal.values, mode="lines+markers", name="10 productos",
                                 line=dict(color=gris, width=2), hovertemplate="%{x}: %{y:.2f}%<extra>10 productos</extra>"))
        fig.add_trace(go.Scatter(x=serieSinSoya.index, y=serieSinSoya.values, mode="lines+markers", name="Sin soya",
                                 line=dict(color=rojo, width=2), hovertemplate="%{x}: %{y:.2f}%<extra>Sin soya</extra>"))
        fig.add_trace(go.Scatter(x=aniosRecta, y=rSinSoya.intercept + rSinSoya.slope * aniosRecta, mode="lines",
                                 name="Recta de regresión sin soya", line=dict(color=rojo, dash="dash", width=1.5),
                                 hovertemplate="%{x}: %{y:.2f}%<extra>Recta</extra>"))
        lineaReferencia(fig, m["meta2030"], f"Meta ODS 12.3 ({numero(m['meta2030'])}%)", azul)
        fig.update_layout(yaxis=dict(range=[0, 9], title="Tasa (%)"), margin=dict(t=30))
        st.plotly_chart(estiloGrafico(fig, 420), width="stretch")
    nota("Se excluye la soya porque Brasil cambió su forma de reporte en 2019. Sin ella, la tasa baja levemente, "
         "pero al ritmo actual no llega a la meta de 2030. La proyección es una extrapolación, no una certeza.")

    tendencia = pr.traducir(m["tendenciaProducto"])
    tablaTendencia = pd.DataFrame({
        "Producto": tendencia["Producto"],
        "Pendiente (p.p./año)": tendencia["Pendiente (p.p./año)"].map(lambda v: numero(v, 3)),
        "p-valor": tendencia["p-valor"].map(pvalor), "R²": tendencia["R²"].map(lambda v: numero(v, 2)),
        "RMSE": tendencia["RMSE"].map(lambda v: numero(v, 2)), "MAE": tendencia["MAE"].map(lambda v: numero(v, 2)),
        "Tasa 2010 (%)": tendencia["Tasa 2010"].map(numero), "Tasa 2023 (%)": tendencia["Tasa 2023"].map(numero),
        "Tendencia": tendencia["Tendencia"]})
    with caja("Tendencia por producto (regresión lineal de la tasa sobre el año)"):
        st.dataframe(tablaTendencia, width="stretch", hide_index=True)
