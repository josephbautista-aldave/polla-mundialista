import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURACIÓN BÁSICA
# ==========================================
st.set_page_config(page_title="BANBET | BanGlobal 2026", page_icon="⚽", layout="centered")
ZONA_HORARIA = pytz.timezone('America/Santiago')

# ==========================================
# 2. BASE DE DATOS LOCAL (USUARIOS Y PARTIDOS)
# ==========================================
USUARIOS = [
    "Selecciona tu nombre...", 
    "Joseph Angel Bautista", 
    "Daniela", 
    "Yeison", 
    "Pato", 
    "Milcka", 
    "Jugador Invitado 1", 
    "Jugador Invitado 2"
]

# Ajusté las fechas para que hoy puedas ver la diferencia entre pasados y futuros
PARTIDOS = [
    {
        "id": "P1", 
        "local": "México 🇲🇽", 
        "visita": "🇵🇱 Polonia", 
        "fecha_hora": "2026-06-11 10:00" # Ya se jugó
    },
    {
        "id": "P2", 
        "local": "Canadá 🇨🇦", 
        "visita": "🇲🇦 Marruecos", 
        "fecha_hora": "2026-06-12 10:00" # Ya se jugó hoy temprano
    },
    {
        "id": "P3", 
        "local": "USA 🇺🇸", 
        "visita": "🏴󠁧󠁢󠁷󠁬󠁳󠁿 Gales", 
        "fecha_hora": "2026-06-12 20:00" # Se juega hoy más tarde (Abierto)
    },
    {
        "id": "P4", 
        "local": "Argentina 🇦🇷", 
        "visita": "🇫🇷 Francia", 
        "fecha_hora": "2026-06-15 16:00" # Se juega en el futuro (Abierto)
    }
]

# ==========================================
# 3. CONEXIÓN A GOOGLE SHEETS (ANTI-KEYERROR)
# ==========================================
def obtener_datos(hoja, columnas):
    """Garantiza que el DataFrame siempre tenga las columnas correctas, aunque esté vacío."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=hoja, ttl=0)
        
        # Si la hoja está totalmente en blanco o no existe
        if df is None or df.empty:
            return pd.DataFrame(columns=columnas)
            
        # Forzar que las columnas existan por si la hoja no tiene encabezados
        for col in columnas:
            if col not in df.columns:
                df[col] = None
                
        return df.dropna(how="all")
    except Exception as e:
        st.error(f"⚠️ Error de lectura en la hoja {hoja}.")
        return pd.DataFrame(columns=columnas)

def guardar_apuesta(usuario, id_partido, g_local, g_visita):
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
            
        df_actualizado = pd.concat([df_existente, nueva_fila], ignore_index=True)
        df_actualizado = df_actualizado.drop_duplicates(subset=["Usuario", "ID_Partido"], keep='last')
        
        conn.update(worksheet="Apuestas", data=df_actualizado)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# ==========================================
# 4. LÓGICA DE PUNTOS
# ==========================================
def calcular_puntos(g_loc_apuesta, g_vis_apuesta, g_loc_real, g_vis_real):
    try:
        gl_a, gv_a = int(g_loc_apuesta), int(g_vis_apuesta)
        gl_r, gv_r = int(g_loc_real), int(g_vis_real)
        
        if gl_a == gl_r and gv_a == gv_r:
            return 3 # Exacto
        elif (gl_a > gv_a and gl_r > gv_r) or (gl_a < gv_a and gl_r < gv_r) or (gl_a == gv_a and gl_r == gv_r):
            return 1 # Tendencia
        return 0 # Fallo
    except (ValueError, TypeError):
        return 0

# ==========================================
# 5. INTERFAZ PRINCIPAL BANBET
# ==========================================
st.title("📱 BANBET")
st.markdown("Plataforma Oficial de Pronósticos | **Las apuestas se cierran al iniciar el partido.**")

# 1. Cargar bases de datos garantizando el esquema
cols_apuestas = ["Timestamp", "Usuario", "ID_Partido", "Goles_Local", "Goles_Visita"]
cols_resultados = ["ID_Partido", "Goles_Local", "Goles_Visita"]

df_apuestas = obtener_datos("Apuestas", cols_apuestas)
df_resultados = obtener_datos("Resultados", cols_resultados)

# 2. Selector de Usuario
usuario_actual = st.selectbox("👤 Selecciona tu perfil:", USUARIOS)

if usuario_actual == "Selecciona tu nombre...":
    st.info("👈 Por favor, selecciona tu nombre para acceder a la plataforma.")
else:
    st.success(f"Sesión iniciada como: **{usuario_actual}**")
    
    # 3. Filtrar datos del usuario (Asegurando que el DataFrame no pierda columnas)
    if not df_apuestas.empty:
        mis_apuestas = df_apuestas[df_apuestas["Usuario"] == usuario_actual]
    else:
        mis_apuestas = pd.DataFrame(columns=cols_apuestas)
    
    ahora_dt = datetime.now(ZONA_HORARIA)
    
    # 4. Separador Automático por Tiempo
    partidos_futuros = []
    partidos_pasados = []
    
    for p in PARTIDOS:
        fecha_partido = ZONA_HORARIA.localize(datetime.strptime(p["fecha_hora"], "%Y-%m-%d %H:%M"))
        if ahora_dt < fecha_partido:
            partidos_futuros.append(p)
        else:
            partidos_pasados.append(p)

    tab_futuros, tab_pasados = st.tabs(["🔮 Pronósticos Abiertos", "📜 Mi Historial (Cerrados)"])
    
    # ==========================================
    # PESTAÑA 1: FUTUROS (APUESTAS ABIERTAS)
    # ==========================================
    with tab_futuros:
        if not partidos_futuros:
            st.success("No hay partidos próximos disponibles por ahora.")
            
        for p in partidos_futuros:
            st.markdown(f"### {p['local']} vs {p['visita']}")
            
            fecha_obj = datetime.strptime(p["fecha_hora"], "%Y-%m-%d %H:%M")
            st.caption(f"🗓️ Cierre de apuestas: {fecha_obj.strftime('%d/%m/%Y a las %H:%M')} hrs")
            
            # Recuperar apuesta previa si existe
            apuesta_previa = mis_apuestas[mis_apuestas["ID_Partido"] == p["id"]]
            
            try:
                g_loc_previo = int(apuesta_previa["Goles_Local"].iloc[0]) if not apuesta_previa.empty else 0
                g_vis_previo = int(apuesta_previa["Goles_Visita"].iloc[0]) if not apuesta_previa.empty else 0
            except (ValueError, TypeError):
                g_loc_previo, g_vis_previo = 0, 0
            
            if not apuesta_previa.empty:
                st.info("✅ Ya ingresaste este pronóstico. Edítalo si cambiaste de opinión.")
            
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
    # PESTAÑA 2: PASADOS (HISTORIAL)
    # ==========================================
    with tab_pasados:
        if not partidos_pasados:
            st.info("Aún no hay partidos finalizados en tu historial.")
            
        for p in partidos_pasados:
            st.markdown(f"### 🔒 {p['local']} vs {p['visita']}")
            st.caption("Partido finalizado - Apuestas cerradas")
            
            apuesta = mis_apuestas[mis_apuestas["ID_Partido"] == p["id"]]
            texto_apuesta = "No apostaste (Asignado 0-0)"
            g_loc_a, g_vis_a = 0, 0
            
            if not apuesta.empty:
                try:
                    g_loc_a = int(apuesta["Goles_Local"].iloc[0])
                    g_vis_a = int(apuesta["Goles_Visita"].iloc[0])
                    texto_apuesta = f"{g_loc_a} - {g_vis_a}"
                except (ValueError, TypeError):
                    texto_apuesta = "Error en formato"

            resultado = df_resultados[df_resultados["ID_Partido"] == p["id"]] if not df_resultados.empty else pd.DataFrame()
            
            if resultado.empty:
                st.warning(f"⏳ Tu apuesta fue: **{texto_apuesta}**. Esperando resultado oficial del administrador.")
            else:
                try:
                    g_loc_r = int(resultado["Goles_Local"].iloc[0])
                    g_vis_r = int(resultado["Goles_Visita"].iloc[0])
                    puntos = calcular_puntos(g_loc_a, g_vis_a, g_loc_r, g_vis_r)
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Tu Apuesta", texto_apuesta)
                    c2.metric("Resultado Real", f"{g_loc_r} - {g_vis_r}")
                    c3.metric("Puntos Obtenidos", f"+{puntos} pts")
                except (ValueError, TypeError):
                    st.error("Error al leer el resultado oficial. Revisa que no haya letras en la hoja de Resultados.")
                
            st.divider()
