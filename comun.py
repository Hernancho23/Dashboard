# ## FUNCIONES Y ESTILO COMUNES DEL DASHBOARD ##

import streamlit as st
import plotly.graph_objects as go

import procesamiento as pr

# Colores del proyecto (los mismos de las diapositivas)
verdeOscuro = "#1F4E3D"
naranja = "#C8501E"
rojo = "#c0392b"
amarillo = "#D9A441"
azul = "#1f78b4"
gris = "#7f8c8d"
colorTipo = {"Perecedero": rojo, "Grano": amarillo}
colorGrupo = {"Pérdida alta": rojo, "Exportadores": azul, "Bajo volumen": amarillo}
traduccionCalidad = {"Value imputed by a receiving agency": "Imputado", "Estimated value": "Estimado",
                     "Official value": "Oficial", "Value from external organization": "Organización externa"}


@st.cache_resource(show_spinner="Procesando las bases de FAOSTAT…")
def cargarResultados():
    # Se calcula una sola vez y se reutiliza en todas las páginas
    exploratorio = pr.procesarExploratorio()
    modelado = pr.procesarModelado(exploratorio)
    return exploratorio, modelado


def estilosPagina():
    # Estilo general: barra lateral oscura y cajas con encabezado (como el ejemplo del profe)
    st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{background:{verdeOscuro};}}
    [data-testid="stSidebar"] * {{color:#F3EEE2;}}
    [data-testid="stSidebar"] [data-baseweb="select"] *, [data-testid="stSidebar"] input {{color:#262730;}}
    [data-testid="stSidebar"] [data-baseweb="tag"] {{background:{naranja};}}
    [data-testid="stSidebar"] [data-baseweb="tag"] * {{color:white;}}
    [data-testid="stSidebarNav"] a[aria-current="page"] {{background:rgba(255,255,255,.14);}}
    .encabezadoCaja {{background:{verdeOscuro};color:white;padding:7px 14px;border-radius:6px 6px 0 0;
                      margin:-1rem -1rem .6rem -1rem;font-weight:600;}}
    .tarjeta {{border-radius:8px;padding:14px 16px;color:white;position:relative;overflow:hidden;height:104px;
               margin-bottom:12px;}}
    .tarjeta .valor {{font-size:1.75rem;font-weight:700;line-height:1.1;}}
    .tarjeta .etiqueta {{font-size:.92rem;opacity:.95;margin-top:4px;}}
    .tarjeta .icono {{position:absolute;right:12px;top:10px;font-size:2.6rem;opacity:.28;}}
    </style>""", unsafe_allow_html=True)


def filtrosLaterales(exploratorio):
    # Filtros consultables: países, productos, tipo, calidad del dato y años
    basePerdidas = pr.traducir(exploratorio["basePerdidas"])
    st.sidebar.markdown("### Filtros consultables")
    st.sidebar.multiselect("País", sorted(basePerdidas["Pais"].unique()), key="fPaises", placeholder="Todos")
    st.sidebar.multiselect("Producto", sorted(basePerdidas["Producto"].unique()), key="fProductos", placeholder="Todos")
    st.sidebar.multiselect("Tipo de producto", ["Perecedero", "Grano"], key="fTipos", placeholder="Todos")
    st.sidebar.multiselect("Calidad del dato de pérdida", ["Imputado", "Estimado", "Oficial", "Organización externa"],
                           key="fCalidad", placeholder="Todas")
    st.sidebar.slider("Años", 2010, 2023, (2010, 2023), key="fAnios")


def basesFiltradas():
    # Devuelve la base de pérdidas y la base maestra con los filtros de la barra lateral
    exploratorio, _ = cargarResultados()
    basePerdidas = pr.traducir(exploratorio["basePerdidas"])
    baseMaestra = pr.traducir(exploratorio["baseMaestra"])
    perecederosEs = [pr.productosEspanol[p] for p in pr.perecederos]
    for base in (basePerdidas, baseMaestra):
        base["Tipo"] = base["Producto"].isin(perecederosEs).map({True: "Perecedero", False: "Grano"})
    basePerdidas["Calidad"] = basePerdidas["Calidad"].map(traduccionCalidad).fillna("Otro")
    baseMaestra = baseMaestra.merge(basePerdidas[["Pais", "Producto", "Año", "Calidad"]],
                                    on=["Pais", "Producto", "Año"], how="left")

    estado = st.session_state
    anios = estado.get("fAnios", (2010, 2023))

    def aplicar(df):
        filtro = df["Año"].between(*anios)
        if estado.get("fPaises"): filtro &= df["Pais"].isin(estado["fPaises"])
        if estado.get("fProductos"): filtro &= df["Producto"].isin(estado["fProductos"])
        if estado.get("fTipos"): filtro &= df["Tipo"].isin(estado["fTipos"])
        if estado.get("fCalidad"): filtro &= df["Calidad"].isin(estado["fCalidad"])
        return df[filtro]

    return aplicar(basePerdidas), aplicar(baseMaestra)


def resumenFiltros():
    # Texto corto con los filtros activos
    estado = st.session_state
    partes = [f"{estado.get('fAnios', (2010, 2023))[0]}–{estado.get('fAnios', (2010, 2023))[1]}"]
    for clave, nombre in [("fPaises", "países"), ("fProductos", "productos"), ("fTipos", "tipos"), ("fCalidad", "calidades")]:
        if estado.get(clave):
            partes.append(f"{len(estado[clave])} {nombre}")
    return "Filtros: " + " · ".join(partes)


def numero(valor, decimales=1):
    # Formato con coma decimal y punto de miles (estilo Colombia)
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def pvalor(p):
    # Muestra el p-valor como en el informe
    return "< 0,001" if p < 0.001 else numero(p, 3)


def tarjetas(lista, columnas=4):
    # Fila de tarjetas de colores: (valor, etiqueta, color, icono)
    cols = st.columns(columnas)
    for i, (valor, etiqueta, color, icono) in enumerate(lista):
        cols[i % columnas].markdown(
            f"<div class='tarjeta' style='background:{color}'><div class='icono'>{icono}</div>"
            f"<div class='valor'>{valor}</div><div class='etiqueta'>{etiqueta}</div></div>",
            unsafe_allow_html=True)


def caja(titulo):
    # Caja con encabezado de color para cada gráfica
    contenedor = st.container(border=True)
    contenedor.markdown(f"<div class='encabezadoCaja'>{titulo}</div>", unsafe_allow_html=True)
    return contenedor


def estiloGrafico(fig, alto=420):
    # Estilo común de las gráficas: fondo blanco, ejes suaves y coma decimal
    fig.update_layout(
        height=alto, template="plotly_white", separators=",.",
        font=dict(family="Source Sans Pro, sans-serif", size=13, color="#262730"),
        title_font=dict(size=15, color=verdeOscuro),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, title_text=""),
        hoverlabel=dict(bgcolor="white", font_size=13),
    )
    # Márgenes por defecto, sin borrar los que la gráfica ya definió
    margenActual = fig.layout.margin
    fig.update_layout(margin={lado: getattr(margenActual, lado) if getattr(margenActual, lado) is not None else valor
                              for lado, valor in dict(l=10, r=10, t=50, b=10).items()})
    fig.update_xaxes(showgrid=False, linecolor="#d0d0d0")
    fig.update_yaxes(gridcolor="#ececec", zeroline=False)
    return fig


def nota(texto):
    # Recuadro de lectura del resultado (como el markdown de cada celda del notebook)
    st.markdown(
        f"<div style='background:#F3EEE2;border-left:4px solid {naranja};padding:10px 14px;"
        f"border-radius:6px;margin:4px 0 14px 0'>{texto}</div>",
        unsafe_allow_html=True,
    )


def verTabla(df, titulo="Ver los datos de esta gráfica"):
    # Tabla desplegable debajo de cada gráfica
    with st.expander(titulo):
        st.dataframe(df, width="stretch", hide_index=True)


def lineaReferencia(fig, valor, texto, color=gris):
    # Línea horizontal punteada con su etiqueta
    fig.add_hline(y=valor, line_dash="dot", line_color=color, line_width=1.5,
                  annotation_text=texto, annotation_position="top left",
                  annotation_font_color=color)
    return fig


def sinDatos(df):
    # Detiene la página si los filtros dejan la base vacía
    if df.empty:
        st.warning("No hay datos con los filtros seleccionados. Cambia los filtros de la barra lateral.")
        st.stop()
