"""
===============================================================================
SISTEMA DE CONTROL DE AVANCE DE INSPECCIONES - INSTRUMENTACIÓN
Contrato N° 3700002135 | Refinería La Pampilla (Repsol Perú)
Desarrollado para: ADEMINSAC PERÚ
===============================================================================
Tecnologías: Streamlit, Plotly, Pandas, OpenPyXL
Ejecución local: streamlit run app_control_inspecciones.py
"""

import datetime
import io
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CORPORATIVOS SOBRIOS
# =============================================================================
st.set_page_config(
    page_title="ADEMINSAC | Control de Inspecciones - Repsol",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta de Colores Corporativos (Repsol / ADEMINSAC)
COLOR_PRIMARY = "#002B49"       # Azul Marino Industrial
COLOR_SECONDARY = "#E87722"     # Naranja Repsol
COLOR_SUCCESS = "#2E7D32"       # Verde Cumplimiento
COLOR_DANGER = "#C62828"        # Rojo Alerta / Incumplimiento
COLOR_WARNING = "#F57F17"       # Amarillo Warning / Moderado
COLOR_BG_CARD = "#F8F9FA"       # Gris Claro Fondo Tarjetas
COLOR_TEXT_MUTED = "#5A626A"     # Gris Texto Secundario

st.markdown(f"""
    <style>
    .main {{
        background-color: #F4F6F9;
    }}
    .metric-card {{
        background-color: white;
        padding: 18px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 5px solid {COLOR_PRIMARY};
        margin-bottom: 15px;
    }}
    .metric-title {{
        font-size: 0.85rem;
        color: {COLOR_TEXT_MUTED};
        font-weight: 600;
        text-transform: uppercase;
    }}
    .metric-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {COLOR_PRIMARY};
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #E9ECEF;
        border-radius: 6px 6px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
    }}
    </style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. INICIALIZACIÓN DE DATOS EN SESIÓN (PERSISTENCIA DINÁMICA / EDITABLE)
# =============================================================================
def cargar_datos_iniciales():
    """Genera dataset de simulación realista para el Contrato 3700002135"""
    
    # --- Data OPS & SST ---
    meses_2025_2026 = pd.date_range(start='2025-01-01', periods=18, freq='MS').strftime('%Y-%m').tolist()
    
    df_ops = pd.DataFrame({
        'Mes': np.random.choice(meses_2025_2026[:12], 35),
        'Departamento': np.random.choice(['Unidad Conversión', 'Destilación / Topping', 'Servicios Auxiliares', 'Tanques y Offsites', 'Terminales Marítimos'], 35),
        'Gravedad': np.random.choice(['Leve', 'Moderada', 'Grave'], 35, p=[0.6, 0.3, 0.1]),
        'Tipo': np.random.choice(['Impuesta', 'Generada'], 35, p=[0.4, 0.6]),
        'Descripción': 'Observación de Seguridad en Inspección de Equipos de Campo'
    })
    
    df_sst = pd.DataFrame({
        'Mes': meses_2025_2026,
        'Planificado_%': [100]*18,
        'Ejecutado_%': [100, 98, 95, 100, 100, 92, 100, 96, 100, 100, 95, 98] + [None]*6, # Proyección a futuro
        'Tipo_Actividad': np.random.choice(['Capacitación SST', 'Inspección Planeada', 'Auditoría Interna', 'Mantenimiento EPP'], 18)
    })

    # --- Data Eventos de Seguridad ---
    df_eventos = pd.DataFrame([
        {'Fecha': '2025-02-14', 'Año': 2025, 'Unidad': 'Topping 1', 'Evento': 'Fuga menor en brida de transmisor de presión', 'Clasificación': 'Incidente Ambiental / Menor', 'Acción_Correctiva': 'Reajuste de pernos y torqueado con protocolo QA/QC', 'Estado': 'Cerrado'},
        {'Fecha': '2025-06-20', 'Año': 2025, 'Unidad': 'FCC (Craqueo Catalítico)', 'Evento': 'Desconexión intempestiva de lazo de control de temperatura', 'Clasificación': 'Falla Operacional', 'Acción_Correctiva': 'Reemplazo de tarjeta I/O y calibración de campo', 'Estado': 'Cerrado'},
        {'Fecha': '2025-10-11', 'Año': 2025, 'Unidad': 'Hydrotreating (HDT)', 'Evento': 'Contacto eléctrico de bajo voltaje en gabinete local', 'Clasificación': 'Cuasi Accidente (Near Miss)', 'Acción_Correctiva': 'Aislamiento térmico y señalización IP65', 'Estado': 'Cerrado'},
        {'Fecha': '2026-01-18', 'Año': 2026, 'Unidad': 'Servicios Auxiliares', 'Evento': 'Deterioro de cableado de señal en válvula de alivio PSV', 'Clasificación': 'Condición Subestándar', 'Acción_Correctiva': 'Canalización con tubería conduit flexible de acero inox', 'Estado': 'En Proceso'},
        {'Fecha': '2026-03-05', 'Año': 2026, 'Unidad': 'Terminal Marítimo 2', 'Evento': 'Corrosión severa en soporte de transmisor de nivel radar', 'Clasificación': 'Condición Subestándar', 'Acción_Correctiva': 'Cambio de soporte a AISI 316L', 'Estado': 'Abierto'}
    ])

    # --- Data Planes de Inspección Instrumentación ---
    unidades = ['Topping 1', 'Topping 2', 'Vacuum 1', 'FCC', 'HDT', 'Plantas Ácidas', 'Terminales']
    tipos_plan = ['Calibración Transmisores (PT/FT/TT)', 'Prueba Funcional Válvulas Control', 'Inspección Sistemas ESD/SIS', 'Mantenimiento Detectores Gas & Fuego']
    
    rows_inspeccion = []
    for mes in meses_2025_2026[:14]:
        for und in unidades:
            prog = np.random.randint(10, 45)
            comp = int(prog * np.random.uniform(0.70, 1.0))
            rows_inspeccion.append({
                'Mes': mes,
                'Unidad': und,
                'Tipo_Plan': np.random.choice(tipos_plan),
                'Instrumentos_Programados': prog,
                'Instrumentos_100%': comp,
                'Comentario': np.random.choice(['Sin Novedad', 'Pendiente repuestos por Parada', 'Falta permiso de trabajo', 'Concluido en fecha'])
            })
    df_inspecciones = pd.DataFrame(rows_inspeccion)
    
    return df_ops, df_sst, df_eventos, df_inspecciones

if 'df_ops' not in st.session_state:
    st.session_state.df_ops, st.session_state.df_sst, st.session_state.df_eventos, st.session_state.df_inspecciones = cargar_datos_iniciales()


# =============================================================================
# 3. ENCABEZADO EJECUTIVO (SIN LOGOS)
# =============================================================================
st.markdown(f"""
    <div style="background-color: {COLOR_PRIMARY}; padding: 20px; border-radius: 8px; color: white; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="margin:0; font-size: 1.8rem; color: white;">ADEMINSAC — Panel Instrumentación & SST</h1>
                <p style="margin:5px 0 0 0; font-size: 1rem; color: #D0D7DE;">Contrato N° 3700002135 | Refinería La Pampilla — Repsol Perú</p>
            </div>
            <div style="text-align: right;">
                <span style="background-color: {COLOR_SECONDARY}; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.85rem;">
                    SISTEMA ACTIVO QA/QC
                </span>
                <p style="margin: 5px 0 0 0; font-size: 0.8rem; color: #ADB5BD;">Fecha de Corte: {datetime.date.today().strftime('%d/%m/%Y')}</p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)


# =============================================================================
# 4. ESTRUCTURA DE PESTAÑAS Y NAVEGACIÓN
# =============================================================================
tab1, tab2, tab3 = st.tabs([
    "🛡️ Seguridad OPS & SST", 
    "🚨 Eventos de Seguridad", 
    "🔧 Planes de Inspección Instrumentación"
])


# =============================================================================
# PESTAÑA 1: SEGURIDAD OPS & SST
# =============================================================================
with tab1:
    st.markdown("### 📊 Control de Observaciones Preventivas de Seguridad (OPS) y Cumplimiento SST")
    
    # METRICAS CLAVE DE SEGURIDAD
    m1, m2, m3, m4 = st.columns(4)
    ops_gen_total = len(st.session_state.df_ops[st.session_state.df_ops['Tipo'] == 'Generada'])
    ops_imp_total = len(st.session_state.df_ops[st.session_state.df_ops['Tipo'] == 'Impuesta'])
    cumpl_prom_sst = st.session_state.df_sst['Ejecutado_%'].dropna().mean()
    
    with m1:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>OPS Generadas (Totales)</div><div class='metric-value'>{ops_gen_total}</div></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>OPS Impuestas (Repsol)</div><div class='metric-value' style='color:{COLOR_DANGER}'>{ops_imp_total}</div></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Cumplimiento Promedio SST</div><div class='metric-value' style='color:{COLOR_SUCCESS}'>{cumpl_prom_sst:.1f}%</div></div>", unsafe_allow_html=True)
    with m4:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Meta Mensual OPS Generadas</div><div class='metric-value'>≥ 6 / mes</div></div>", unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        # Gráfico 1: OPS impuestas por mes y gravedad
        st.subheader("1. OPS Impuestas por Mes y Gravedad")
        df_ops_imp = st.session_state.df_ops[st.session_state.df_ops['Tipo'] == 'Impuesta']
        if not df_ops_imp.empty:
            df_g1 = df_ops_imp.groupby(['Mes', 'Gravedad']).size().reset_index(name='Cantidad')
            fig1 = px.bar(
                df_g1, x='Mes', y='Cantidad', color='Gravedad',
                color_discrete_map={'Leve': COLOR_WARNING, 'Moderada': COLOR_SECONDARY, 'Grave': COLOR_DANGER},
                barmode='stack', text_auto=True
            )
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No hay registro de OPS impuestas.")

    with col_g2:
        # Gráfico 2: OPS Generadas vs Cuota Mínima (6/mes) con Semáforo
        st.subheader("2. OPS Generadas vs. Cuota Mínima Mensual (Meta: 6)")
        df_ops_gen = st.session_state.df_ops[st.session_state.df_ops['Tipo'] == 'Generada'].groupby('Mes').size().reset_index(name='Generadas')
        
        all_months = pd.DataFrame({'Mes': st.session_state.df_sst['Mes']})
        df_ops_gen = pd.merge(all_months, df_ops_gen, on='Mes', how='left').fillna(0)
        df_ops_gen['Estado'] = df_ops_gen['Generadas'].apply(lambda x: 'Cumple (≥6)' if x >= 6 else 'Incumple (<6)')
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=df_ops_gen['Mes'], y=df_ops_gen['Generadas'],
            marker_color=df_ops_gen['Estado'].map({'Cumple (≥6)': COLOR_SUCCESS, 'Incumple (<6)': COLOR_DANGER}),
            text=df_ops_gen['Generadas'], textposition='auto', name="OPS Generadas"
        ))
        fig2.add_trace(go.Scatter(
            x=df_ops_gen['Mes'], y=[6]*len(df_ops_gen),
            mode='lines', name='Umbral Mínimo (6)',
            line=dict(color='black', width=2, dash='dash')
        ))
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig2, use_container_width=True)

    col_g3, col_g4 = st.columns(2)
    
    with col_g3:
        # Gráfico 3: OPS impuestas por departamento y gravedad
        st.subheader("3. OPS Impuestas por Departamento / Área")
        if not df_ops_imp.empty:
            df_g3 = df_ops_imp.groupby(['Departamento', 'Gravedad']).size().reset_index(name='Cantidad')
            fig3 = px.bar(
                df_g3, y='Departamento', x='Cantidad', color='Gravedad', orientation='h',
                color_discrete_map={'Leve': COLOR_WARNING, 'Moderada': COLOR_SECONDARY, 'Grave': COLOR_DANGER},
                text_auto=True
            )
            fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig3, use_container_width=True)

    with col_g4:
        # Gráfico 4: Cumplimiento Plan Anual SST (%) con Proyección Automática
        st.subheader("4. Cumplimiento Plan Anual SST (%) y Proyección")
        df_sst_plot = st.session_state.df_sst.copy()
        
        ejecutados = df_sst_plot['Ejecutado_%'].dropna().values
        x_hist = np.arange(len(ejecutados))
        poly = np.polyfit(x_hist, ejecutados, 1)
        
        proyeccion = []
        for i in range(len(df_sst_plot)):
            if pd.isna(df_sst_plot.loc[i, 'Ejecutado_%']):
                val_proj = np.clip(poly[0]*i + poly[1], 0, 100)
                proyeccion.append(val_proj)
            else:
                proyeccion.append(None)
        
        df_sst_plot['Proyección_%'] = proyeccion

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=df_sst_plot['Mes'], y=df_sst_plot['Planificado_%'], name='Meta (100%)', line=dict(color='gray', dash='dash')))
        fig4.add_trace(go.Scatter(x=df_sst_plot['Mes'], y=df_sst_plot['Ejecutado_%'], name='Ejecutado real', mode='lines+markers', line=dict(color=COLOR_PRIMARY, width=3)))
        fig4.add_trace(go.Scatter(x=df_sst_plot['Mes'], y=df_sst_plot['Proyección_%'], name='Proyección Tendencia', mode='lines+markers', line=dict(color=COLOR_SECONDARY, dash='dot')))
        fig4.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(range=[50, 105]), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig4, use_container_width=True)

    # --- MÓDULO DE REGISTRO / EDICIÓN ---
    with st.expander("➕ Registro de Nueva OPS (Impuesta / Generada)"):
        with st.form("form_nueva_ops"):
            c1, c2, c3, c4 = st.columns(4)
            f_mes = c1.selectbox("Mes", st.session_state.df_sst['Mes'].unique())
            f_tipo = c2.selectbox("Tipo de OPS", ['Generada', 'Impuesta'])
            f_depto = c3.selectbox("Departamento / Área", ['Unidad Conversión', 'Destilación / Topping', 'Servicios Auxiliares', 'Tanques y Offsites', 'Terminales Marítimos'])
            f_grav = c4.selectbox("Gravedad", ['Leve', 'Moderada', 'Grave'])
            f_desc = st.text_input("Descripción del hallazgo")
            
            btn_ops = st.form_submit_button("Guardar OPS")
            if btn_ops:
                nueva_row = pd.DataFrame([{'Mes': f_mes, 'Departamento': f_depto, 'Gravedad': f_grav, 'Tipo': f_tipo, 'Descripción': f_desc}])
                st.session_state.df_ops = pd.concat([st.session_state.df_ops, nueva_row], ignore_index=True)
                st.success("OPS registrada correctamente.")
                st.rerun()


# =============================================================================
# PESTAÑA 2: EVENTOS DE SEGURIDAD
# =============================================================================
with tab2:
    st.markdown("### 🚨 Monitoreo Histórico y Línea de Tiempo de Eventos de Seguridad")
    
    col_ev1, col_ev2 = st.columns(2)
    
    with col_ev1:
        st.subheader("Eventos Registrados 2025")
        df_2025 = st.session_state.df_eventos[st.session_state.df_eventos['Año'] == 2025]
        if not df_2025.empty:
            fig_ev25 = px.pie(df_2025, names='Clasificación', hole=0.4, color_discrete_sequence=[COLOR_PRIMARY, COLOR_SECONDARY, COLOR_WARNING])
            fig_ev25.update_layout(paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_ev25, use_container_width=True)
            st.dataframe(df_2025[['Fecha', 'Unidad', 'Evento', 'Estado']], hide_index=True)
        else:
            st.info("Sin eventos registrados en 2025.")
            
    with col_ev2:
        st.subheader("Eventos Registrados 2026")
        df_2026 = st.session_state.df_eventos[st.session_state.df_eventos['Año'] == 2026]
        if not df_2026.empty:
            fig_ev26 = px.pie(df_2026, names='Clasificación', hole=0.4, color_discrete_sequence=[COLOR_DANGER, COLOR_SECONDARY, COLOR_SUCCESS])
            fig_ev26.update_layout(paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_ev26, use_container_width=True)
            st.dataframe(df_2026[['Fecha', 'Unidad', 'Evento', 'Estado']], hide_index=True)
        else:
            st.info("Sin eventos registrados en 2026.")

    # Línea de Tiempo interactiva de Eventos
    st.subheader("⏱️ Línea de Tiempo Cronológica de Eventos de Seguridad")
    df_ev_sorted = st.session_state.df_eventos.sort_values(by='Fecha')
    
    fig_timeline = px.scatter(
        df_ev_sorted, x='Fecha', y='Unidad', color='Clasificación', size=[15]*len(df_ev_sorted),
        hover_data=['Evento', 'Acción_Correctiva', 'Estado'],
        color_discrete_sequence=[COLOR_DANGER, COLOR_SECONDARY, COLOR_PRIMARY, COLOR_WARNING]
    )
    fig_timeline.update_traces(marker=dict(symbol='diamond', line=dict(width=2, color='DarkSlateGrey')))
    fig_timeline.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
    st.plotly_chart(fig_timeline, use_container_width=True)

    # Registro de Nuevos Eventos
    with st.expander("➕ Formulario de Registro de Evento de Seguridad / Incidente"):
        with st.form("form_nuevo_evento"):
            ce1, ce2, ce3 = st.columns(3)
            fe_fecha = ce1.date_input("Fecha del Evento", datetime.date.today())
            fe_unidad = ce2.selectbox("Unidad Operativa", ['Topping 1', 'Topping 2', 'Vacuum 1', 'FCC', 'HDT', 'Plantas Ácidas', 'Servicios Auxiliares', 'Terminales'])
            fe_clasif = ce3.selectbox("Clasificación", ['Accidente con Tiempo Perdido', 'Accidente Sin Tiempo Perdido', 'Cuasi Accidente (Near Miss)', 'Condición Subestándar', 'Falla Operacional', 'Incidente Ambiental / Menor'])
            
            fe_evento = st.text_area("Descripción detallada del evento")
            fe_accion = st.text_area("Acción Correctiva Inmediata / Plan de Acción")
            fe_estado = st.selectbox("Estado de la Acción", ['Abierto', 'En Proceso', 'Cerrado'])
            
            btn_ev = st.form_submit_button("Registrar Evento de Seguridad")
            if btn_ev:
                n_ev = pd.DataFrame([{
                    'Fecha': str(fe_fecha),
                    'Año': fe_fecha.year,
                    'Unidad': fe_unidad,
                    'Evento': fe_evento,
                    'Clasificación': fe_clasif,
                    'Acción_Correctiva': fe_accion,
                    'Estado': fe_estado
                }])
                st.session_state.df_eventos = pd.concat([st.session_state.df_eventos, n_ev], ignore_index=True)
                st.success("Evento de seguridad integrado exitosamente en el historial.")
                st.rerun()


# =============================================================================
# PESTAÑA 3: PLANES DE INSPECCIÓN INSTRUMENTACIÓN
# =============================================================================
with tab3:
    st.markdown("### 🔧 Control Ejecutivo de Avance de Inspecciones de Instrumentación")
    
    # FILTROS DINÁMICOS
    st.markdown("#### 🔍 Filtros de Operación")
    f_col1, f_col2, f_col3 = st.columns(3)
    
    with f_col1:
        filtro_mes = st.multiselect("Filtrar por Mes:", options=sorted(st.session_state.df_inspecciones['Mes'].unique()), default=st.session_state.df_inspecciones['Mes'].unique()[:6])
    with f_col2:
        filtro_unidad = st.multiselect("Filtrar por Unidad Operativa:", options=sorted(st.session_state.df_inspecciones['Unidad'].unique()), default=st.session_state.df_inspecciones['Unidad'].unique())
    with f_col3:
        filtro_tipo = st.multiselect("Filtrar por Tipo de Plan:", options=sorted(st.session_state.df_inspecciones['Tipo_Plan'].unique()), default=st.session_state.df_inspecciones['Tipo_Plan'].unique())

    # Aplicación de Filtros
    df_insp_filtered = st.session_state.df_inspecciones[
        (st.session_state.df_inspecciones['Mes'].isin(filtro_mes)) &
        (st.session_state.df_inspecciones['Unidad'].isin(filtro_unidad)) &
        (st.session_state.df_inspecciones['Tipo_Plan'].isin(filtro_tipo))
    ].copy()

    # CÁLCULOS KPI DE AVANCE DE CAMPO
    tot_prog = df_insp_filtered['Instrumentos_Programados'].sum()
    tot_comp = df_insp_filtered['Instrumentos_100%'].sum()
    pct_avance = (tot_comp / tot_prog * 100) if tot_prog > 0 else 0.0

    df_insp_filtered['Avance_%'] = (df_insp_filtered['Instrumentos_100%'] / df_insp_filtered['Instrumentos_Programados'] * 100).round(1)

    # RESUMEN GLOBAL DE AVANCE (KPI METRICS & GAUGE)
    ki1, ki2, ki3 = st.columns([1, 1, 2])
    with ki1:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Instrumentos Programados</div><div class='metric-value'>{tot_prog:,}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Completados al 100%</div><div class='metric-value' style='color:{COLOR_SUCCESS}'>{tot_comp:,}</div></div>", unsafe_allow_html=True)
    with ki2:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Instrumentos Pendientes</div><div class='metric-value' style='color:{COLOR_DANGER}'>{tot_prog - tot_comp:,}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><div class='metric-title'>% Avance Global Campo</div><div class='metric-value' style='color:{COLOR_PRIMARY}'>{pct_avance:.1f}%</div></div>", unsafe_allow_html=True)
    
    with ki3:
        # Gauge de Avance Global
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = pct_avance,
            title = {'text': "Nivel de Cumplimiento Global (Meta: 95%)", 'font': {'size': 14}},
            delta = {'reference': 95.0, 'increasing': {'color': COLOR_SUCCESS}},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': COLOR_PRIMARY},
                'steps': [
                    {'range': [0, 70], 'color': "#FFCDD2"},
                    {'range': [70, 90], 'color': "#FFE0B2"},
                    {'range': [90, 100], 'color': "#C8E6C9"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 95.0
                }
            }
        ))
        fig_gauge.update_layout(height=220, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gauge, use_container_width=True)

    col_ip1, col_ip2 = st.columns(2)
    
    with col_ip1:
        # Avance por Tipo de Plan
        st.subheader("Avance por Tipo de Plan de Inspección")
        df_tipo_plan = df_insp_filtered.groupby('Tipo_Plan')[['Instrumentos_Programados', 'Instrumentos_100%']].sum().reset_index()
        df_tipo_plan['Pendientes'] = df_tipo_plan['Instrumentos_Programados'] - df_tipo_plan['Instrumentos_100%']
        
        fig_tp = go.Figure()
        fig_tp.add_trace(go.Bar(y=df_tipo_plan['Tipo_Plan'], x=df_tipo_plan['Instrumentos_100%'], name='Completados (100%)', orientation='h', marker_color=COLOR_SUCCESS))
        fig_tp.add_trace(go.Bar(y=df_tipo_plan['Tipo_Plan'], x=df_tipo_plan['Pendientes'], name='Pendientes', orientation='h', marker_color=COLOR_DANGER))
        fig_tp.update_layout(barmode='stack', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_tp, use_container_width=True)

    with col_ip2:
        # Avance Mensual
        st.subheader("Avance Mensual: Completados vs. Pendientes")
        df_mes_plan = df_insp_filtered.groupby('Mes')[['Instrumentos_Programados', 'Instrumentos_100%']].sum().reset_index()
        df_mes_plan['Pendientes'] = df_mes_plan['Instrumentos_Programados'] - df_mes_plan['Instrumentos_100%']
        
        fig_mp = go.Figure()
        fig_mp.add_trace(go.Bar(x=df_mes_plan['Mes'], y=df_mes_plan['Instrumentos_100%'], name='Completados', marker_color=COLOR_PRIMARY))
        fig_mp.add_trace(go.Bar(x=df_mes_plan['Mes'], y=df_mes_plan['Pendientes'], name='Pendientes', marker_color=COLOR_SECONDARY))
        fig_mp.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_mp, use_container_width=True)

    # Matriz Térmica
    st.subheader("Matriz Térmica de Avance de Inspección (% por Unidad y Mes)")
    df_pivot_avance = df_insp_filtered.pivot_table(index='Unidad', columns='Mes', values='Avance_%', aggfunc='mean').fillna(0)
    
    fig_heatmap = px.imshow(
        df_pivot_avance, text_auto=".0f", aspect="auto",
        color_continuous_scale="Reds" if df_pivot_avance.values.min() < 50 else "YlGn",
        labels=dict(x="Mes", y="Unidad Operativa", color="% Avance")
    )
    fig_heatmap.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # TABLA INTERACTIVA DE EDICIÓN Y GESTIÓN
    st.subheader("📋 Resumen General y Modificación de Inspecciones de Campo")
    st.info("💡 **Edición Interactiva:** Puedes modificar directamente las celdas de 'Instrumentos 100%', agregar observaciones o cambiar datos en la siguiente tabla.")

    edited_df_inspecciones = st.data_editor(
        df_insp_filtered[['Mes', 'Unidad', 'Tipo_Plan', 'Instrumentos_Programados', 'Instrumentos_100%', 'Avance_%', 'Comentario']],
        column_config={
            "Avance_%": st.column_config.ProgressColumn(
                "Avance de Campo",
                help="Porcentaje de avance ejecutado",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "Instrumentos_100%": st.column_config.NumberColumn(
                "Cantidad 100%",
                help="Número de instrumentos auditados y concluidos al 100%",
                min_value=0,
                step=1,
            )
        },
        disabled=["Avance_%"],
        num_rows="dynamic",
        use_container_width=True,
        key="editor_inspecciones"
    )

    if st.button("💾 Guardar Cambios en la Tabla de Inspecciones"):
        st.session_state.df_inspecciones.update(edited_df_inspecciones)
        st.success("¡Datos de avance de campo actualizados correctamente!")
        st.rerun()

    # DESCARGA DE REPORTES EXCEL
    st.markdown("---")
    st.subheader("📥 Exportación de Informes de Inspección (Excel)")
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_insp_filtered.to_excel(writer, sheet_name='Avance_Inspecciones', index=False)
        st.session_state.df_ops.to_excel(writer, sheet_name='Registro_OPS', index=False)
        st.session_state.df_eventos.to_excel(writer, sheet_name='Eventos_Seguridad', index=False)
    
    st.download_button(
        label="📊 Descargar Reporte Ejecutivo Completo en Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"Reporte_Control_Inspecciones_Repsol_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )