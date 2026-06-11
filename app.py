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

# ==========================================
# BASE DE DATOS LOCAL DE PARTIDOS
# ==========================================
# Aquí puedes agregar los 104 partidos. Te dejo la estructura lista con algunos reales/simulados.
PARTIDOS_DATA = [
    {"id": "1", "fase": "Grupo A", "local": "México", "visita": "Polonia", "bandera_L": "🇲🇽", "bandera_V": "🇵🇱", "sede": "Estadio Azteca, CDMX", "fecha": "11 Jun"},
    {"id": "2", "fase": "Grupo B", "local": "Canadá", "visita": "Marruecos", "bandera_L": "🇨🇦", "bandera_V": "🇲🇦", "sede": "BMO Field, Toronto", "fecha": "12 Jun"},
    {"id": "3", "fase": "Grupo C", "local": "USA", "visita": "Gales", "bandera_L": "🇺🇸", "bandera_V": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "sede": "SoFi Stadium, LA", "fecha": "12 Jun"},
    {"id": "4", "fase": "Grupo D", "local": "Argentina", "visita": "Francia", "bandera_L": "🇦🇷", "bandera_V": "🇫🇷", "sede": "MetLife Stadium, NY/NJ", "fecha": "13 Jun"},
    {"id": "5", "fase": "Grupo E", "local": "Chile", "visita": "Uruguay", "bandera_L": "🇨🇱", "bandera_V": "🇺🇾", "sede": "Hard Rock Stadium, Miami", "fecha": "14 Jun"},
    {"id": "6", "fase": "Grupo F", "local": "Brasil", "visita": "Inglaterra", "bandera_L": "🇧🇷", "bandera_V": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "sede": "AT&T Stadium, Dallas", "fecha": "15 Jun"},
]

# Formatear la lista para el menú desplegable
OPCIONES_PARTIDOS = [
    f"{p['bandera_L']} {p['local']} vs {p['visita']} {p['bandera_V']} | {p['fase']} | 📍 {p['sede']} ({p['fecha']})"
    for p in PARTIDOS_DATA
]

# ==========================================
# FUNCIONES DE BASE DE DATOS (GSHEETS)
# ==========================================
def load_data(sheet_name, columns):
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df = conn.read(worksheet=sheet_name, ttl=0) 
        if df.empty:
            return pd.DataFrame(columns=columns)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame(columns=columns)

def save_data(sheet_name, new_data_df, subset_drop):
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        existing_data = conn.read(worksheet=sheet_name, ttl=0).dropna(how="all")
    except Exception:
        existing_data = pd.DataFrame(columns=new_data_df.columns)
        
    updated_data = pd.concat([existing_data, new_data_df], ignore_index=True)
    updated_data = updated_data.drop_duplicates(subset=subset_drop, keep='last')
    conn.update(worksheet=sheet_name, data=updated_data)
    st.cache_data.clear()

# ==========================================
# MOTOR DE PUNTOS
# ==========================================
def calcular_ranking(df_pronosticos, df_resultados):
    if df_pronosticos.empty or df_resultados.empty:
        return pd.DataFrame(columns=["Usuario", "Puntos", "Aciertos Exactos"])

    df = pd.merge(df_pronosticos, df_resultados, on="Partido", suffixes=('_P', '_R'))
    puntos, exactos = [], []

    for _, row in df.iterrows():
        try:
            gl_p, gv_p = int(row['Goles_Local_P']), int(row['Goles_Visita_P'])
            gl_r, gv_r = int(row['Goles_Local_R']), int(row['Goles_Visita_R'])
            
            if gl_p == gl_r and gv_p == gv_r:
                puntos.append(3)
                exactos.append(1)
            elif (gl_p > gv_p and gl_r > gv_r) or (gl_p < gv_p and gl_r < gv_r) or (gl_p == gv_p and gl_r == gv_r):
                puntos.append(1)
                exactos.append(0)
            else:
                puntos.append(0)
                exactos.append(0)
        except ValueError:
            puntos.append(0); exactos.append(0)

    df['Puntos'] = puntos
    df['Exactos'] = exactos
    
    ranking = df.groupby("Usuario").agg({'Puntos': 'sum', 'Exactos': 'sum'}).reset_index()
    ranking = ranking.sort_values(by=["Puntos", "Exactos"], ascending=[False, False]).reset_index(drop=True)
    ranking.index += 1 
    
    return ranking.rename(columns={"Exactos": "Aciertos Exactos"})

# ==========================================
# INTERFAZ DE USUARIO (SIDEBAR & MENÚ)
# ==========================================
st.sidebar.title("⚽ Mundial 2026")
menu = st.sidebar.radio("Navegación:", ["🏆 Ranking", "📝 Mi Pronóstico", "📊 Dashboard de Análisis", "⚙️ Panel de Admin"])

st.sidebar.markdown("---")
st.sidebar.info("💡 **Reglas:**\n- Resultado exacto: **3 pts**\n- Acertar ganador/empate: **1 pt**")

cols_pronosticos = ["Usuario", "Partido", "Goles_Local", "Goles_Visita"]
cols_resultados = ["Partido", "Goles_Local", "Goles_Visita"]

df_pron = load_data("Pronosticos", cols_pronosticos)
df_res = load_data("Resultados", cols_resultados)

# ==========================================
# PANTALLA 1: RANKING
# ==========================================
if menu == "🏆 Ranking":
    st.title("🏆 Tabla de Posiciones Global")
    ranking_df = calcular_ranking(df_pron, df_res)
    
    if not ranking_df.empty:
        col1, col2, col3 = st.columns(3)
        with col2: st.metric("🥇 1er Lugar", f"{ranking_df.iloc[0]['Usuario']}", f"{ranking_df.iloc[0]['Puntos']} pts")
        if len(ranking_df) > 1:
            with col1: st.metric("🥈 2do Lugar", f"{ranking_df.iloc[1]['Usuario']}", f"{ranking_df.iloc[1]['Puntos']} pts", delta_color="off")
        if len(ranking_df) > 2:
            with col3: st.metric("🥉 3er Lugar", f"{ranking_df.iloc[2]['Usuario']}", f"{ranking_df.iloc[2]['Puntos']} pts", delta_color="off")
        
        st.dataframe(ranking_df, use_container_width=True)
    else:
        st.warning("Aún no hay puntos para mostrar.")

# ==========================================
# PANTALLA 2: PRONÓSTICOS
# ==========================================
elif menu == "📝 Mi Pronóstico":
    st.title("📝 Ingresa tus Predicciones")
    st.markdown("Busca el partido, analiza tu jugada y guarda tu pronóstico.")
    
    with st.form("form_pronostico", clear_on_submit=False):
        usuario = st.text_input("👤 Tu Nombre o Apodo:", placeholder="Ej: JuanPerez99")
        partido_seleccionado = st.selectbox("⚔️ Selecciona el Partido:", OPCIONES_PARTIDOS)
        
        # Extraemos solo los nombres de los equipos para la interfaz visual
        equipos = partido_seleccionado.split('|')[0].strip()
        local, visita = equipos.split(' vs ')
        
        st.markdown(f"### 🏟️ {local} 🆚 {visita}")
        
        col1, col2 = st.columns(2)
        with col1:
            goles_local = st.number_input(f"Goles {local}:", min_value=0, max_value=20, step=1, value=0)
        with col2:
            goles_visita = st.number_input(f"Goles {visita}:", min_value=0, max_value=20, step=1, value=0)
            
        submit = st.form_submit_button("💾 Guardar Pronóstico", type="primary")
        
        if submit:
            if not usuario.strip():
                st.error("¡Por favor ingresa tu nombre de usuario!")
            else:
                nuevo_pron = pd.DataFrame([{
                    "Usuario": usuario.strip(),
                    "Partido": partido_seleccionado,  # Guardamos el string completo como ID único
                    "Goles_Local": goles_local,
                    "Goles_Visita": goles_visita
                }])
                with st.spinner("Guardando en la base de datos..."):
                    save_data("Pronosticos", nuevo_pron, subset_drop=["Usuario", "Partido"])
                st.success(f"✅ ¡Anotado para {usuario}!")
                st.balloons()

# ==========================================
# PANTALLA 3: DASHBOARD (NUEVO)
# ==========================================
elif menu == "📊 Dashboard de Análisis":
    st.title("📊 Estadísticas de la Comunidad")
    st.markdown("Analiza la tendencia de los pronósticos con estos KPIs generados en tiempo real.")
    
    if not df_pron.empty:
        total_pronosticos = len(df_pron)
        promedio_goles = (pd.to_numeric(df_pron['Goles_Local']).sum() + pd.to_numeric(df_pron['Goles_Visita']).sum()) / total_pronosticos if total_pronosticos > 0 else 0
        partido_mas_votado = df_pron['Partido'].value_counts().idxmax() if not df_pron.empty else "N/A"
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Apuestas", total_pronosticos)
        c2.metric("Promedio de Goles x Partido", round(promedio_goles, 1))
        
        # Extraer nombre corto del partido más votado
        nombre_corto = partido_mas_votado.split('|')[0].strip() if partido_mas_votado != "N/A" else "N/A"
        c3.metric("Partido Más Votado", nombre_corto)
        
        st.markdown("### 📈 Tendencia de Partidos")
        conteo_partidos = df_pron['Partido'].value_counts().reset_index()
        conteo_partidos.columns = ['Partido', 'Cantidad de Pronósticos']
        conteo_partidos['Partido'] = conteo_partidos['Partido'].apply(lambda x: x.split('|')[0].strip())
        st.bar_chart(conteo_partidos.set_index('Partido'))
    else:
        st.info("Necesitamos que los usuarios comiencen a ingresar pronósticos para generar las gráficas.")

# ==========================================
# PANTALLA 4: PANEL DE ADMIN
# ==========================================
elif menu == "⚙️ Panel de Admin":
    st.title("⚙️ Panel de Control")
    if "admin_auth" not in st.session_state:
        st.session_state["admin_auth"] = False

    if not st.session_state["admin_auth"]:
        pwd = st.text_input("🔑 Contraseña:", type="password")
        if st.button("Ingresar"):
            if pwd == "Mundial2026!":
                st.session_state["admin_auth"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
    else:
        st.success("✅ Autenticado")
        if st.button("Cerrar Sesión"):
            st.session_state["admin_auth"] = False
            st.rerun()
            
        with st.form("form_resultados"):
            partido_res = st.selectbox("⚔️ Partido Finalizado:", OPCIONES_PARTIDOS)
            equipos = partido_res.split('|')[0].strip()
            
            st.markdown(f"**Resultado oficial para:** {equipos}")
            c1, c2 = st.columns(2)
            with c1: g_local_res = st.number_input("⚽ Goles Reales Local:", min_value=0, max_value=20, step=1, value=0)
            with c2: g_visita_res = st.number_input("⚽ Goles Reales Visita:", min_value=0, max_value=20, step=1, value=0)
                
            if st.form_submit_button("🚨 Confirmar Resultado", type="primary"):
                nuevo_res = pd.DataFrame([{"Partido": partido_res, "Goles_Local": g_local_res, "Goles_Visita": g_visita_res}])
                save_data("Resultados", nuevo_res, subset_drop=["Partido"])
                st.success("✅ ¡Resultado guardado!")
