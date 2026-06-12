import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURACIÓN BÁSICA
# ==========================================
st.set_page_config(page_title="BANBET | Mundial 2026", page_icon="⚽", layout="centered")
ZONA_HORARIA = pytz.timezone('America/Santiago')

# ==========================================
# 2. BASE DE DATOS LOCAL (USUARIOS Y PARTIDOS)
# ==========================================
# Lista de 18 cupos (Puedes agregar el resto después)
USUARIOS = [
    "Selecciona tu nombre...", 
    "Joseph Bautista", 
    "Daniela", 
    "Yeison", 
    "Pato", 
    "Milcka", 
    "Jugador 7", 
    "Jugador 8"
]

# Base de partidos de prueba. 
# ATENCIÓN: Formato de fecha "YYYY-MM-DD HH:MM"
PARTIDOS = [
    {
        "id": "P1", 
        "local": "México 🇲🇽", 
        "visita": "🇵🇱 Polonia", 
        "fecha_hora": "2026-06-11 10:00" # Partido en el pasado (Bloqueado)
    },
    {
        "id": "P2", 
        "local": "USA 🇺🇸", 
        "visita": "🏴󠁧󠁢󠁷󠁬󠁳󠁿 Gales", 
        "fecha_hora": "2026-06-12 20:00" # Partido a futuro cercano
    },
    {
        "id": "P3", 
        "local": "Argentina 🇦🇷", 
        "visita": "🇫🇷 Francia", 
        "fecha_hora": "2026-06-15 16:00" # Partido en el futuro
    }
]

# ==========================================
# 3. CONEXIÓN A GOOGLE SHEETS (BLINDADA)
# ==========================================
def obtener_datos(hoja, columnas):
    """Obtiene datos de GSheets. Si hay error o está vacía, devuelve estructura limpia."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=hoja, ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=columnas)
        return df.dropna(how="all")
    except Exception:
        # Modo a prueba de fallos: Si GSheets falla, la app no se cae
        return pd.DataFrame(columns=columnas)

def guardar_apuesta(usuario, id_partido, g_local, g_visita):
    """Guarda o actualiza la apuesta del usuario en GSheets."""
    conn = st.connection("gsheets", type=GSheetsConnection)
    ahora = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")
    nueva_fila = pd.DataFrame([{
        "Timestamp": ahora,
        "Usuario": usuario,
        "ID_Partido": id_partido,
        "Goles_Local": g_local,
        "Goles_Visita": g_visita
    }])
    
    try:
        df_existente = conn.read(worksheet="Apuestas", ttl=0)
        if df_existente is None or df_existente.empty:
            df_existente = pd.DataFrame(columns=["Timestamp", "Usuario", "ID_Partido", "Goles_Local", "Goles_Visita"])
        else:
            df_existente = df_existente.dropna(how="all")
            
        # Unir y dejar solo la última apuesta de ese usuario para ese partido
        df_actualizado = pd.concat([df_existente, nueva_fila], ignore_index=True)
        df_actualizado = df_actualizado.drop_duplicates(subset=["Usuario", "ID_Partido"], keep='last')
        
        conn.update(worksheet="Apuestas", data=df_actualizado)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return False

# ==========================================
# 4. LÓGICA DE PUNTOS
# ==========================================
def calcular_puntos(g_loc_apuesta, g_vis_apuesta, g_loc_real, g_vis_real):
    """Retorna 3 (Exacto), 1 (Tendencia) o 0 (Fallo)."""
    try:
        gl_a, gv_a = int(g_loc_apuesta), int(g_vis_apuesta)
        gl_r, gv_r = int(g_loc_real), int(g_vis_real)
        
        if gl_a == gl_r and gv_a == gv_r:
            return 3
        elif (gl_a > gv_a and gl_r > gv_r) or (gl_a < gv_a and gl_r < gv_r) or (gl_a == gv_a and gl_r == gv_r):
            return 1
        return 0
    except ValueError:
        return 0

# ==========================================
# 5. INTERFAZ PRINCIPAL BANBET
# ==========================================
st.title("📱 BANBET")
st.markdown("Plataforma Oficial de Pronósticos | **Las apuestas se cierran al iniciar el partido.**")

# Cargar bases de datos
df_apuestas = obtener_datos("Apuestas", ["Timestamp", "Usuario", "ID_Partido", "Goles_Local", "Goles_Visita"])
df_resultados = obtener_datos("Resultados", ["ID_Partido", "Goles_Local", "Goles_Visita"])

# 1. Selector de Usuario (Filtro Global)
usuario_actual = st.selectbox("👤 ¿Quién eres?", USUARIOS)

if usuario_actual == "Selecciona tu nombre...":
    st.info("👈 Por favor, selecciona tu nombre para ver tus partidos.")
else:
    st.success(f"Bienvenido/a, **{usuario_actual}**")
    
    # Filtrar solo las apuestas de este usuario
    mis_apuestas = df_apuestas[df_apuestas["Usuario"] == usuario_actual] if not df_apuestas.empty else pd.DataFrame()
    
    # Evaluar la hora actual
    ahora_dt = datetime.now(ZONA_HORARIA)
    
    # Separar partidos en Futuros y Pasados
    partidos_futuros = []
    partidos_pasados = []
    
    for p in PARTIDOS:
        fecha_partido = ZONA_HORARIA.localize(datetime.strptime(p["fecha_hora"], "%Y-%m-%d %H:%M"))
        if ahora_dt < fecha_partido:
            partidos_futuros.append(p)
        else:
            partidos_pasados.append(p)

    # 2. Pestañas de Navegación
    tab_futuros, tab_pasados = st.tabs(["🔮 Partidos Disponibles (Para Apostar)", "📜 Mi Historial (Partidos Pasados)"])
    
    # ==========================================
    # PESTAÑA 1: FUTUROS (APUESTAS ABIERTAS)
    # ==========================================
    with tab_futuros:
        if not partidos_futuros:
            st.success("No hay partidos próximos disponibles por ahora.")
            
        for p in partidos_futuros:
            st.markdown(f"### {p['local']} vs {p['visita']}")
            
            # Formatear fecha para mostrarla amigable
            fecha_obj = datetime.strptime(p["fecha_hora"], "%Y-%m-%d %H:%M")
            st.caption(f"🗓️ Cierre de apuestas: {fecha_obj.strftime('%d/%m/%Y a las %H:%M')} hrs")
            
            # Buscar si el usuario ya apostó a este partido
            apuesta_previa = mis_apuestas[mis_apuestas["ID_Partido"] == p["id"]]
            g_loc_previo = int(apuesta_previa["Goles_Local"].iloc[0]) if not apuesta_previa.empty else 0
            g_vis_previo = int(apuesta_previa["Goles_Visita"].iloc[0]) if not apuesta_previa.empty else 0
            
            if not apuesta_previa.empty:
                st.info("✅ Ya tienes una apuesta registrada. Puedes modificarla si lo deseas.")
            
            # Formulario único por partido
            with st.form(key=f"form_{p['id']}"):
                col1, col2 = st.columns(2)
                with col1:
                    gl = st.number_input(f"Goles {p['local']}", min_value=0, max_value=20, step=1, value=g_loc_previo, key=f"loc_{p['id']}")
                with col2:
                    gv = st.number_input(f"Goles {p['visita']}", min_value=0, max_value=20, step=1, value=g_vis_previo, key=f"vis_{p['id']}")
                
                enviar = st.form_submit_button("💾 Guardar Apuesta", type="primary")
                
                if enviar:
                    with st.spinner("Guardando en BANBET..."):
                        if guardar_apuesta(usuario_actual, p["id"], gl, gv):
                            st.success("¡Apuesta confirmada!")
                            st.rerun()
            st.divider()

    # ==========================================
    # PESTAÑA 2: PASADOS (HISTORIAL Y RESULTADOS)
    # ==========================================
    with tab_pasados:
        if not partidos_pasados:
            st.info("Aún no hay partidos finalizados.")
            
        for p in partidos_pasados:
            st.markdown(f"### 🔒 {p['local']} vs {p['visita']}")
            st.caption("Partido finalizado - Apuestas cerradas")
            
            # 1. Buscar la apuesta del usuario
            apuesta = mis_apuestas[mis_apuestas["ID_Partido"] == p["id"]]
            texto_apuesta = "No apostaste (Asignado 0-0)"
            g_loc_a, g_vis_a = 0, 0
            
            if not apuesta.empty:
                g_loc_a = apuesta["Goles_Local"].iloc[0]
                g_vis_a = apuesta["Goles_Visita"].iloc[0]
                texto_apuesta = f"{g_loc_a} - {g_vis_a}"

            # 2. Buscar el resultado oficial
            resultado = df_resultados[df_resultados["ID_Partido"] == p["id"]] if not df_resultados.empty else pd.DataFrame()
            
            if resultado.empty:
                # El partido ya empezó/terminó, pero el Admin aún no sube el resultado
                st.warning(f"⏳ Tu apuesta fue: **{texto_apuesta}**. Esperando resultado oficial.")
            else:
                # Ya hay resultado oficial
                g_loc_r = resultado["Goles_Local"].iloc[0]
                g_vis_r = resultado["Goles_Visita"].iloc[0]
                
                puntos = calcular_puntos(g_loc_a, g_vis_a, g_loc_r, g_vis_r)
                
                # Mostrar tarjetas de resumen
                c1, c2, c3 = st.columns(3)
                c1.metric("Tu Apuesta", texto_apuesta)
                c2.metric("Resultado Real", f"{g_loc_r} - {g_vis_r}")
                c3.metric("Puntos Obtenidos", f"+{puntos} pts")
                
            st.divider()
