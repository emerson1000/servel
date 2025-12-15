import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
from datetime import datetime

# Configuración de página
st.set_page_config(
    page_title="Monitor Electoral Chile",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado mejorado
st.markdown("""
    <style>
    /* Configuración general */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }
    
    /* Header principal */
    .main-header {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, #42a5f5 0%, #29b6f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-size: 1.3rem;
        color: #e0e0e0 !important;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    /* Cards de métricas mejoradas - fondo oscuro para mejor contraste */
    div[data-testid="stMetricContainer"] {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        padding: 1.8rem 1.5rem;
        border-radius: 15px;
        border: 2px solid #42a5f5;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    
    div[data-testid="stMetricContainer"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1565c0;
        line-height: 1.2;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        color: #424242;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 1rem;
        font-weight: 700;
    }
    
    /* Títulos de sección - colores accesibles */
    h2 {
        color: #42a5f5 !important;
        font-weight: 800;
        font-size: 1.8rem;
        border-left: 5px solid #29b6f6;
        padding-left: 1rem;
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
    }
    
    h3 {
        color: #64b5f6 !important;
        font-weight: 700;
        font-size: 1.4rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    /* Info boxes mejoradas */
    .stInfo {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 5px solid #2196f3;
        padding: 1.2rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border-left: 5px solid #4caf50;
        padding: 1rem;
        border-radius: 8px;
    }
    
    /* Separadores */
    hr {
        border: none;
        border-top: 3px solid #e0e0e0;
        margin: 2.5rem 0;
    }
    
    /* Tablas mejoradas */
    .dataframe {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Sidebar mejorado */
    .css-1d391kg {
        background: linear-gradient(180deg, #f5f5f5 0%, #ffffff 100%);
    }
    
    /* Mejorar contraste general - forzar colores claros */
    p, div, span {
        color: #e0e0e0 !important;
    }
    
    /* Forzar números y valores a blanco */
    .stNumber, .stText, [data-testid="stText"] {
        color: #ffffff !important;
    }
    
    /* Cards personalizados */
    .info-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

def load_data(file_path):
    """Carga datos"""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"Error cargando el archivo: {e}")
        return None

@st.cache_data
def load_election_config(config_path='config_elecciones.json'):
    """Carga la configuración de elecciones"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

def detect_candidates(df):
    """Detecta automáticamente las columnas de candidatos"""
    cols = [c.replace('_votos', '') for c in df.columns if c.endswith('_votos')]
    ignored = ['blanco', 'nulo', 'emitidos', 'total']
    candidates = [c for c in cols if c not in ignored]
    return candidates

def detect_election_from_filename(filename, config):
    """Intenta detectar qué elección es basándose en el nombre del archivo"""
    if not config:
        return None
    
    filename_lower = filename.lower()
    
    for key, eleccion in config.get('elecciones', {}).items():
        nombre_lower = eleccion.get('nombre', '').lower()
        if any(palabra in filename_lower for palabra in nombre_lower.split()):
            return key, eleccion
        
        if 'primera' in filename_lower or '1v' in filename_lower or '1ra' in filename_lower:
            if 'primera' in key or '1v' in key:
                return key, eleccion
        if 'segunda' in filename_lower or '2v' in filename_lower or '2da' in filename_lower:
            if 'segunda' in key or '2v' in key:
                return key, eleccion
    
    return None

def format_candidate_name(candidate_key):
    """Formatea el nombre del candidato para mostrar"""
    return candidate_key.replace('_', ' ').title()

# --- HEADER ---
st.markdown('<h1 class="main-header">🗳️ Monitor Electoral Chile</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Análisis de resultados electorales en tiempo real</p>', unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("⚙️ Configuración")

config = load_election_config()
folder_path = "."

# Buscar archivos CSV
try:
    all_files = [
        f for f in os.listdir(folder_path) 
        if f.endswith('.csv') 
        and 'matriz' in f.lower()
        and 'progreso_parcial' not in f.lower()
    ]
    all_files_with_time = [(f, os.path.getmtime(os.path.join(folder_path, f))) for f in all_files]
    all_files_with_time.sort(key=lambda x: x[1], reverse=True)
    files = [f[0] for f in all_files_with_time]
except Exception as e:
    st.error(f"Error accediendo a la carpeta: {e}")
    files = []

if not files:
    st.warning("No se encontraron archivos CSV con el prefijo 'matriz' en la carpeta.")
    st.info("💡 Ejecuta el scraper primero para generar los archivos de datos.")
    st.stop()

# Selector de archivo
selected_file = st.sidebar.selectbox(
    "📁 Selecciona archivo CSV:", 
    files,
    index=0,
    help="Archivos ordenados por fecha (más recientes primero)"
)

eleccion_info = None
if config:
    eleccion_detectada = detect_election_from_filename(selected_file, config)
    if eleccion_detectada:
        eleccion_key, eleccion_info = eleccion_detectada
        st.sidebar.success(f"✅ {eleccion_info['nombre']}")

# Cargar datos
file_path = os.path.join(folder_path, selected_file)
df = load_data(file_path)

if df is None:
    st.error("Error al cargar los datos.")
    st.stop()

# Información del archivo
file_time = os.path.getmtime(file_path)
file_date = pd.Timestamp.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S')
st.sidebar.markdown("---")
st.sidebar.markdown(f"**📅 Generado:** {file_date}")
st.sidebar.markdown(f"**📊 Comunas:** {len(df)}")
st.sidebar.markdown(f"**👥 Candidatos:** {len(detect_candidates(df))}")

# Detectar candidatos
candidates = detect_candidates(df)

if not candidates:
    st.error("No se pudieron detectar candidatos en el archivo.")
    st.stop()

# Detectar si es primera o segunda vuelta
es_segunda_vuelta = False
if eleccion_info and 'vuelta' in eleccion_info:
    es_segunda_vuelta = eleccion_info['vuelta'] == 2

# --- CONTENIDO PRINCIPAL ---

# Header con información de la elección
if eleccion_info:
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("🗳️ Elección", eleccion_info['nombre'])
    with col_info2:
        st.metric("📍 Comunas", f"{len(df):,}")
    with col_info3:
        st.metric("👥 Candidatos", len(candidates))

st.markdown("---")

# Calcular resultados nacionales
national_results = {}
total_votes_valid = 0

for cand in candidates:
    votes = df[f"{cand}_votos"].sum()
    national_results[cand] = votes
    total_votes_valid += votes

sorted_results = dict(sorted(national_results.items(), key=lambda item: item[1], reverse=True))

# --- SECCIÓN 1: KPIs PRINCIPALES ---
st.markdown("## 📊 Resultados Nacionales")

# Mostrar todos los candidatos en KPIs
# Para segunda vuelta: 2 columnas, para primera vuelta: hasta 4 columnas
if es_segunda_vuelta:
    num_cols = min(len(candidates), 2)
else:
    num_cols = min(len(candidates), 4)
kpi_cols = st.columns(num_cols)

for idx, (cand, votes) in enumerate(sorted_results.items()):
    col_idx = idx % num_cols
    if idx > 0 and col_idx == 0:
        kpi_cols = st.columns(num_cols)
    
    pct = (votes / total_votes_valid) * 100 if total_votes_valid > 0 else 0
    with kpi_cols[col_idx]:
        st.metric(
            label=format_candidate_name(cand),
            value=f"{votes:,.0f}",
            delta=f"{pct:.1f}%"
        )

st.markdown("---")

# --- SECCIÓN 2: GRÁFICOS PRINCIPALES ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("### 📈 Distribución de Votos")
    chart_data = pd.DataFrame({
        'Candidato': [format_candidate_name(c) for c in sorted_results.keys()],
        'Votos': list(sorted_results.values()),
        'Porcentaje': [(v / total_votes_valid * 100) if total_votes_valid > 0 else 0 
                       for v in sorted_results.values()]
    })
    
    chart_data['Porcentaje_Texto'] = chart_data['Porcentaje'].apply(lambda x: f'{x:.1f}%')
    
    # Colores: 2 para segunda vuelta, 8 para primera vuelta
    if es_segunda_vuelta:
        color_sequence = ['#42a5f5', '#ff9800']  # Azul y naranja para 2 candidatos
    else:
        color_sequence = ['#42a5f5', '#ff9800', '#00bcd4', '#ff5722', '#9c27b0', '#4caf50', '#f44336', '#ffc107']
    
    fig_bar = px.bar(
        chart_data, 
        x='Votos', 
        y='Candidato',
        orientation='h',
        color='Candidato',
        text='Porcentaje_Texto',
        title="",
        labels={'Votos': 'Número de Votos', 'Candidato': ''},
        color_discrete_sequence=color_sequence
    )
    fig_bar.update_layout(
        showlegend=False, 
        height=450,
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font=dict(size=13, color='#ffffff', family='Arial'),
        xaxis=dict(
            gridcolor='#424242', 
            linecolor='#616161',
            title_font=dict(size=14, color='#ffffff')
        ),
        yaxis=dict(
            gridcolor='#424242', 
            linecolor='#616161',
            title_font=dict(size=14, color='#ffffff')
        ),
        margin=dict(l=10, r=10, t=10, b=10)
    )
    fig_bar.update_traces(
        textposition='outside',
        marker=dict(line=dict(width=1, color='#ffffff'))
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_chart2:
    st.markdown("### 🥧 Distribución Porcentual")
    # Colores: 2 para segunda vuelta, 8 para primera vuelta
    if es_segunda_vuelta:
        color_sequence = ['#42a5f5', '#ff9800']  # Azul y naranja para 2 candidatos
    else:
        color_sequence = ['#42a5f5', '#ff9800', '#00bcd4', '#ff5722', '#9c27b0', '#4caf50', '#f44336', '#ffc107']
    
    fig_pie = px.pie(
        chart_data,
        values='Votos',
        names='Candidato',
        title="",
        color_discrete_sequence=color_sequence,
        hole=0.4
    )
    fig_pie.update_layout(
        height=450,
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font=dict(size=13, color='#ffffff', family='Arial'),
        showlegend=True,
        legend=dict(
            font=dict(color='#ffffff', size=12),
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
    )
    fig_pie.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont=dict(size=11, color='#ffffff', family='Arial Bold')
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# --- SECCIÓN 3: TABLA COMPLETA DE RESULTADOS ---
st.markdown("## 📋 Tabla de Resultados Completa")

results_table = pd.DataFrame({
    'Candidato': [format_candidate_name(c) for c in sorted_results.keys()],
    'Votos': [f"{v:,.0f}" for v in sorted_results.values()],
    'Porcentaje': [f"{(v / total_votes_valid * 100):.2f}%" if total_votes_valid > 0 else "0.00%" 
                   for v in sorted_results.values()],
    'Votos_Numerico': list(sorted_results.values())
})

results_table_display = results_table[['Candidato', 'Votos', 'Porcentaje']].copy()
results_table_display.columns = ['Candidato', 'Votos', 'Porcentaje (%)']

st.dataframe(
    results_table_display,
    use_container_width=True,
    hide_index=True,
    height=400
)

st.markdown("---")

# --- SECCIÓN 4: ANÁLISIS POR REGIÓN Y COMUNA ---
st.markdown("## 🔍 Análisis Geográfico")

# Filtros
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    regiones = ["Todas"] + sorted(list(df['region'].unique()))
    selected_region = st.selectbox("🌍 Filtrar por Región:", regiones, key="region_filter")

selected_comuna = "Todas"
filtered_df = df.copy()

if selected_region != "Todas":
    filtered_df = filtered_df[filtered_df['region'] == selected_region]
    
    with filter_col2:
        comunas = ["Todas"] + sorted(list(filtered_df['comuna'].unique()))
        selected_comuna = st.selectbox("🏘️ Filtrar por Comuna:", comunas, key="comuna_filter")
        
    if selected_comuna != "Todas":
        filtered_df = filtered_df[filtered_df['comuna'] == selected_comuna]

# Resumen del filtro
if selected_region != "Todas" or selected_comuna != "Todas":
    st.info(
        f"📍 **Filtro activo:** {selected_region} {f'- {selected_comuna}' if selected_comuna != 'Todas' else ''} ({len(filtered_df)} comunas)", 
        icon="ℹ️"
    )

# Resultados agregados del filtro
if len(filtered_df) > 0:
    st.markdown("### 📊 Resultados del Área Seleccionada")
    
    filtered_results = {}
    filtered_total = 0
    
    for cand in candidates:
        votes = filtered_df[f"{cand}_votos"].sum()
        filtered_results[cand] = votes
        filtered_total += votes
    
    filtered_sorted = dict(sorted(filtered_results.items(), key=lambda item: item[1], reverse=True))
    
    # Gráfico de barras del área filtrada
    filtered_chart_data = pd.DataFrame({
        'Candidato': [format_candidate_name(c) for c in filtered_sorted.keys()],
        'Votos': list(filtered_sorted.values()),
        'Porcentaje': [(v / filtered_total * 100) if filtered_total > 0 else 0 
                       for v in filtered_sorted.values()]
    })
    
    filtered_chart_data['Porcentaje_Texto'] = filtered_chart_data['Porcentaje'].apply(lambda x: f'{x:.1f}%')
    
    fig_filtered = px.bar(
        filtered_chart_data,
        x='Candidato',
        y='Votos',
        text='Porcentaje_Texto',
        title="",
        color='Votos',
        color_continuous_scale='Blues',
        labels={'Votos': 'Número de Votos', 'Candidato': 'Candidato'}
    )
    fig_filtered.update_layout(
        height=400,
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font=dict(size=12, color='#ffffff', family='Arial'),
        showlegend=False,
        xaxis=dict(gridcolor='#424242', linecolor='#616161', title_font=dict(color='#ffffff')),
        yaxis=dict(gridcolor='#424242', linecolor='#616161', title_font=dict(color='#ffffff'))
    )
    fig_filtered.update_traces(
        textposition='outside',
        marker=dict(line=dict(width=1, color='#ffffff'))
    )
    st.plotly_chart(fig_filtered, use_container_width=True)
    
    # Tabla detallada
    st.markdown("### 📋 Detalle por Comuna")
    display_cols = ['comuna', 'region'] + [f"{c}_votos" for c in candidates] + [f"{c}_pct" for c in candidates]
    display_cols = [col for col in display_cols if col in filtered_df.columns]
    
    display_df = filtered_df[display_cols].copy()
    rename_dict = {}
    for col in display_df.columns:
        if col == 'comuna':
            rename_dict[col] = 'Comuna'
        elif col == 'region':
            rename_dict[col] = 'Región'
        elif col.endswith('_votos'):
            rename_dict[col] = format_candidate_name(col.replace('_votos', '')) + ' (Votos)'
        elif col.endswith('_pct'):
            rename_dict[col] = format_candidate_name(col.replace('_pct', '')) + ' (%)'
    
    display_df = display_df.rename(columns=rename_dict)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        hide_index=True
    )

# --- SECCIÓN 5: ANÁLISIS POR REGIÓN ---
st.markdown("---")
st.markdown("## 🗺️ Análisis Comparativo por Región")

region_summary = df.groupby('region').agg({
    **{f"{c}_votos": 'sum' for c in candidates if f"{c}_votos" in df.columns}
}).reset_index()

# Calcular porcentajes por región
for cand in candidates:
    if f"{cand}_votos" in region_summary.columns:
        total_region = region_summary[[f"{c}_votos" for c in candidates if f"{c}_votos" in region_summary.columns]].sum(axis=1)
        region_summary[f"{cand}_pct"] = (region_summary[f"{cand}_votos"] / total_region * 100).round(2)

# Gráfico de regiones
region_chart_data = []
for _, row in region_summary.iterrows():
    region = row['region']
    for cand in candidates:
        if f"{cand}_votos" in row:
            region_chart_data.append({
                'Región': region,
                'Candidato': format_candidate_name(cand),
                'Votos': row[f"{cand}_votos"],
                'Porcentaje': row.get(f"{cand}_pct", 0)
            })

if region_chart_data:
    region_df = pd.DataFrame(region_chart_data)
    
    # Colores: 2 para segunda vuelta, 8 para primera vuelta
    if es_segunda_vuelta:
        color_sequence = ['#42a5f5', '#ff9800']  # Azul y naranja para 2 candidatos
    else:
        color_sequence = ['#42a5f5', '#ff9800', '#00bcd4', '#ff5722', '#9c27b0', '#4caf50', '#f44336', '#ffc107']
    
    fig_region = px.bar(
        region_df,
        x='Región',
        y='Votos',
        color='Candidato',
        title="",
        barmode='group',
        color_discrete_sequence=color_sequence
    )
    fig_region.update_layout(
        height=500,
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font=dict(size=12, color='#ffffff', family='Arial'),
        xaxis=dict(
            gridcolor='#e0e0e0', 
            linecolor='#bdbdbd', 
            tickangle=-45,
            title_font=dict(size=14, color='#424242')
        ),
        yaxis=dict(
            gridcolor='#e0e0e0', 
            linecolor='#bdbdbd',
            title_font=dict(size=14, color='#424242')
        ),
        legend=dict(
            font=dict(color='#ffffff', size=11),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    st.plotly_chart(fig_region, use_container_width=True)
    
    # Tabla resumen por región
    st.markdown("### 📊 Resumen por Región")
    region_display_cols = ['region'] + [f"{c}_votos" for c in candidates if f"{c}_votos" in region_summary.columns]
    region_display = region_summary[region_display_cols].copy()
    region_display = region_display.rename(columns={'region': 'Región'})
    for col in region_display.columns:
        if col != 'Región':
            region_display[col] = region_display[col].apply(lambda x: f"{x:,.0f}")
            region_display = region_display.rename(columns={col: format_candidate_name(col.replace('_votos', ''))})
    
    st.dataframe(region_display, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #757575; padding: 2rem 0;">'
    '<strong>Monitor Electoral Chile</strong> - Sistema de análisis de resultados electorales<br>'
    f'Última actualización: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    '</div>',
    unsafe_allow_html=True
)
