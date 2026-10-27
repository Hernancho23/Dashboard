# Dashboard: Detección de puntos críticos de pérdida de alimentos

Proyecto 7 · Minería de Datos · ITM — Jimena Cardona, Hernán Céspedes y Valentina Ramírez.

## Estructura

```
app.py                  menú, filtros consultables y estilo
procesamiento.py        mismo código del notebook (unión, KPIs, PCA, logística, K-means, Chi², MCA, tendencias)
comun.py                colores, tarjetas, cajas y funciones de formato
paginas/                una página por sección del menú
datos/                  los 4 CSV limpios de Power Query
requirements.txt        librerías
```

## Correrlo en el computador

```
pip install -r requirements.txt
streamlit run app.py
```

## Publicarlo en internet (Streamlit Community Cloud, gratis)

1. Crear un repositorio en GitHub y subir **todo** el contenido de esta carpeta (incluida `datos/` y `.streamlit/`).
2. Entrar a https://share.streamlit.io con la cuenta de GitHub.
3. **Create app** → elegir el repositorio, la rama `main` y el archivo `app.py` → **Deploy**.
4. Queda un enlace del tipo `https://<nombre>.streamlit.app` para compartir con el profe.

Cada vez que se suba un cambio al repositorio, la app se actualiza sola.
