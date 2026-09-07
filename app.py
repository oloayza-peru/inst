import datetime
import io
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as _go
import streamlit as st

# 1. DEFINICIÓN DE LA FUNCIÓN (Debe ir arriba)
def cargar_datos_iniciales():
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
        'Ejecutado_%': [100, 98, 95, 100, 100, 92, 100, 96, 100, 100, 95, 98] + [None]*6,
        'Tipo_Actividad': np.random.choice(['Capacitación SST', 'Inspección Planeada', 'Auditoría Interna', 'Mantenimiento EPP'], 18)
    })

    df_eventos = pd.DataFrame([
        {'Fecha': '2025-02-14', 'Año': 2025, 'Unidad': 'Topping 1', 'Evento': 'Fuga menor en brida de transmisor de presión', 'Clasificación': 'Incidente Ambiental / Menor', 'Acción_Correctiva': 'Reajuste de pernos y torqueado con protocolo QA/QC', 'Estado': 'Cerrado'},
        {'Fecha': '2025-06-20', 'Año': 2025, 'Unidad': 'FCC (Craqueo Catalítico)', 'Evento': 'Desconexión intempestiva de lazo de control de temperatura', 'Clasificación': 'Falla Operacional', 'Acción_Correctiva': 'Reemplazo de tarjeta I/O y calibración de campo', 'Estado': 'Cerrado'},
        {'Fecha': '2025-10-11', 'Año': 2025, 'Unidad': 'Hydrotreating (HDT)', 'Evento': 'Contacto eléctrico de bajo voltaje en gabinete local', 'Clasificación': 'Cuasi Accidente (Near Miss)', 'Acción_Correctiva': 'Aislamiento térmico y señalización IP65', 'Estado': 'Cerrado'},
        {'Fecha': '2026-01-18', 'Año': 2026, 'Unidad': 'Servicios Auxiliares', 'Evento': 'Deterioro de cableado de señal en válvula de alivio PSV', 'Clasificación': 'Condición Subestándar', 'Acción_Correctiva': 'Canalización con tuberia conduit flexible de acero inox', 'Estado': 'En Proceso'},
        {'Fecha': '2026-03-05', 'Año': 2026, 'Unidad': 'Terminal Marítimo 2', 'Evento': 'Corrosión severa en soporte de transmisor de nivel radar', 'Clasificación': 'Condición Subestándar', 'Acción_Correctiva': 'Cambio de soporte a AISI 316L', 'Estado': 'Abierto'}
    ])

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


# 2. INVOCACIÓN DE LA FUNCIÓN (Debe ir abajo de la definición)
if 'df_ops' not in st.session_state:
    st.session_state.df_ops, st.session_state.df_sst, st.session_state.df_eventos, st.session_state.df_inspecciones = cargar_datos_iniciales()

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y DATOS
# =============================================================================
st.set_page_config(page_title="ADEMINSAC | Control de Inspecciones", layout="wide")

# (Tus funciones de inicialización de session_state permanecen igual aquí)
if 'df_ops' not in st.session_state:
    st.session_state.df_ops, st.session_state.df_sst, st.session_state.df_eventos, st.session_state.df_inspecciones = cargar_datos_iniciales()

# Encabezado principal...
st.title("ADEMINSAC — Panel Instrumentación & SST")

# =============================================================================
# 2. DEFINICIÓN DE PESTAÑAS
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
    
    # ===> AQUÍ AGREGAS EL CARGADOR DE LA PESTAÑA 1 <===
    up_tab1 = st.file_uploader("📂 Cargar archivo de OPS / SST (.xlsx o .csv)", type=["xlsx", "csv"], key="up_ops")
    if up_tab1 is not None:
        try:
            if up_tab1.name.endswith('.csv'):
                st.session_state.df_ops = pd.read_csv(up_tab1)
            else:
                st.session_state.df_ops = pd.read_excel(up_tab1, sheet_name=0)
            st.success("¡Datos de OPS & SST actualizados correctamente!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
    # ==================================================

    # (A continuación sigue el código existente de la Pestaña 1: Métricas, Gráficos 1 al 4, etc.)


# =============================================================================
# PESTAÑA 2: EVENTOS DE SEGURIDAD
# =============================================================================
with tab2:
    st.markdown("### 🚨 Monitoreo Histórico y Línea de Tiempo de Eventos de Seguridad")
    
    # ===> AQUÍ AGREGAS EL CARGADOR DE LA PESTAÑA 2 <===
    up_tab2 = st.file_uploader("📂 Cargar archivo de Eventos de Seguridad (.xlsx o .csv)", type=["xlsx", "csv"], key="up_eventos")
    if up_tab2 is not None:
        try:
            if up_tab2.name.endswith('.csv'):
                st.session_state.df_eventos = pd.read_csv(up_tab2)
            else:
                st.session_state.df_eventos = pd.read_excel(up_tab2, sheet_name=0)
            st.success("¡Historial de Eventos actualizado correctamente!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
    # ==================================================

    # (A continuación sigue el código existente de la Pestaña 2: Gráficos 2025/2026, Línea de tiempo, etc.)


# =============================================================================
# PESTAÑA 3: PLANES DE INSPECCIÓN INSTRUMENTACIÓN
# =============================================================================
with tab3:
    st.markdown("### 🔧 Control Ejecutivo de Avance de Inspecciones de Instrumentación")
    
    # ===> AQUÍ AGREGAS EL CARGADOR DE LA PESTAÑA 3 <===
    up_tab3 = st.file_uploader("📂 Cargar archivo de Planes de Inspección (.xlsx o .csv)", type=["xlsx", "csv"], key="up_inspecciones")
    if up_tab3 is not None:
        try:
            if up_tab3.name.endswith('.csv'):
                st.session_state.df_inspecciones = pd.read_csv(up_tab3)
            else:
                st.session_state.df_inspecciones = pd.read_excel(up_tab3, sheet_name=0)
            st.success("¡Plan de Inspecciones actualizado correctamente!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
    # ==================================================

    # (A continuación sigue el código existente de la Pestaña 3: Filtros de operación, KPIs, Gauge, Tabla interactiva, etc.)
