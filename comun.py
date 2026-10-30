# ## FUNCIONES Y ESTILO COMUNES DEL DASHBOARD ##

import streamlit as st

import procesamiento as pr

# Identidad visual: agro moderno
bosque = "#1F4D3A"
bosqueClaro = "#2F6B52"
crema = "#F7F5EF"
carbon = "#23302A"
grisCalido = "#8A8F87"
coral = "#E4572E"
verde = "#1B9E77"
ambar = "#E0A526"
colorTipo = {"Perecedero": coral, "Grano": ambar}
colorGrupo = {"Pérdida alta": coral, "Exportadores": verde, "Bajo volumen": ambar}
escalaPerdida = [[0, "#FBF3E4"], [0.35, "#F2C38B"], [0.7, coral], [1, "#8E2A1B"]]
traduccionCalidad = {"Value imputed by a receiving agency": "Imputado", "Estimated value": "Estimado",
                     "Official value": "Oficial", "Value from external organization": "Organización externa"}
codigosISO = {
    "Argentina": "ARG", "Bolivia": "BOL", "Brasil": "BRA", "Chile": "CHL", "Colombia": "COL",
    "Costa Rica": "CRI", "Rep. Dominicana": "DOM", "Ecuador": "ECU", "El Salvador": "SLV",
    "Honduras": "HND", "México": "MEX", "Nicaragua": "NIC", "Panamá": "PAN", "Paraguay": "PRY",
    "Perú": "PER", "Uruguay": "URY", "Venezuela": "VEN",
}


@st.cache_resource(show_spinner="Cargando los datos de FAOSTAT…")
def cargarResultados():
    # Se calcula una sola vez y se reutiliza en todas las páginas
    exploratorio = pr.procesarExploratorio()
    modelado = pr.procesarModelado(exploratorio)
    return exploratorio, modelado


def estilosPagina():
    # Tipografía, colores y tarjetas
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    html, body, .stApp, p, h1, h2, h3, h4, label, li, td, th, input {{font-family:'Plus Jakarta Sans', sans-serif;}}
    .stApp {{background:{crema};color:{carbon};}}
    [data-testid="stMain"] p, [data-testid="stMain"] li, [data-testid="stMain"] h4,
    [data-testid="stMain"] [data-testid="stCaptionContainer"] {{color:{carbon};}}
    [data-testid="stTable"] table, [data-testid="stTable"] td, [data-testid="stTable"] th
        {{color:{carbon} !important;background:white !important;border-color:#ECE8DD !important;}}
    [data-testid="stTable"] th {{color:{grisCalido} !important;font-weight:600;}}
    [data-testid="stHeader"] {{background:transparent;}}
    [data-testid="stSidebar"] {{background:{bosque};}}
    [data-testid="stSidebar"] * {{color:#E8EFE9;}}
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] div[role="group"]:not(:has([data-baseweb="slider"])):not([data-testid="stSlider"] *)
        {{background:white !important;border-color:#d9d6cc !important;}}
    [data-testid="stSidebar"] [data-baseweb="select"] *, [data-testid="stSidebar"] input
        {{color:{carbon} !important;-webkit-text-fill-color:{carbon};}}
    [data-testid="stSidebar"] input::placeholder {{color:{grisCalido} !important;-webkit-text-fill-color:{grisCalido};}}
    [data-testid="stSidebar"] [data-baseweb="select"] svg {{fill:{carbon};}}
    [data-baseweb="popover"] ul, [data-baseweb="popover"] li {{background:white !important;color:{carbon} !important;}}
    [data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"] {{background:{ambar} !important;box-shadow:none;}}
    [data-testid="stSidebar"] [data-testid="stSlider"] [data-baseweb="slider"] > div > div {{background:{ambar} !important;}}
    [data-testid="stDownloadButton"] button {{background:white;color:{carbon};border-color:#d9d6cc;}}
    [data-testid="stExpander"] details {{background:white;}}
    [data-testid="stSidebar"] [data-baseweb="tag"] {{background:{ambar};}}
    [data-testid="stSidebar"] [data-baseweb="tag"] * {{color:{carbon};}}
    [data-testid="stSidebarNav"] a {{border-radius:8px;}}
    [data-testid="stSidebarNav"] a[aria-current="page"] {{background:rgba(255,255,255,.12);}}
    [data-testid="stSidebarNav"] a[aria-current="page"] span {{color:white;font-weight:700;}}
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] > [data-testid="stMarkdown"] .tituloCaja)
        {{background:white;border:none !important;border-radius:14px;box-shadow:0 1px 3px rgba(31,77,58,.08),
          0 6px 18px rgba(31,77,58,.06);}}
    .tituloCaja {{font-weight:700;font-size:1.05rem;color:{carbon};margin-bottom:-6px;}}
    .subtituloCaja {{font-size:.86rem;color:{grisCalido};font-weight:400;margin-top:2px;}}
    .portada {{background:linear-gradient(120deg,{bosque} 0%,{bosqueClaro} 100%);color:white;border-radius:16px;
               padding:26px 30px;margin-bottom:18px;}}
    .portada .etiqueta {{text-transform:uppercase;letter-spacing:.12em;font-size:.78rem;color:{ambar};font-weight:700;}}
    .portada h1 {{color:white;font-size:2.1rem;font-weight:800;line-height:1.2;margin:6px 0 6px 0;padding:0;}}
    .portada p {{color:#D8E6DD;font-size:1rem;margin:0;}}
    .encabezado {{margin:4px 0 16px 0;}}
    .encabezado .etiqueta {{text-transform:uppercase;letter-spacing:.12em;font-size:.76rem;color:{bosqueClaro};font-weight:700;}}
    .encabezado h2 {{color:{carbon};font-size:1.75rem;font-weight:800;margin:2px 0 0 0;padding:0;}}
    .encabezado p {{color:{grisCalido};margin:2px 0 0 0;font-size:.95rem;}}
    .cifra {{background:white;border-radius:14px;padding:16px 18px;box-shadow:0 1px 3px rgba(31,77,58,.08),
             0 6px 18px rgba(31,77,58,.06);border-top:4px solid var(--acento);min-height:132px;margin-bottom:14px;}}
    .cifra .nombre {{text-transform:uppercase;letter-spacing:.08em;font-size:.72rem;color:{grisCalido};font-weight:700;}}
    .cifra .valor {{font-size:1.85rem;font-weight:800;color:{carbon};line-height:1.15;margin-top:6px;}}
    .cifra .detalle {{font-size:.82rem;color:{grisCalido};margin-top:2px;}}
    .segmento {{background:white;border-radius:14px;padding:16px 18px;border-left:6px solid var(--acento);
                box-shadow:0 1px 3px rgba(31,77,58,.08),0 6px 18px rgba(31,77,58,.06);min-height:168px;margin-bottom:14px;}}
    .segmento .titulo {{font-weight:800;font-size:1.1rem;color:{carbon};}}
    .segmento .rol {{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:var(--acento);font-weight:700;}}
    .segmento .datos {{font-size:.92rem;color:#4b5550;margin-top:8px;line-height:1.55;}}
    </style>""", unsafe_allow_html=True)


def filtrosLaterales(exploratorio):
    # Filtros: país, producto, tipo y años
    basePerdidas = pr.traducir(exploratorio["basePerdidas"])
    st.sidebar.markdown("#### Filtros")
    st.sidebar.multiselect("País", sorted(basePerdidas["Pais"].unique()), key="fPaises", placeholder="Todos")
    st.sidebar.multiselect("Producto", sorted(basePerdidas["Producto"].unique()), key="fProductos", placeholder="Todos")
    st.sidebar.multiselect("Tipo de producto", ["Perecedero", "Grano"], key="fTipos", placeholder="Todos")
    st.sidebar.slider("Años", 2010, 2023, (2010, 2023), key="fAnios")


def basesFiltradas():
    # Base de pérdidas y base maestra con los filtros de la barra lateral
    exploratorio, _ = cargarResultados()
    basePerdidas = pr.traducir(exploratorio["basePerdidas"])
    baseMaestra = pr.traducir(exploratorio["baseMaestra"])
    perecederosEs = [pr.productosEspanol[p] for p in pr.perecederos]
    for base in (basePerdidas, baseMaestra):
        base["Tipo"] = base["Producto"].isin(perecederosEs).map({True: "Perecedero", False: "Grano"})
    basePerdidas["Calidad"] = basePerdidas["Calidad"].map(traduccionCalidad).fillna("Otro")

    estado = st.session_state
    anios = estado.get("fAnios", (2010, 2023))

    def aplicar(df):
        filtro = df["Año"].between(*anios)
        if estado.get("fPaises"): filtro &= df["Pais"].isin(estado["fPaises"])
        if estado.get("fProductos"): filtro &= df["Producto"].isin(estado["fProductos"])
        if estado.get("fTipos"): filtro &= df["Tipo"].isin(estado["fTipos"])
        return df[filtro]

    return aplicar(basePerdidas), aplicar(baseMaestra)


def textoFiltros():
    # Filtros activos en una línea
    estado = st.session_state
    anios = estado.get("fAnios", (2010, 2023))
    partes = [f"{anios[0]}–{anios[1]}"]
    for clave in ["fPaises", "fProductos", "fTipos"]:
        if estado.get(clave):
            partes.append(", ".join(estado[clave]) if len(estado[clave]) <= 3 else f"{len(estado[clave])} seleccionados")
    return " · ".join(partes)


def encabezado(etiqueta, titulo, detalle=""):
    # Encabezado de cada sección
    st.markdown(f"<div class='encabezado'><div class='etiqueta'>{etiqueta}</div><h2>{titulo}</h2>"
                f"<p>{detalle}</p></div>", unsafe_allow_html=True)


def cifras(lista, columnas=4):
    # Tarjetas de cifras: (nombre, valor, detalle, color de acento)
    cols = st.columns(columnas)
    for i, (nombre, valor, detalle, acento) in enumerate(lista):
        cols[i % columnas].markdown(
            f"<div class='cifra' style='--acento:{acento}'><div class='nombre'>{nombre}</div>"
            f"<div class='valor'>{valor}</div><div class='detalle'>{detalle}</div></div>", unsafe_allow_html=True)


def caja(titulo, subtitulo=""):
    # Tarjeta blanca con título para cada gráfica
    contenedor = st.container(border=True)
    contenedor.markdown(f"<div class='tituloCaja'>{titulo}<div class='subtituloCaja'>{subtitulo}</div></div>",
                        unsafe_allow_html=True)
    return contenedor


def numero(valor, decimales=1):
    # Formato con coma decimal y punto de miles
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def pvalor(p):
    # p-valor como en el informe
    return "< 0,001" if p < 0.001 else numero(p, 3)


def estiloGrafico(fig, alto=400):
    # Estilo común de las gráficas
    fig.update_layout(
        height=alto, template="plotly_white", separators=",.", paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Plus Jakarta Sans, sans-serif", size=13, color=carbon),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, title_text=""),
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="Plus Jakarta Sans, sans-serif"),
    )
    margenActual = fig.layout.margin
    fig.update_layout(margin={lado: getattr(margenActual, lado) if getattr(margenActual, lado) is not None else valor
                              for lado, valor in dict(l=10, r=10, t=30, b=10).items()})
    fig.update_xaxes(showgrid=False, linecolor="#d9d6cc", tickfont=dict(color=grisCalido))
    fig.update_yaxes(gridcolor="#efece4", zeroline=False, tickfont=dict(color=grisCalido))
    return fig


def sinDatos(df):
    # Detiene la página si los filtros dejan la base vacía
    if df.empty:
        st.warning("No hay datos con los filtros seleccionados.")
        st.stop()
