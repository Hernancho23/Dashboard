# ## PROCESAMIENTO DE LOS DATOS ##
# Reproduce el notebook "Detección de puntos críticos de pérdida de alimentos v2":
# carga, unión de las 4 bases, KPIs, base de modelado, PCA, logística, Random Forest,
# K-means, asociación (Chi² y MCA) y tendencias. Las páginas solo leen estos resultados.

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score, roc_curve

carpetaDatos = Path(__file__).parent / "datos"

# Nombres en español para mostrar en el dashboard
nombresCortos = {
    "Venezuela (Bolivarian Republic of)": "Venezuela",
    "Bolivia (Plurinational State of)": "Bolivia",
    "Dominican Republic": "Rep. Dominicana",
}
paisesEspanol = {
    "Argentina": "Argentina", "Bolivia": "Bolivia", "Brazil": "Brasil", "Chile": "Chile",
    "Colombia": "Colombia", "Costa Rica": "Costa Rica", "Rep. Dominicana": "Rep. Dominicana",
    "Ecuador": "Ecuador", "El Salvador": "El Salvador", "Honduras": "Honduras", "Mexico": "México",
    "Nicaragua": "Nicaragua", "Panama": "Panamá", "Paraguay": "Paraguay", "Peru": "Perú",
    "Uruguay": "Uruguay", "Venezuela": "Venezuela",
}
productosEspanol = {
    "Tomatoes": "Tomate", "Avocados": "Aguacate", "Carrots and turnips": "Zanahoria",
    "Bananas": "Banano", "Potatoes": "Papa", "Coffee, green": "Café verde", "Beans, dry": "Fríjol seco",
    "Maize (corn)": "Maíz", "Rice": "Arroz", "Soya beans": "Soya",
}
perecederos = ["Tomatoes", "Avocados", "Carrots and turnips", "Bananas", "Potatoes"]
sudamerica = ["Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Ecuador",
              "Paraguay", "Peru", "Uruguay", "Venezuela"]


def traducir(df):
    # Cambia los nombres de países y productos al español (solo para mostrar)
    df = df.copy()
    if "Pais" in df.columns:
        df["Pais"] = df["Pais"].replace(paisesEspanol)
    if "Producto" in df.columns:
        df["Producto"] = df["Producto"].replace(productosEspanol)
    return df


# ## Funciones del análisis factorial (iguales al notebook) ##

def pruebaKMO(datos):
    # Compara las correlaciones simples con las correlaciones parciales
    R = np.corrcoef(datos.T)
    Rinv = np.linalg.inv(R)
    parcial = -Rinv / np.sqrt(np.outer(np.diag(Rinv), np.diag(Rinv)))
    np.fill_diagonal(R, 0); np.fill_diagonal(parcial, 0)
    r2 = (R ** 2).sum(axis=0); p2 = (parcial ** 2).sum(axis=0)
    return r2.sum() / (r2.sum() + p2.sum()), r2 / (r2 + p2)


def pruebaBartlett(datos):
    # H0: no hay correlación entre las variables
    n, p = datos.shape
    R = np.corrcoef(datos.T)
    chi2 = -(n - 1 - (2 * p + 5) / 6) * np.log(np.linalg.det(R))
    gl = p * (p - 1) / 2
    return chi2, gl, stats.chi2.sf(chi2, gl)


def alfaCronbach(items, confianza=0.95):
    # Alfa = k/(k-1) * (1 - suma de varianzas de los ítems / varianza del total)
    k, n = items.shape[1], len(items)
    alfa = k / (k - 1) * (1 - items.var(ddof=1).sum() / items.sum(axis=1).var(ddof=1))
    gl1, gl2 = n - 1, (n - 1) * (k - 1)
    a = 1 - confianza
    ic = (1 - (1 - alfa) * stats.f.ppf(1 - a / 2, gl1, gl2), 1 - (1 - alfa) * stats.f.ppf(a / 2, gl1, gl2))
    return alfa, ic


def correspondenciasMultiples(datos, nDimensiones=2):
    # Tabla disyuntiva, residuos estandarizados y descomposición en valores singulares
    Z = pd.get_dummies(datos, prefix_sep="__").astype(float)
    P = Z / Z.values.sum()
    filas, columnas = P.sum(axis=1).values, P.sum(axis=0).values
    S = (P.values - np.outer(filas, columnas)) / np.sqrt(np.outer(filas, columnas))
    U, valoresSingulares, Vt = np.linalg.svd(S, full_matrices=False)
    autovalores = valoresSingulares ** 2
    coordenadas = pd.DataFrame(Vt.T[:, :nDimensiones] * valoresSingulares[:nDimensiones] / np.sqrt(columnas)[:, None],
                               index=Z.columns, columns=[f"Dim{i+1}" for i in range(nDimensiones)])
    return autovalores, coordenadas


def tasaRegional(base):
    # Tasa de pérdida regional por año = pérdida total / oferta total
    t = base.groupby("Año")[["Perdida", "Oferta"]].sum()
    return t["Perdida"] / t["Oferta"] * 100


# ## Carga y unión de las bases (Evento 1) ##

def cargarBases():
    # Creación de los dataframe (mismo formato del notebook)
    lectura = dict(sep=";", decimal=",", encoding="latin1")
    sua = pd.read_csv(carpetaDatos / "SUA_Limpia.csv", **lectura)
    produccion = pd.read_csv(carpetaDatos / "Produccion_Limpia.csv", **lectura)
    precios = pd.read_csv(carpetaDatos / "Precios_Limpia.csv", **lectura)
    trade = pd.read_csv(carpetaDatos / "Trade_Limpia.csv", **lectura)
    return sua, produccion, precios, trade


def procesarExploratorio():
    sua, produccion, precios, trade = cargarBases()

    # Pivot de Producción y Trade, pérdidas y precios
    llave = ["Pais", "Producto", "Año"]
    produccionPivot = produccion.pivot_table(index=llave, columns="Elemento", values="Valor", aggfunc="first").reset_index()
    produccionPivot.columns.name = None
    tradePivot = trade.pivot_table(index=llave, columns="Elemento", values="Valor", aggfunc="first").reset_index()
    tradePivot.columns.name = None
    perdidasLimpio = sua[sua["Elemento"] == "Loss"][llave + ["Valor"]].rename(columns={"Valor": "Perdida"})
    preciosLimpio = precios[llave + ["Valor"]].rename(columns={"Valor": "Precio_USD_ton"})

    # Países presentes en las cuatro bases (17)
    paisesComunes = (set(produccionPivot["Pais"]) & set(perdidasLimpio["Pais"])
                     & set(preciosLimpio["Pais"]) & set(tradePivot["Pais"]))
    produccion17 = produccionPivot[produccionPivot["Pais"].isin(paisesComunes)].copy()
    perdidas17 = perdidasLimpio[perdidasLimpio["Pais"].isin(paisesComunes)].copy()
    precios17 = preciosLimpio[preciosLimpio["Pais"].isin(paisesComunes)].copy()
    trade17 = tradePivot[tradePivot["Pais"].isin(paisesComunes)].copy()

    # Base maestra: unión de las cuatro bases por País + Producto + Año
    baseMaestra = (produccion17.merge(perdidas17, on=llave, how="inner")
                   .merge(precios17, on=llave, how="inner")
                   .merge(trade17, on=llave, how="inner"))

    # KPI 1, 2 y 6: pérdida total, tasa de pérdida y dependencia importadora
    sua17 = sua[sua["Pais"].isin(paisesComunes)]
    suaAncho = sua17.pivot_table(index=llave, columns="Elemento", values="Valor", aggfunc="first").reset_index()
    suaAncho.columns.name = None
    suaAncho["Oferta"] = suaAncho[["Production", "Import quantity"]].sum(axis=1)
    basePerdidas = (suaAncho[llave + ["Loss", "Import quantity", "Oferta"]]
                    .rename(columns={"Loss": "Perdida", "Import quantity": "Importaciones"})
                    .dropna(subset=["Perdida"]))
    basePerdidas = basePerdidas[basePerdidas["Oferta"] > 0].copy()
    basePerdidas["TasaPerdida"] = basePerdidas["Perdida"] / basePerdidas["Oferta"] * 100
    basePerdidas["DependenciaImportadora"] = basePerdidas["Importaciones"].fillna(0) / basePerdidas["Oferta"] * 100

    # KPI 3 y 5: pérdida económica y pérdida sobre exportaciones (Trade en miles de USD)
    baseMaestra["PerdidaUSD"] = baseMaestra["Perdida"] * baseMaestra["Precio_USD_ton"]
    baseMaestra["ExportUSD"] = baseMaestra["Export value"] * 1000
    baseMaestra["ImportUSD"] = baseMaestra["Import value"] * 1000
    baseMaestra["PerdidaSobreExport"] = (baseMaestra["PerdidaUSD"] / baseMaestra["ExportUSD"] * 100
                                         ).replace([np.inf, -np.inf], np.nan)

    # KPI 4: índice de rendimiento (país vs mediana regional del producto-año)
    rendimiento = produccion17[llave + ["Yield"]].dropna(subset=["Yield"]).copy()
    rendimiento["YieldRegional"] = rendimiento.groupby(["Producto", "Año"])["Yield"].transform("median")
    rendimiento["IndiceRendimiento"] = rendimiento["Yield"] / rendimiento["YieldRegional"] * 100
    basePerdidas = basePerdidas.merge(rendimiento[llave + ["IndiceRendimiento"]], on=llave, how="left")

    # Calidad del dato de pérdida
    calidad = sua17[sua17["Elemento"] == "Loss"][llave + ["Calidad"]].copy()
    basePerdidas = basePerdidas.merge(calidad, on=llave, how="left")

    # Atípicos de la tasa de pérdida por producto (IQR)
    cuartiles = basePerdidas.groupby("Producto")["TasaPerdida"].quantile([0.25, 0.75]).unstack()
    cuartiles.columns = ["Q1", "Q3"]
    cuartiles["LimiteSuperior"] = cuartiles["Q3"] + 1.5 * (cuartiles["Q3"] - cuartiles["Q1"])
    basePerdidas = basePerdidas.merge(cuartiles[["LimiteSuperior"]], left_on="Producto", right_index=True, how="left")
    basePerdidas["AtipicoTasa"] = basePerdidas["TasaPerdida"] > basePerdidas["LimiteSuperior"]

    # Nombres cortos de países
    basePerdidas["Pais"] = basePerdidas["Pais"].replace(nombresCortos)
    baseMaestra["Pais"] = baseMaestra["Pais"].replace(nombresCortos)
    suaAncho["Pais"] = suaAncho["Pais"].replace(nombresCortos)
    sua17 = sua17.assign(Pais=sua17["Pais"].replace(nombresCortos))

    return {"basePerdidas": basePerdidas, "baseMaestra": baseMaestra, "suaAncho": suaAncho, "sua17": sua17,
            "bases": {"SUA": sua, "Producción": produccion, "Precios": precios, "Trade": trade}}


def kpisPorPais(basePerdidas, baseMaestra):
    # Resumen de los 6 KPIs por país (sobre la base filtrada que reciba)
    resumenFisico = basePerdidas.groupby("Pais").agg(
        PerdidaTotal=("Perdida", "sum"), Oferta=("Oferta", "sum"),
        Importaciones=("Importaciones", "sum"), IndiceRendimiento=("IndiceRendimiento", "median"))
    resumenFisico["TasaPerdida"] = resumenFisico["PerdidaTotal"] / resumenFisico["Oferta"] * 100
    resumenFisico["DependenciaImportadora"] = resumenFisico["Importaciones"] / resumenFisico["Oferta"] * 100

    conExport = baseMaestra[baseMaestra["ExportUSD"] > 0]
    resumenEconomico = baseMaestra.groupby("Pais").agg(PerdidaUSD=("PerdidaUSD", "sum"))
    resumenEconomico["PerdidaSobreExport"] = (conExport.groupby("Pais")["PerdidaUSD"].sum()
                                             / conExport.groupby("Pais")["ExportUSD"].sum() * 100)

    kpis = resumenFisico.join(resumenEconomico, how="left")
    return kpis[["PerdidaTotal", "TasaPerdida", "PerdidaUSD", "IndiceRendimiento",
                 "PerdidaSobreExport", "DependenciaImportadora"]]


# ## Modelado multivariado (Evento 2) ##

def procesarModelado(exploratorio):
    basePerdidas = exploratorio["basePerdidas"]
    baseMaestra = exploratorio["baseMaestra"]
    suaAncho = exploratorio["suaAncho"]
    sua17 = exploratorio["sua17"]
    llave = ["Pais", "Producto", "Año"]
    r = {}

    # Base de modelado: una fila por país-producto (mediana 2010-2023)
    suaExtra = suaAncho[llave + ["Export quantity"]]
    calidadPerdida17 = sua17[sua17["Elemento"] == "Loss"][llave + ["Calidad"]]
    baseAnual = (basePerdidas[llave + ["Perdida", "Oferta", "TasaPerdida", "DependenciaImportadora", "IndiceRendimiento"]]
                 .merge(baseMaestra[llave + ["Precio_USD_ton", "PerdidaUSD", "ExportUSD", "ImportUSD"]], on=llave, how="inner")
                 .merge(suaExtra, on=llave, how="left")
                 .merge(calidadPerdida17, on=llave, how="left"))
    baseAnual["OrientacionExportadora"] = (baseAnual["Export quantity"].fillna(0) / baseAnual["Oferta"] * 100).clip(upper=100)
    baseAnual["DatoEstimado"] = (baseAnual["Calidad"] == "Estimated value").astype(int)
    baseAnual["DatoImputado"] = (baseAnual["Calidad"] == "Value imputed by a receiving agency").astype(int)

    baseModelo = baseAnual.groupby(["Pais", "Producto"]).agg(
        TasaPerdida=("TasaPerdida", "median"), Perdida=("Perdida", "median"),
        PerdidaUSD=("PerdidaUSD", "median"), Oferta=("Oferta", "median"),
        Precio=("Precio_USD_ton", "median"), IndiceRendimiento=("IndiceRendimiento", "median"),
        DependenciaImportadora=("DependenciaImportadora", "median"),
        OrientacionExportadora=("OrientacionExportadora", "median"),
        ExportUSD=("ExportUSD", "median"), ImportUSD=("ImportUSD", "median"),
        PropEstimado=("DatoEstimado", "mean"), PropImputado=("DatoImputado", "mean")).reset_index()
    baseModelo = baseModelo.dropna(subset=["IndiceRendimiento"]).reset_index(drop=True)
    baseModelo["Calidad"] = np.select([baseModelo["PropEstimado"] >= 0.5, baseModelo["PropImputado"] >= 0.5],
                                      ["Estimado", "Imputado"], "Oficial")
    baseModelo["Perecedero"] = baseModelo["Producto"].isin(perecederos).astype(int)
    baseModelo["DatoEstimado"] = (baseModelo["Calidad"] == "Estimado").astype(int)
    baseModelo["Sudamerica"] = baseModelo["Pais"].isin(sudamerica).astype(int)
    baseModelo["Critico"] = (baseModelo["TasaPerdida"].round(1) >= 10).astype(int)
    baseModelo["logPerdida"] = np.log10(baseModelo["Perdida"] + 1)
    baseModelo["logPerdidaUSD"] = np.log10(baseModelo["PerdidaUSD"] + 1)
    baseModelo["logOferta"] = np.log10(baseModelo["Oferta"])
    baseModelo["logPrecio"] = np.log10(baseModelo["Precio"])
    baseModelo["logExportUSD"] = np.log10(baseModelo["ExportUSD"].fillna(0) + 1)
    baseModelo["logImportUSD"] = np.log10(baseModelo["ImportUSD"].fillna(0) + 1)

    # PCA: se retira la variable con KMO individual < 0,5 hasta que todas lo superen
    variablesPCA = ["TasaPerdida", "logPerdida", "logPerdidaUSD", "IndiceRendimiento",
                    "DependenciaImportadora", "OrientacionExportadora", "logExportUSD", "logImportUSD"]
    retiradas = []
    while True:
        kmoGlobal, kmoIndividual = pruebaKMO(baseModelo[variablesPCA].values)
        if kmoIndividual.min() >= 0.5:
            break
        retiradas.append((variablesPCA[kmoIndividual.argmin()], kmoIndividual.min()))
        variablesPCA.pop(int(kmoIndividual.argmin()))
    datosPCA = baseModelo[variablesPCA]
    chi2B, glB, pB = pruebaBartlett(datosPCA.values)

    datosEstandar = StandardScaler().fit_transform(datosPCA)
    pca = PCA().fit(datosEstandar)
    acumulada = pca.explained_variance_ratio_.cumsum()
    nComponentes = int(np.argmax(acumulada >= 0.80) + 1)
    nombresPC = [f"PC{i+1}" for i in range(nComponentes)]
    cargas = pd.DataFrame(pca.components_[:nComponentes].T, index=variablesPCA, columns=nombresPC)
    cargas["Dimensión"] = cargas[nombresPC].abs().idxmax(axis=1)
    puntajes = pd.DataFrame(pca.transform(datosEstandar)[:, :nComponentes], columns=nombresPC)
    puntajes[["Pais", "Producto"]] = baseModelo[["Pais", "Producto"]].values

    # Alfa de Cronbach por dimensión
    datosZ = pd.DataFrame(datosEstandar, columns=variablesPCA)
    alfas = {}
    for pc in nombresPC:
        seleccion = cargas.index[cargas["Dimensión"] == pc].tolist()
        if len(seleccion) > 1:
            alfas[pc] = alfaCronbach(datosZ[seleccion] * np.sign(cargas.loc[seleccion, pc].values))
        else:
            alfas[pc] = None

    r.update(variablesPCA=variablesPCA, retiradas=retiradas, kmoGlobal=kmoGlobal,
             kmoIndividual=pd.Series(kmoIndividual, index=variablesPCA), chi2B=chi2B, glB=glB, pB=pB,
             varianza=pca.explained_variance_ratio_, acumulada=acumulada, nComponentes=nComponentes,
             nombresPC=nombresPC, cargas=cargas, puntajes=puntajes, alfas=alfas)

    # Regresión logística con los criterios de Hosmer-Lemeshow
    cualitativas = ["Perecedero", "DatoEstimado", "Sudamerica"]
    cuantitativas = ["IndiceRendimiento", "DependenciaImportadora", "OrientacionExportadora", "logOferta", "logPrecio"]
    bivariado = []
    for v in cualitativas:
        chi2, p, gl, _ = stats.chi2_contingency(pd.crosstab(baseModelo[v], baseModelo["Critico"]))
        bivariado.append({"Variable": v, "Tipo": "Cualitativa", "Chi²": chi2, "p-valor": p})
    for v in cuantitativas:
        m = smf.logit(f"Critico ~ {v}", data=baseModelo).fit(disp=0)
        bivariado.append({"Variable": v, "Tipo": "Cuantitativa", "Chi²": m.llr, "p-valor": m.llr_pvalue})
    bivariado = pd.DataFrame(bivariado).sort_values("p-valor")
    bivariado["Pasa (p < 0,25)"] = np.where(bivariado["p-valor"] < 0.25, "Sí", "No")

    variablesModelo = bivariado.loc[bivariado["Pasa (p < 0,25)"] == "Sí", "Variable"].tolist()
    salidas = []
    while True:
        modeloLogit = smf.logit("Critico ~ " + " + ".join(variablesModelo), data=baseModelo).fit(disp=0)
        pvalores = modeloLogit.pvalues.drop("Intercept")
        if pvalores.max() < 0.05:
            break
        salidas.append((pvalores.idxmax(), pvalores.max()))
        variablesModelo.remove(pvalores.idxmax())
    intervalos = np.exp(modeloLogit.conf_int())
    tablaOR = pd.DataFrame({"Coeficiente": modeloLogit.params, "OR": np.exp(modeloLogit.params),
                            "IC 95% inf": intervalos[0], "IC 95% sup": intervalos[1],
                            "p-valor Wald": modeloLogit.pvalues})
    escenarios = pd.DataFrame([(a, c) for a in [0, 1] for c in [0, 1]], columns=["Perecedero", "DatoEstimado"])
    escenarios["Probabilidad"] = modeloLogit.predict(escenarios)

    # Random Forest y validación cruzada de 5 particiones
    candidatas = cualitativas + cuantitativas
    bosque = RandomForestClassifier(n_estimators=500, random_state=42).fit(baseModelo[candidatas], baseModelo["Critico"])
    importanciaRF = pd.Series(bosque.feature_importances_, index=candidatas).sort_values()
    validacion = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y = baseModelo["Critico"]
    modelos = {"Regresión logística": (LogisticRegression(max_iter=1000), baseModelo[variablesModelo]),
               "Random Forest": (RandomForestClassifier(n_estimators=500, random_state=42), baseModelo[candidatas])}
    metricas, curvasROC, matrices = [], {}, {}
    for nombre, (modelo, X) in modelos.items():
        prob = cross_val_predict(modelo, X, y, cv=validacion, method="predict_proba")[:, 1]
        pred = (prob >= 0.5).astype(int)
        vn, fp, fn, vp = confusion_matrix(y, pred).ravel()
        metricas.append({"Modelo": nombre, "Exactitud": accuracy_score(y, pred), "AUC": roc_auc_score(y, prob),
                         "Sensibilidad": vp / (vp + fn), "Especificidad": vn / (vn + fp)})
        curvasROC[nombre] = roc_curve(y, prob)[:2]
        matrices[nombre] = confusion_matrix(y, pred)
    r.update(bivariado=bivariado, salidas=salidas, variablesModelo=variablesModelo, tablaOR=tablaOR,
             escenarios=escenarios, importanciaRF=importanciaRF, metricas=pd.DataFrame(metricas),
             curvasROC=curvasROC, matrices=matrices)

    # K-means sobre los puntajes de las componentes
    inercias = [KMeans(n_clusters=k, n_init=50, random_state=42).fit(puntajes[nombresPC]).inertia_ for k in range(2, 9)]
    kmeans = KMeans(n_clusters=3, n_init=50, random_state=42).fit(puntajes[nombresPC])
    baseModelo["Grupo"] = kmeans.labels_
    perfilGrupos = baseModelo.groupby("Grupo").agg(
        Combinaciones=("Producto", "size"), TasaPerdida=("TasaPerdida", "median"),
        PerdidaMillUSD=("PerdidaUSD", lambda x: x.median() / 1e6),
        IndiceRendimiento=("IndiceRendimiento", "median"),
        DependenciaImportadora=("DependenciaImportadora", "median"),
        OrientacionExportadora=("OrientacionExportadora", "median"),
        PctPerecederos=("Perecedero", lambda x: x.mean() * 100),
        PctCriticos=("Critico", lambda x: x.mean() * 100))

    def nombrarGrupo(fila):
        if fila["TasaPerdida"] == perfilGrupos["TasaPerdida"].max(): return "Pérdida alta"
        if fila["OrientacionExportadora"] == perfilGrupos["OrientacionExportadora"].max(): return "Exportadores"
        return "Bajo volumen"
    perfilGrupos["Nombre"] = perfilGrupos.apply(nombrarGrupo, axis=1)
    baseModelo["NombreGrupo"] = baseModelo["Grupo"].map(perfilGrupos["Nombre"])
    r.update(inercias=pd.Series(inercias, index=range(2, 9)), perfilGrupos=perfilGrupos.set_index("Nombre"))

    # Asociación: Chi² de cada característica con la condición de crítico
    baseModelo["Tipo"] = np.where(baseModelo["Perecedero"] == 1, "Perecedero", "Grano")
    baseModelo["Region"] = np.where(baseModelo["Sudamerica"] == 1, "Sudamérica", "Centroamérica y Caribe")
    baseModelo["Rendimiento"] = pd.cut(baseModelo["IndiceRendimiento"], [-1, 90, 110, np.inf],
                                       labels=["Rend. bajo", "Rend. medio", "Rend. alto"]).astype(str)
    baseModelo["Comercio"] = np.select([baseModelo["DependenciaImportadora"] >= 30, baseModelo["OrientacionExportadora"] >= 20],
                                       ["Importador", "Exportador"], "Mercado interno")
    baseModelo["Condicion"] = np.where(baseModelo["Critico"] == 1, "Crítico", "No crítico")
    asociaciones = []
    for v in ["Tipo", "Calidad", "Region", "Rendimiento", "Comercio"]:
        chi2, p, gl, _ = stats.chi2_contingency(pd.crosstab(baseModelo[v], baseModelo["Condicion"]))
        asociaciones.append({"Variable": v, "Chi²": chi2, "gl": gl, "p-valor": p,
                             "¿Hay asociación? (p < 0,05)": "Sí" if p < 0.05 else "No"})
    asociaciones = pd.DataFrame(asociaciones).sort_values("p-valor")
    criticosCalidad = pd.crosstab(baseModelo["Calidad"], baseModelo["Condicion"], normalize="index")["Crítico"] * 100

    # MCA
    variablesMCA = ["Tipo", "Calidad", "Region", "Rendimiento", "Comercio", "Condicion"]
    autovaloresMCA, coordenadas = correspondenciasMultiples(baseModelo[variablesMCA])
    coordenadas = coordenadas * np.sign(coordenadas.loc["Condicion__Crítico"])
    inerciaMCA = autovaloresMCA[:2] / autovaloresMCA.sum() * 100
    r.update(asociaciones=asociaciones, criticosCalidad=criticosCalidad, coordenadasMCA=coordenadas, inerciaMCA=inerciaMCA)

    # Tendencias: por producto y regional (con y sin soya)
    evolucion = (basePerdidas.groupby(["Año", "Producto"])[["Perdida", "Oferta"]].sum()
                 .assign(TasaRegional=lambda d: d["Perdida"] / d["Oferta"] * 100).reset_index())
    tendenciaProducto = []
    for producto, g in evolucion.groupby("Producto"):
        lr = stats.linregress(g["Año"], g["TasaRegional"])
        error = g["TasaRegional"] - (lr.intercept + lr.slope * g["Año"])
        tendenciaProducto.append({"Producto": producto, "Pendiente (p.p./año)": lr.slope, "p-valor": lr.pvalue,
                                  "R²": lr.rvalue ** 2, "RMSE": np.sqrt((error ** 2).mean()), "MAE": error.abs().mean(),
                                  "Tasa 2010": g.loc[g["Año"] == 2010, "TasaRegional"].iloc[0],
                                  "Tasa 2023": g.loc[g["Año"] == 2023, "TasaRegional"].iloc[0]})
    tendenciaProducto = pd.DataFrame(tendenciaProducto).sort_values("Pendiente (p.p./año)", ascending=False)
    tendenciaProducto["Tendencia"] = np.where(tendenciaProducto["p-valor"] >= 0.05, "Sin tendencia",
                                              np.where(tendenciaProducto["Pendiente (p.p./año)"] > 0, "Creciente", "Decreciente"))
    serieTotal = tasaRegional(basePerdidas)
    serieSinSoya = tasaRegional(basePerdidas[basePerdidas["Producto"] != "Soya beans"])
    rTotal = stats.linregress(serieTotal.index, serieTotal.values)
    rSinSoya = stats.linregress(serieSinSoya.index, serieSinSoya.values)
    r.update(evolucion=evolucion, tendenciaProducto=tendenciaProducto, serieTotal=serieTotal,
             serieSinSoya=serieSinSoya, rTotal=rTotal, rSinSoya=rSinSoya,
             proyeccion2030=rSinSoya.intercept + rSinSoya.slope * 2030, meta2030=serieSinSoya.loc[2015] / 2)

    r["baseModelo"] = baseModelo
    return r
