import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="🏆 Polla Mundial 2026", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Partidos base para el torneo (puedes agregar más aquí)
PARTIDOS = [
    "Brasil vs Francia",
    "Argentina vs España",
    "Colombia vs Uruguay",
    "Inglaterra vs Alemania",
    "Chile vs Perú"
]

# ==========================================
# FUNCIONES DE BASE DE DATOS (GSHEETS)
# ==========================================
def load_data(sheet_name, columns):
    """Carga los datos desde Google Sheets. Si la hoja está vacía, devuelve un DataFrame base."""
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        # ttl=0 fuerza a leer los datos más recientes siempre
        df = conn.read(worksheet=sheet_name, ttl=0) 
        if df.empty:
            return pd.DataFrame(columns=columns)
        return df.dropna(how="all")
    except Exception:
        # Si la hoja no existe aún, devolvemos la estructura vacía
        return pd.DataFrame(columns=columns)

def save_data(sheet_name, new_data_df, subset_drop):
    """Guarda nuevos datos, sobreescribiendo pronósticos/resultados previos del mismo usuario/partido."""
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 1. Leer datos actuales
    try:
        existing_data = conn.read(worksheet=sheet_name, ttl=0).dropna(how="all")
    except Exception:
        existing_data = pd.DataFrame(columns=new_data_df.columns)
        
    # 2. Unir y limpiar duplicados (mantiene el último ingreso)
    updated_data = pd.concat([existing_data, new_data_df], ignore_index=True)
    updated_data = updated_data.drop_duplicates(subset=subset_drop, keep='last')
    
    # 3. Actualizar la planilla
    conn.update(worksheet=sheet_name, data=updated_data)
    st.cache_data.clear()

# ==========================================
# MOTOR DE PUNTOS
# ==========================================
def calcular_ranking(df_pronosticos, df_resultados):
    if df_pronosticos.empty or df_resultados.empty:
        return pd.DataFrame(columns=["Usuario", "Puntos", "Aciertos Exactos"])

    # Cruzar pronósticos con resultados oficiales
    df = pd.merge(df_pronosticos, df_resultados, on="Partido", suffixes=('_P', '_R'))
    
    puntos = []
    exactos = []

    for _, row in df.iterrows():
        try:
            gl_p, gv_p = int(row['Goles_Local_P']), int(row['Goles_Visita_P'])
            gl_r, gv_r = int(row['Goles_Local_R']), int(row['Goles_Visita_R'])
            
            # Lógica de puntaje
            if gl_p == gl_r and gv_p == gv_r:
                puntos.append(3) # Acierto exacto
                exactos.append(1)
            elif (gl_p > gv_p and gl_r > gv_r) or (gl_p < gv_p and gl_r < gv_r) or (gl_p == gv_p and gl_r == gv_r):
                puntos.append(1) # Acierto de tendencia (ganador/empate)
                exactos.append(0)
            else:
                puntos.append(0) # Ningún acierto
                exactos.append(0)
        except ValueError:
            puntos.append(0)
            exactos.append(0)

    df['Puntos'] = puntos
    df['Exactos'] = exactos
    
    # Agrupar por usuario
    ranking = df.groupby("Usuario").agg({'Puntos': 'sum', 'Exactos': 'sum'}).reset_index()
    ranking = ranking.sort_values(by=["Puntos", "Exactos"], ascending=[False, False]).reset_index(drop=True)
    ranking.index += 1 # Que el ranking empiece en 1
    
    return ranking.rename(columns={"Exactos": "Aciertos Exactos"})

# ==========================================
# INTERFAZ DE USUARIO (SIDEBAR & MENÚ)
# ==========================================
st.sidebar.title("⚽ Mundial 2026")
menu = st.sidebar.radio("Navegación:", ["🏆 Ranking y Resultados", "📝 Mi Pronóstico", "⚙️ Panel de Admin"])

st.sidebar.markdown("---")
st.sidebar.info("💡 **Reglas:**\n- Resultado exacto: **3 pts**\n- Acertar ganador/empate: **1 pt**")

# Definición de columnas
cols_pronosticos = ["Usuario", "Partido", "Goles_Local", "Goles_Visita"]
cols_resultados = ["Partido", "Goles_Local", "Goles_Visita"]

# Cargar datos al vuelo
df_pron = load_data("Pronosticos", cols_pronosticos)
df_res = load_data("Resultados", cols_resultados)

# ==========================================
# PANTALLA 1: RANKING Y RESULTADOS
# ==========================================
if menu == "🏆 Ranking y Resultados":
    st.title("🏆 Tabla de Posiciones Global")
    st.markdown("¡Revisa quién lidera la Polla Mundialista!")
    
    ranking_df = calcular_ranking(df_pron, df_res)
    
    if not ranking_df.empty:
        # Top 3 en métricas dinámicas
        col1, col2, col3 = st.columns(3)
        with col2:
            st.metric(label="🥇 1er Lugar", value=f"{ranking_df.iloc[0]['Usuario']}", delta=f"{ranking_df.iloc[0]['Puntos']} pts", delta_color="normal")
        if len(ranking_df) > 1:
            with col1:
                st.metric(label="🥈 2do Lugar", value=f"{ranking_df.iloc[1]['Usuario']}", delta=f"{ranking_df.iloc[1]['Puntos']} pts", delta_color="off")
        if len(ranking_df) > 2:
            with col3:
                st.metric(label="🥉 3er Lugar", value=f"{ranking_df.iloc[2]['Usuario']}", delta=f"{ranking_df.iloc[2]['Puntos']} pts", delta_color="off")
        
        st.markdown("### 📊 Clasificación Completa")
        st.dataframe(ranking_df, use_container_width=True)
    else:
        st.warning("Aún no hay resultados oficiales o pronósticos procesados para generar el ranking.")

    st.markdown("---")
    st.markdown("### 🏟️ Resultados Oficiales (Histórico)")
    if not df_res.empty:
        st.dataframe(df_res, use_container_width=True)
    else:
        st.info("El administrador aún no ingresa resultados oficiales.")

# ==========================================
# PANTALLA 2: INGRESAR PRONÓSTICO
# ==========================================
elif menu == "📝 Mi Pronóstico":
    st.title("📝 Ingresa tus Predicciones")
    st.markdown("Asegúrate de usar siempre el **mismo nombre de usuario** para que tus puntos se sumen correctamente. Si vuelves a pronosticar un partido, **se sobreescribirá** tu apuesta anterior.")
    
    with st.form("form_pronostico", clear_on_submit=False):
        usuario = st.text_input("👤 Tu Nombre o Apodo:", placeholder="Ej: JuanPerez99")
        partido = st.selectbox("⚔️ Selecciona el Partido:", PARTIDOS)
        
        col1, col2 = st.columns(2)
        with col1:
            goles_local = st.number_input("⚽ Goles Equipo Local:", min_value=0, max_value=20, step=1, value=0)
        with col2:
            goles_visita = st.number_input("⚽ Goles Equipo Visita:", min_value=0, max_value=20, step=1, value=0)
            
        submit = st.form_submit_button("💾 Guardar Pronóstico", type="primary")
        
        if submit:
            if not usuario.strip():
                st.error("¡Por favor ingresa tu nombre de usuario!")
            else:
                nuevo_pron = pd.DataFrame([{
                    "Usuario": usuario.strip(),
                    "Partido": partido,
                    "Goles_Local": goles_local,
                    "Goles_Visita": goles_visita
                }])
                
                with st.spinner("Guardando en la base de datos..."):
                    # Se sobreescribe si es el mismo usuario y el mismo partido
                    save_data("Pronosticos", nuevo_pron, subset_drop=["Usuario", "Partido"])
                st.success(f"✅ ¡Pronóstico guardado exitosamente para {usuario}!")
                st.balloons()

# ==========================================
# PANTALLA 3: PANEL DE ADMINISTRADOR
# ==========================================
elif menu == "⚙️ Panel de Admin":
    st.title("⚙️ Panel de Control - Organizador")
    st.markdown("Esta sección es **exclusiva** para cargar los resultados reales de los partidos.")
    
    # Sistema de seguridad simple
    if "admin_auth" not in st.session_state:
        st.session_state["admin_auth"] = False

    if not st.session_state["admin_auth"]:
        pwd = st.text_input("🔑 Contraseña de Administrador:", type="password")
        if st.button("Ingresar"):
            if pwd == "Mundial2026!":
                st.session_state["admin_auth"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
    else:
        st.success("✅ Autenticado como Administrador")
        if st.button("Cerrar Sesión"):
            st.session_state["admin_auth"] = False
            st.rerun()
            
        st.markdown("### 📥 Ingresar Resultado Oficial")
        with st.form("form_resultados"):
            partido_res = st.selectbox("⚔️ Partido Finalizado:", PARTIDOS)
            
            col1, col2 = st.columns(2)
            with col1:
                g_local_res = st.number_input("⚽ Goles Reales Local:", min_value=0, max_value=20, step=1, value=0)
            with col2:
                g_visita_res = st.number_input("⚽ Goles Reales Visita:", min_value=0, max_value=20, step=1, value=0)
                
            submit_res = st.form_submit_button("🚨 Confirmar Resultado Oficial", type="primary")
            
            if submit_res:
                nuevo_res = pd.DataFrame([{
                    "Partido": partido_res,
                    "Goles_Local": g_local_res,
                    "Goles_Visita": g_visita_res
                }])
                
                with st.spinner("Actualizando sistema..."):
                    # Si el admin se equivoca y vuelve a ingresar un partido, se sobreescribe el anterior
                    save_data("Resultados", nuevo_res, subset_drop=["Partido"])
                st.success(f"✅ ¡Resultado de {partido_res} subido! El ranking ha sido actualizado.")
