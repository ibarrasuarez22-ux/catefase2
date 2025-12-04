import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import os

# ==========================================
# 1. CONFIGURACIÓN VISUAL EJECUTIVA
# ==========================================
st.set_page_config(layout="wide", page_title="SITS Estrategia", page_icon="🗳️")

st.markdown("""
<style>
    /* Estilos para Tablas y Leyendas */
    .legend-table {
        font-size: 14px; width: 100%; border-collapse: collapse; border: 1px solid #ddd;
    }
    .legend-table td { padding: 10px; border-bottom: 1px solid #eee; vertical-align: middle; }
    .legend-table th { background-color: #f8f9fa; padding: 10px; text-align: left; }
    
    /* Cajas de KPI (Números Grandes) */
    .kpi-container {
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #e0e0e0;
        text-align: center;
        margin-top: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .kpi-title { font-size: 16px; color: #555; text-transform: uppercase; font-weight: 600; }
    .kpi-value { font-size: 32px; font-weight: 800; color: #2c3e50; margin: 5px 0; }
    .kpi-note { font-size: 13px; color: #888; font-style: italic; }

    /* Cajas de Texto Explicativo */
    .guide-box {
        background-color: #e3f2fd; border-left: 6px solid #2196f3;
        padding: 15px; border-radius: 5px; font-size: 15px; line-height: 1.6;
        margin-bottom: 20px;
    }
    .action-box {
        background-color: #fbe9e7; border-left: 6px solid #ff5722;
        padding: 15px; border-radius: 5px; font-size: 15px; line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

st.title("🗳️ SITS: Tablero de Comando Electoral 2025")
st.markdown("**Herramienta de Decisión Estratégica:** Cruce de Necesidad Social (Fase 1) vs. Rentabilidad Política (Fase 2).")

# ==========================================
# 2. CARGA DE DATOS
# ==========================================
@st.cache_data
def cargar():
    fu, fr = "sits_urbano_fase2.geojson", "sits_rural_fase2.geojson"
    if not os.path.exists(fu): return None, None
    u, r = gpd.read_file(fu), gpd.read_file(fr)
    u['TIPO'], r['TIPO'] = 'Urbano', 'Rural'
    u['LUGAR'] = u['NOM_LOC'] + " - AGEB " + u['CVE_AGEB']
    r['LUGAR'] = r['NOM_LOC']
    return u, r

u, r = cargar()
if u is None: st.stop()

# ==========================================
# 3. BARRA LATERAL (FILTROS CLAROS)
# ==========================================
with st.sidebar:
    st.header("🎛️ Filtros de Inteligencia")
    st.info("Use estos controles para definir QUÉ buscar y DÓNDE buscar.")
    
    # 1. ESTRATEGIA
    st.markdown("### 1. Situación Política")
    estrat = sorted(list(set(u['ACCION_TACTICA'].unique()) | set(r['ACCION_TACTICA'].unique())))
    # Default: Las más importantes
    default_est = [e for e in estrat if "GUERRA" in e or "BLINDAJE" in e]
    sel_est = st.multiselect("Seleccione Estrategias:", estrat, default=default_est)
    
    st.divider()
    
    # 2. FOCO SOCIAL (TRADUCTOR)
    st.markdown("### 2. Causa Social (Bandera)")
    opciones_sociales = {
        "🔥 Pobreza General (SITS)": "SITS_INDEX",
        "👩‍👧 Jefas de Familia": "IND_JEFAS",
        "🍲 Alimentación / Despensas": "CAR_ALIM",
        "🚰 Servicios (Agua/Luz)": "CAR_SERV",
        "🏠 Vivienda (Piso/Techo)": "CAR_VIV",
        "🏥 Salud / Medicinas": "CAR_SALUD",
        "🎓 Educación / Becas": "CAR_EDU",
        "💬 Población Indígena": "POB_INDIGENA",
        "♿ Personas con Discapacidad": "POB_DISC"
    }
    label_social = st.selectbox("¿Qué necesidad vamos a atender?", list(opciones_sociales.keys()))
    foco_social = opciones_sociales[label_social]
    
    # APLICAR FILTROS
    u_f = u[u['ACCION_TACTICA'].isin(sel_est)]
    r_f = r[r['ACCION_TACTICA'].isin(sel_est)]

# ==========================================
# 4. INTERFAZ
# ==========================================
tab1, tab2, tab3 = st.tabs(["🗺️ MAPA DE CRUCE", "📈 MATRIZ DE DECISIÓN", "📋 LISTADO DE ACCIÓN"])

# --- TAB 1: MAPA Y POTENCIAL ---
with tab1:
    col_mapa, col_leyenda = st.columns([3, 1.2])
    
    with col_mapa:
        # Mapa
        if not u_f.empty: clat, clon = u_f.geometry.centroid.y.mean(), u_f.geometry.centroid.x.mean()
        else: clat, clon = 18.42, -95.11
        m = folium.Map([clat, clon], zoom_start=13, tiles="CartoDB positron")
        
        color_map = {
            "1. GUERRA SOCIAL (Empate + Pobreza Alta)": "#d63031",
            "2. BLINDAJE (Ganada + Pobreza Alta)": "#009432",
            "3. OPORTUNIDAD (Perdida + Pobreza Extrema)": "#f79f1f",
            "4. GUERRA ELECTORAL (Empate + Clase Media)": "#ff7675",
            "5. MANTENIMIENTO (Ganada + Clase Media)": "#badc58",
            "6. ZONA PERDIDA": "#b2bec3"
        }
        def gc(v): return color_map.get(v, "blue")

        # Tooltip fácil
        val_tooltip = f"{foco_social}"
        
        if not u_f.empty:
            folium.GeoJson(u_f, style_function=lambda x: {'fillColor': gc(x['properties']['ACCION_TACTICA']), 'color':'black', 'weight':0.5, 'fillOpacity':0.8},
                           tooltip=folium.GeoJsonTooltip(fields=['LUGAR', 'ACCION_TACTICA', 'MARGEN_ABS'], aliases=['Zona:', 'Estrategia:', 'Margen Votos:'])).add_to(m)
        if not r_f.empty:
            for _, row in r_f.iterrows():
                folium.CircleMarker([row.geometry.centroid.y, row.geometry.centroid.x], radius=9, color='black', weight=1, fill=True,
                                    fill_color=gc(row['ACCION_TACTICA']), fill_opacity=0.9,
                                    popup=f"{row['LUGAR']}<br>{row['ACCION_TACTICA']}").add_to(m)
        st_folium(m, height=500, use_container_width=True)

    with col_leyenda:
        st.markdown("### 🚦 Semáforo de Acción")
        st.markdown("""
        <table class="legend-table">
            <tr>
                <td width="10%"><span style="color:#d63031; font-size:25px;">■</span></td>
                <td><b>ROJO (GUERRA):</b><br>Empate técnico + Pobreza.<br><i>Acción: Volcar recursos aquí.</i></td>
            </tr>
            <tr>
                <td><span style="color:#009432; font-size:25px;">■</span></td>
                <td><b>VERDE (BLINDAJE):</b><br>Ganada + Pobreza.<br><i>Acción: Fidelizar voto duro.</i></td>
            </tr>
            <tr>
                <td><span style="color:#f79f1f; font-size:25px;">■</span></td>
                <td><b>NARANJA (OPORTUNIDAD):</b><br>Perdida + Pobreza.<br><i>Acción: Entrar por necesidad.</i></td>
            </tr>
            <tr>
                <td><span style="color:#b2bec3; font-size:25px;">■</span></td>
                <td><b>GRIS (AIRE):</b><br>Clase Media o Perdida.<br><i>Acción: Campaña de imagen.</i></td>
            </tr>
        </table>
        """, unsafe_allow_html=True)

    # --- SECCIÓN DE POTENCIAL (ABAJO) ---
    st.markdown("### 📊 Potencial del Cruce (Resumen)")
    
    df_all = pd.concat([u_f, r_f])
    if not df_all.empty:
        # Cálculo de Capital Social
        es_indice = any(x in foco_social for x in ["INDEX", "IND", "CAR_"])
        if es_indice:
            base = df_all['TOTAL_HOGARES_25'] if "JEFAS" in foco_social else df_all['POBTOT_25']
            social_capital = (df_all[foco_social] * base).sum()
            txt_cap = f"Hogares/Personas con {label_social}"
        else:
            col_abs = foco_social + "_25"
            social_capital = df_all[col_abs].sum() if col_abs in df_all.columns else 0
            txt_cap = f"Total {label_social}"

        pob_tot = df_all['POBTOT_25'].sum()
        voto_duro = (df_all['POBTOT_25'] * 0.6 * df_all['PCT_MC_25']).sum() # Est. LN * %MC

        # Cajas KPI anchas y claras
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"""<div class="kpi-container"><div class="kpi-title">Población Total en Zona</div><div class="kpi-value">{int(pob_tot):,}</div><div class="kpi-note">Habitantes en las zonas filtradas</div></div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""<div class="kpi-container" style="border-top: 5px solid #2196f3;"><div class="kpi-title">OBJETIVO SOCIAL</div><div class="kpi-value" style="color:#2196f3">{int(social_capital):,}</div><div class="kpi-note">{txt_cap}</div></div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""<div class="kpi-container" style="border-top: 5px solid #ff9800;"><div class="kpi-title">CAPITAL POLÍTICO</div><div class="kpi-value" style="color:#ff9800">{int(voto_duro):,}</div><div class="kpi-note">Votos MC Estimados (Piso)</div></div>""", unsafe_allow_html=True)

# --- TAB 2: MATRIZ EXPLICADA ---
with tab2:
    st.subheader("📈 Matriz de Dispersión Estratégica")
    
    # Caja de Explicación Dinámica
    st.markdown(f"""
    <div class="guide-box">
        <h4>🤔 ¿Qué estoy viendo en esta gráfica?</h4>
        <p>Cada círculo es una Colonia o Comunidad. Su posición nos dice qué hacer:</p>
        <ul>
            <li><b>Eje Vertical (Arriba/Abajo):</b> Nivel de <b>{label_social}</b>. <br>Los círculos de <b>arriba</b> tienen mayor necesidad de este apoyo.</li>
            <li><b>Eje Horizontal (Izquierda/Derecha):</b> Riesgo Electoral.<br>Los círculos a la <b>izquierda</b> (cerca del 0) son empates técnicos.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if not df_all.empty:
        fig = px.scatter(df_all, x="MARGEN_ABS", y=foco_social,
                         color="ACCION_TACTICA", size="POBTOT_25", hover_name="LUGAR",
                         color_discrete_map=color_map,
                         labels={"MARGEN_ABS": "Margen Electoral (0 = Empate)", foco_social: f"Nivel: {label_social}"},
                         height=500)
        
        fig.add_vline(x=0.05, line_dash="dash", annotation_text="Peligro < 5%")
        st.plotly_chart(fig, use_container_width=True)
        
        # Caja de Acción
        st.markdown(f"""
        <div class="action-box">
            <h4>💡 Ideas de Acción para {label_social}:</h4>
            <ul>
                <li><b>Si ve puntos Rojos altos:</b> Envíe brigadas de {label_social} inmediatamente. Son zonas de empate donde este apoyo decide la elección.</li>
                <li><b>Si ve puntos Verdes altos:</b> Organice eventos de agradecimiento o refuerzo. Ya votan por nosotros, hay que fidelizarlos con el apoyo.</li>
                <li><b>Si ve puntos Naranjas altos:</b> Evalúe si el costo del programa vale la pena para intentar convencer a una zona opositora.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 3: LISTADO Y DESCARGA ---
with tab3:
    st.subheader("📋 Padrón de Operación Cruzado")
    
    st.markdown(f"""
    **Instrucciones de Uso:**
    Esta tabla es el resultado final del análisis. Muestra las zonas filtradas ordenadas por **Prioridad Política** (primero las Guerras) y luego por **Volumen de Necesidad** ({label_social}).
    
    1. Utilice los filtros de la izquierda para definir el criterio (Ej. "Jefas de Familia" en "Zonas de Guerra").
    2. La tabla abajo se actualizará automáticamente.
    3. Descargue el Excel y entréguelo al Coordinador de Zona.
    """)
    
    if not df_all.empty:
        col_sort = foco_social
        # Ordenar: 1. Prioridad Táctica, 2. Cantidad de Necesidad Social
        df_view = df_all.sort_values(['PRIORIDAD_NUM', col_sort], ascending=[True, False])
        
        cols_ver = ['LUGAR', 'SECCION', 'ACCION_TACTICA', 'MARGEN_ABS', 'PCT_MC_25', foco_social]
        
        # Formateo de columnas para la vista
        fmt_config = {
            "MARGEN_ABS": st.column_config.NumberColumn("Margen Victoria", format="%.2f%%"),
            "PCT_MC_25": st.column_config.NumberColumn("Fuerza MC", format="%.1f%%"),
            foco_social: st.column_config.ProgressColumn(label_social, format="%.2f", min_value=0, max_value=1) if es_indice else st.column_config.NumberColumn(label_social, format="%d")
        }

        st.dataframe(df_view[cols_ver], hide_index=True, use_container_width=True, column_config=fmt_config)
        
        csv = df_view[cols_ver].to_csv(index=False).encode('utf-8')
        st.download_button(f"📥 Descargar Plan Maestro ({label_social})", csv, f"Estrategia_{label_social}.csv", "text/csv")
