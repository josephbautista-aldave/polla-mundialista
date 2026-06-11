import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz

# ==========================================
# 1. CONFIGURACIÓN E INICIALIZACIÓN
# ==========================================
st.set_page_config(
    page_title="🏆 Polla Mundial BGL 2026", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Zona horaria local
ZONA_HORARIA = pytz.timezone('America/Santiago')

# Base de datos local de partidos (Fase de Grupos)
PARTIDOS_DATA = [
    {"id": "1", "fase": "Grupo A", "local": "México", "visita": "Polonia", "bandera_L": "🇲🇽", "bandera_V": "🇵🇱", "sede": "Estadio Azteca, CDMX", "fecha": "11 Jun"},
    {"id": "2", "fase": "Grupo B", "local": "Canadá", "visita": "Marruecos", "bandera_L": "🇨🇦", "bandera_V": "🇲🇦", "sede": "BMO Field, Toronto", "fecha": "12 Jun"},
    {"id": "3", "fase": "Grupo C", "local": "USA", "visita": "Gales", "bandera_L": "🇺🇸", "bandera_V": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "sede": "SoFi Stadium, LA", "fecha": "12 Jun"},
    {"id": "4", "fase": "Grupo D", "local": "Argentina", "visita": "Francia", "bandera_L": "🇦🇷", "bandera_V": "🇫🇷", "sede": "MetLife Stadium, NY/NJ", "fecha": "13 Jun"},
    {"id": "5", "fase": "Grupo E", "local": "Chile", "visita": "Uruguay", "bandera_L": "🇨🇱", "bandera_V": "🇺🇾", "sede": "Hard Rock Stadium, Miami", "fecha": "14 Jun"},
    {"id": "6", "fase": "Grupo F", "local": "Brasil", "visita": "Inglaterra", "bandera_L": "🇧🇷", "bandera_V": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "sede": "AT&T Stadium, Dallas", "fecha": "15 Jun"},
]

OPCIONES_PARTIDOS = [
    f"{p['bandera_L']} {p['local']} vs {p['visita']} {p['bandera_V']} | {p['fase']} | 📍 {p['sede']} ({p['fecha']})"
    for p in PARTIDOS_DATA
]

# Estructura de columnas
COLS_PRONOSTICOS = ["Timestamp", "Usuario", "Partido", "Goles_Local", "Goles_Visita"]
COLS_RESULTADOS = ["Timestamp", "Partido", "Goles_Local", "Goles_Visita"]

# ==========================================
# 2. CAPA DE DATOS (CONEXIÓN ROBUSTA)
# ==========================================
def obtener_conexion():
    """Retorna el objeto de conexión de GSheets."""
    return st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(sheet_name, columns, ttl=60):
    """Carga datos con manejo de caché y tolerancia a fallos."""
    conn = obtener_conexion()
    try:
        df = conn.read(worksheet=sheet_name, ttl=ttl)
        if df is None or df.empty:
            return pd.DataFrame(columns=columns)
        return df.dropna(how="all")
    except Exception as e:
        st.error(f"⚠️ Error de conexión al cargar {sheet_name}. Revisa tu internet o los permisos de la planilla.")
        return pd.DataFrame(columns=columns)

def guardar_datos(sheet_name, new_row_df, subset_drop):
    """Guarda datos de forma segura, sobreescribiendo registros previos y limpiando el caché."""
    conn = obtener_conexion()
    try:
        # Forzar lectura sin caché para no sobreescribir datos antiguos
        df_existente = conn.read(worksheet=sheet_name, ttl=0)
        if df_existente is None or df_existente.empty:
            df_existente = pd.DataFrame(columns=new_row_df.columns)
        else:
            df_existente = df_existente.dropna(how="all")
            
        # Concatenar y aplicar drop_duplicates manteniendo el último ingreso
        df_actualizado = pd.concat([df_existente, new_row_df], ignore_index=True)
        df_actualizado = df_actualizado.drop_duplicates(subset=subset_drop, keep='last')
        
        # Actualizar GSheets y limpiar caché de Streamlit
        conn.update(worksheet=sheet_name, data=df_actualizado)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"⚠️ Error crítico al guardar los datos: {str(e)}")
        return False

# ==========================================
# 3. MOTOR LÓGICO DE GESTIÓN Y RANKING
# ==========================================
def calcular_ranking(df_p, df_r):
    """Calcula el puntaje exacto y de tendencia, devolviendo un DataFrame ordenado."""
    if df_p.empty or df_r.empty:
        return pd.DataFrame(columns=["Usuario", "Puntos", "Aciertos Exactos", "Tendencias", "Total Pronósticos"])

    df = pd.merge(df_p, df_r, on="Partido", suffixes=('_P', '_R'))
    
    puntos, exactos, tendencias = [], [], []

    for _, row in df.iterrows():
        try:
            gl_p, gv_p = int(row['Goles_Local_P']), int(row['Goles_Visita_P'])
            gl_r, gv_r = int(row['Goles_Local_R']), int(row['Goles_Visita_R'])
            
            # Lógica de asignación
            if gl_p == gl_r and gv_p == gv_r:
                puntos.append(3); exactos.append(1); tendencias.append(0)
            elif (gl_p > gv_p and gl_r > gv_r) or (gl_p < gv_p and gl_r < gv_r) or (gl_p == gv_p and gl_r == gv_r):
                puntos.append(1); exactos.append(0); tendencias.append(1)
            else:
                puntos.append(0); exactos.append(0); tendencias.append(0)
        except ValueError:
            puntos.append(0); exactos.append(0); tendencias.append(0)

    df['Puntos'] = puntos
    df['Exactos'] = exactos
    df['Tendencias'] = tendencias
    
    # Agrupación y KPI por usuario
    ranking = df.groupby("Usuario").agg(
        Puntos=('Puntos', 'sum'),
        Aciertos_Exactos=('Exactos', 'sum'),
        Tendencias=('Tendencias', 'sum'),
        Partidos_Jugados=('Partido', 'count')
    ).reset_index()
    
    # Ordenamiento jerárquico: Puntos > Aciertos Exactos > Partidos Jugados (menos es mejor eficiencia)
    ranking = ranking.sort_values(by=["Puntos", "Aciertos_Exactos", "Partidos_Jugados"], ascending=[False, False, True]).reset_index(drop=True)
    ranking.index += 1 
    
    # Renombrar para presentación visual
    return ranking.rename(columns={
        "Aciertos_Exactos": "Aciertos Exactos (3pts)",
        "Tendencias": "Acierto Tendencia (1pt)",
        "Partidos_Jugados": "Pronósticos Evaluados"
    })

# ==========================================
# 4. INTERFAZ DE USUARIO Y RENDERIZADO
# ==========================================
st.sidebar.title("⚽ Mundial BGL 2026")
menu = st.sidebar.radio("Navegación:", [
    "🏆 Ranking Oficial", 
    "📝 Ingresar Pronóstico", 
    "📊 Control de Gestión", 
    "⚙️ Operaciones (Admin)"
])

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Reglamento Interno:**
* 🎯 **3 Puntos:** Marcador exacto.
* 📈 **1 Punto:** Acertar ganador o empate.
* ❌ **0 Puntos:** Ningún acierto.
* *Nota: Solo se toma el último pronóstico guardado.*
""")
if st.sidebar.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

# Carga de datos base en memoria
df_pron = cargar_datos("Pronosticos", COLS_PRONOSTICOS)
df_res = cargar_datos("Resultados", COLS_RESULTADOS)

# ------------------------------------------
# VISTA: RANKING
# ------------------------------------------
if menu == "🏆 Ranking Oficial":
    st.title("🏆 Tabla de Posiciones")
    st.markdown("Clasificación general actualizada en tiempo real basada en los resultados oficiales.")
    
    ranking_df = calcular_ranking(df_pron, df_res)
    
    if not ranking_df.empty:
        c1, c2, c3 = st.columns(3)
        with c2: 
            st.metric("🥇 Líder Actual", f"{ranking_df.iloc[0]['Usuario']}", f"{ranking_df.iloc[0]['Puntos']} pts")
        if len(ranking_df) > 1:
            with c1: 
                st.metric("🥈 Segundo", f"{ranking_df.iloc[1]['Usuario']}", f"{ranking_df.iloc[1]['Puntos']} pts", delta_color="off")
        if len(ranking_df) > 2:
            with c3: 
                st.metric("🥉 Tercero", f"{ranking_df.iloc[2]['Usuario']}", f"{ranking_df.iloc[2]['Puntos']} pts", delta_color="off")
        
        st.markdown("### 📋 Detalle de Clasificación")
        st.dataframe(ranking_df, use_container_width=True, hide_index=False)
    else:
        st.info("Aún no se han consolidado resultados oficiales contra los pronósticos ingresados.")

# ------------------------------------------
# VISTA: PRONÓSTICOS
# ------------------------------------------
elif menu == "📝 Ingresar Pronóstico":
    st.title("📝 Registro de Pronósticos")
    st.markdown("Selecciona el partido, proyecta tu resultado y guarda en el sistema.")
    
    with st.form("form_pronostico", clear_on_submit=False):
        usuario_input = st.text_input("👤 Tu Nombre (Usa siempre el mismo):", placeholder="Ej: Daniela, Yeison, Pato, Milcka...")
        partido_seleccionado = st.selectbox("⚔️ Selecciona el Partido:", OPCIONES_PARTIDOS)
        
        equipos = partido_seleccionado.split('|')[0].strip()
        local, visita = equipos.split(' vs ')
        
        st.markdown(f"#### {local} 🆚 {visita}")
        
        c1, c2 = st.columns(2)
        with c1:
            g_local = st.number_input(f"Goles {local}:", min_value=0, max_value=20, step=1, value=0)
        with c2:
            g_visita = st.number_input(f"Goles {visita}:", min_value=0, max_value=20, step=1, value=0)
            
        submit = st.form_submit_button("💾 Guardar Pronóstico", type="primary")
        
        if submit:
            usuario_limpio = usuario_input.strip().title() # Limpieza de string
            if not usuario_limpio:
                st.error("⚠️ Debes ingresar un nombre de usuario válido.")
            else:
                ahora = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")
                nuevo_pron = pd.DataFrame([{
                    "Timestamp": ahora,
                    "Usuario": usuario_limpio,
                    "Partido": partido_seleccionado,
                    "Goles_Local": g_local,
                    "Goles_Visita": g_visita
                }])
                
                with st.spinner("Sincronizando con Google Sheets..."):
                    exito = guardar_datos("Pronosticos", nuevo_pron, subset_drop=["Usuario", "Partido"])
                if exito:
                    st.success(f"✅ Registro exitoso para **{usuario_limpio}**.")
                    st.balloons()

# ------------------------------------------
# VISTA: DASHBOARD / CONTROL DE GESTIÓN
# ------------------------------------------
elif menu == "📊 Control de Gestión":
    st.title("📊 Panel de Control y Estadísticas")
    st.markdown("Monitoreo de la participación y tendencias de los resultados proyectados.")
    
    if not df_pron.empty:
        # KPIs
        total_apuestas = len(df_pron)
        total_usuarios = df_pron['Usuario'].nunique()
        df_pron['Goles_Totales'] = pd.to_numeric(df_pron['Goles_Local']) + pd.to_numeric(df_pron['Goles_Visita'])
        promedio_goles = df_pron['Goles_Totales'].mean()
        partido_mas_votado = df_pron['Partido'].value_counts().idxmax()
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Pronósticos", total_apuestas)
        kpi2.metric("Usuarios Activos", total_usuarios)
        kpi3.metric("Promedio Goles Esperados", round(promedio_goles, 2))
        kpi4.metric("Partido + Popular", partido_mas_votado.split('|')[0].strip())
        
        st.markdown("---")
        c_grafico, c_tabla = st.columns([2, 1])
        
        with c_grafico:
            st.markdown("### 📈 Participación por Partido")
            conteo_p = df_pron['Partido'].value_counts().reset_index()
            conteo_p.columns = ['Partido', 'Volumen']
            conteo_p['Partido'] = conteo_p['Partido'].apply(lambda x: x.split('|')[0].strip())
            st.bar_chart(conteo_p.set_index('Partido'), color="#2ecc71")
            
        with c_tabla:
            st.markdown("### 👥 Top Participantes")
            actividad_usuarios = df_pron['Usuario'].value_counts().reset_index()
            actividad_usuarios.columns = ['Usuario', 'Pronósticos Ingresados']
            st.dataframe(actividad_usuarios, hide_index=True, use_container_width=True)
            
        st.markdown("### 🔍 Registro Crudo (Últimos Movimientos)")
        st.dataframe(df_pron.sort_values(by="Timestamp", ascending=False).head(10), use_container_width=True)
    else:
        st.warning("No hay suficientes datos procesados para generar el dashboard.")

# ------------------------------------------
# VISTA: PANEL DE ADMINISTRADOR
# ------------------------------------------
elif menu == "⚙️ Operaciones (Admin)":
    st.title("⚙️ Operaciones y Cierre de Partidos")
    
    if "admin_auth" not in st.session_state:
        st.session_state["admin_auth"] = False

    if not st.session_state["admin_auth"]:
        pwd = st.text_input("🔑 Clave de Operaciones:", type="password")
        if st.button("Validar Credenciales"):
            if pwd == "Mundial2026!": # Contraseña de seguridad
                st.session_state["admin_auth"] = True
                st.rerun()
            else:
                st.error("Acceso denegado.")
    else:
        st.success("✅ Autenticado en Consola de Operaciones")
        if st.button("Cerrar Sesión"):
            st.session_state["admin_auth"] = False
            st.rerun()
            
        st.markdown("### 📥 Carga de Resultados Oficiales")
        with st.form("form_resultados"):
            partido_res = st.selectbox("⚔️ Seleccionar partido finalizado:", OPCIONES_PARTIDOS)
            
            c1, c2 = st.columns(2)
            with c1: g_loc = st.number_input("⚽ Goles Reales Local:", min_value=0, max_value=20, step=1, value=0)
            with c2: g_vis = st.number_input("⚽ Goles Reales Visita:", min_value=0, max_value=20, step=1, value=0)
                
            if st.form_submit_button("🚨 Confirmar e Impactar Ranking", type="primary"):
                ahora = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")
                nuevo_res = pd.DataFrame([{
                    "Timestamp": ahora, 
                    "Partido": partido_res, 
                    "Goles_Local": g_loc, 
                    "Goles_Visita": g_vis
                }])
                
                with st.spinner("Actualizando base oficial..."):
                    exito = guardar_datos("Resultados", nuevo_res, subset_drop=["Partido"])
                if exito:
                    st.success("✅ Resultado consolidado correctamente. El ranking se ha actualizado.")
