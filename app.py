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
    "Alisson",
    "Bernarda",
    "Carlos",
    "Claudio",
    "Costanzo",
    "Cristian",
    "Daniela",
    "David",
    "Emanuel",
    "Isidora",
    "Joseph",
    "Marco",
    "Miguel",
    "Milcka",
    "Nayadeth",
    "Nicol",
    "Patricio",
    "Rodrigo"
]

PARTIDOS = [
    {"id": "P1", "local": "México 🇲🇽", "visita": "Sudáfrica 🇿🇦", "fecha_hora": "2026-06-11 15:00"},
    {"id": "P2", "local": "Corea del Sur 🇰🇷", "visita": "República Checa 🇨🇿", "fecha_hora": "2026-06-11 22:00"},
    {"id": "P3", "local": "Canadá 🇨🇦", "visita": "Bosnia y Herzegovina 🇧🇦", "fecha_hora": "2026-06-12 15:00"},
    {"id": "P4", "local": "Estados Unidos 🇺🇸", "visita": "Paraguay 🇵🇾", "fecha_hora": "2026-06-12 21:00"},
    {"id": "P5", "local": "Catar 🇶🇦", "visita": "Suiza 🇨🇭", "fecha_hora": "2026-06-13 15:00"},
    {"id": "P6", "local": "Brasil 🇧🇷", "visita": "Marruecos 🇲🇦", "fecha_hora": "2026-06-13 18:00"},
    {"id": "P7", "local": "Haití 🇭🇹", "visita": "Escocia 🏴󠁧󠁢󠁳󠁣󠁴󠁿", "fecha_hora": "2026-06-13 21:00"},
    {"id": "P8", "local": "Australia 🇦🇺", "visita": "Turquía 🇹🇷", "fecha_hora": "2026-06-14 00:00"},
    {"id": "P9", "local": "Alemania 🇩🇪", "visita": "Curazao 🇨🇼", "fecha_hora": "2026-06-14 13:00"},
    {"id": "P10", "local": "Países Bajos 🇳🇱", "visita": "Japón 🇯🇵", "fecha_hora": "2026-06-14 16:00"},
    {"id": "P11", "local": "Costa de Marfil 🇨🇮", "visita": "Ecuador 🇪🇨", "fecha_hora": "2026-06-14 19:00"},
    {"id": "P12", "local": "Suecia 🇸🇪", "visita": "Túnez 🇹🇳", "fecha_hora": "2026-06-14 22:00"},
    {"id": "P13", "local": "España 🇪🇸", "visita": "Cabo Verde 🇨🇻", "fecha_hora": "2026-06-15 12:00"},
    {"id": "P14", "local": "Bélgica 🇧🇪", "visita": "Egipto 🇪🇬", "fecha_hora": "2026-06-15 15:00"},
    {"id": "P15", "local": "Arabia Saudita 🇸🇦", "visita": "Uruguay 🇺🇾", "fecha_hora": "2026-06-15 18:00"},
    {"id": "P16", "local": "Irán 🇮🇷", "visita": "Nueva Zelanda 🇳🇿", "fecha_hora": "2026-06-15 21:00"},
    {"id": "P17", "local": "Francia 🇫🇷", "visita": "Senegal 🇸🇳", "fecha_hora": "2026-06-16 15:00"},
    {"id": "P18", "local": "Irak 🇮🇶", "visita": "Noruega 🇳🇴", "fecha_hora": "2026-06-16 18:00"},
    {"id": "P19", "local": "Argentina 🇦🇷", "visita": "Argelia 🇩🇿", "fecha_hora": "2026-06-16 21:00"},
    {"id": "P20", "local": "Austria 🇦🇹", "visita": "Jordania 🇯🇴", "fecha_hora": "2026-06-17 00:00"},
    {"id": "P21", "local": "Portugal 🇵🇹", "visita": "RD Congo 🇨🇩", "fecha_hora": "2026-06-17 13:00"},
    {"id": "P22", "local": "Inglaterra 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "visita": "Croacia 🇭🇷", "fecha_hora": "2026-06-17 16:00"},
    {"id": "P23", "local": "Ghana 🇬🇭", "visita": "Panama 🇵🇦", "fecha_hora": "2026-06-17 19:00"},
    {"id": "P24", "local": "Uzbekistán 🇺🇿", "visita": "Colombia 🇨🇴", "fecha_hora": "2026-06-17 22:00"}
]

COLS_APUESTAS = ["Timestamp", "Usuario", "ID_Partido", "Goles_Local", "Goles_Visita"]
COLS_RESULTADOS = ["ID_Partido", "Goles_Local", "Goles_Visita"]

# ==========================================
# 3. CAPA DE DATOS AUTO-REPARABLE
# ==========================================
def obtener_datos(hoja, columnas):
    """Intenta leer la hoja. Si da error 400 o está vacía, inicializa una tabla limpia con sus columnas."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=hoja, ttl=0)
        
        if df is None or df.empty or df.columns[0].startswith("Unnamed"):
            # Si la hoja está rota o vacía, le creamos la estructura base en memoria
            return pd.DataFrame(columns=columnas)
            
        # Verificar que todas las columnas requeridas existan
        for col in columnas:
            if col not in df.columns:
                df[col] = None
        return df.dropna(how="all")
    except Exception:
        # Si da Error 400 porque la pestaña está vacía, devolvemos el cascarón limpio
        return pd.DataFrame(columns=columnas)

def guardar_datos_seguro(hoja, df_nuevo):
    """Fuerza la escritura limpiando estructuras corruptas previas."""
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        conn.update(worksheet=hoja, data=df_nuevo)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error de escritura en GSheets ({hoja}): {e}")
        return False

# ==========================================
# 4. LÓGICA DE NEGOCIO
# ==========================================
def calcular_puntos(g_loc_apuesta, g_vis_apuesta, g_loc_real, g_vis_real):
    try:
        gl_a, gv_a = int(g_loc_apuesta), int(g_vis_apuesta)
        gl_r, gv_r = int(g_loc_real), int(g_vis_real)
        if gl_a == gl_r and gv_a == gv_r:
            return 3
        elif (gl_a > gv_a and gl_r > gv_r) or (gl_a < gv_a and gl_r < gv_r) or (gl_a == gv_a and gl_r == gv_r):
            return 1
        return 0
    except (ValueError, TypeError):
        return 0

# ==========================================
# 5. INTERFAZ DE USUARIO
# ==========================================
st.title("📱 BANBET")
st.markdown("Plataforma Oficial de Pronósticos | **Las apuestas se cierran al iniciar el partido.**")

# Cargar las tablas mitigando el Error 400
df_apuestas = obtener_datos("Apuestas", COLS_APUESTAS)
df_resultados = obtener_datos("Resultados", COLS_RESULTADOS)

usuario_actual = st.selectbox("👤 Selecciona tu perfil:", USUARIOS)

if usuario_actual == "Selecciona tu nombre...":
    st.info("👈 Por favor, selecciona tu nombre para acceder a la plataforma.")
else:
    st.success(f"Sesión iniciada como: **{usuario_actual}**")
    
    mis_apuestas = df_apuestas[df_apuestas["Usuario"] == usuario_actual] if not df_apuestas.empty else pd.DataFrame(columns=COLS_APUESTAS)
    ahora_dt = datetime.now(ZONA_HORARIA)
    
    partidos_futuros = []
    partidos_pasados = []
    for p in PARTIDOS:
        fecha_partido = ZONA_HORARIA.localize(datetime.strptime(p["fecha_hora"], "%Y-%m-%d %H:%M"))
        if ahora_dt < fecha_partido:
            partidos_futuros.append(p)
        else:
            partidos_pasados.append(p)

    tab_futuros, tab_pasados = st.tabs(["🔮 Pronósticos Abiertos", "📜 Mi Historial (Cerrados)"])
    
    # ------------------------------------------
    # PESTAÑA: APUESTAS ABIERTAS
    # ------------------------------------------
    with tab_futuros:
        if not partidos_futuros:
            st.success("No hay partidos próximos disponibles por ahora.")
            
        for p in partidos_futuros:
            st.markdown(f"### {p['local']} vs {p['visita']}")
            fecha_obj = datetime.strptime(p["fecha_hora"], "%Y-%m-%d %H:%M")
            st.caption(f"🗓️ Cierre: {fecha_obj.strftime('%d/%m/%Y a las %H:%M')} hrs")
            
            # Buscar apuestas previas de forma segura
            g_loc_previo, g_vis_previo = 0, 0
            if not mis_apuestas.empty:
                apuesta_previa = mis_apuestas[mis_apuestas["ID_Partido"] == p["id"]]
                if not apuesta_previa.empty:
                    try:
                        g_loc_previo = int(apuesta_previa["Goles_Local"].iloc[0])
                        g_vis_previo = int(apuesta_previa["Goles_Visita"].iloc[0])
                        st.info("✅ Ya ingresaste este pronóstico. Puedes modificarlo.")
                    except Exception:
                        pass
            
            with st.form(key=f"form_{p['id']}"):
                col1, col2 = st.columns(2)
                with col1:
                    gl = st.number_input(f"Goles {p['local']}", min_value=0, max_value=20, step=1, value=g_loc_previo, key=f"loc_{p['id']}")
                with col2:
                    gv = st.number_input(f"Goles {p['visita']}", min_value=0, max_value=20, step=1, value=g_vis_previo, key=f"vis_{p['id']}")
                
                if st.form_submit_button("💾 Guardar Apuesta", type="primary"):
                    with st.spinner("Sincronizando con la base de datos..."):
                        ahora_str = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")
                        nueva_apuesta = pd.DataFrame([{"Timestamp": ahora_str, "Usuario": usuario_actual, "ID_Partido": p["id"], "Goles_Local": gl, "Goles_Visita": gv}])
                        
                        # Combinar de forma segura reconstruyendo el DataFrame si es necesario
                        df_base = df_apuestas if not df_apuestas.empty else pd.DataFrame(columns=COLS_APUESTAS)
                        df_final = pd.concat([df_base, nueva_apuesta], ignore_index=True)
                        df_final = df_final.drop_duplicates(subset=["Usuario", "ID_Partido"], keep='last')
                        
                        if guardar_datos_seguro("Apuestas", df_final):
                            st.success("¡Apuesta guardada exitosamente!")
                            st.rerun()
            st.divider()

    # ------------------------------------------
    # PESTAÑA: HISTORIAL
    # ------------------------------------------
    with tab_pasados:
        if not partidos_pasados:
            st.info("Aún no hay partidos finalizados en tu historial.")
            
        for p in partidos_pasados:
            st.markdown(f"### 🔒 {p['local']} vs {p['visita']}")
            
            texto_apuesta = "No apostaste (Asignado 0-0)"
            g_loc_a, g_vis_a = 0, 0
            
            if not mis_apuestas.empty:
                apuesta = mis_apuestas[mis_apuestas["ID_Partido"] == p["id"]]
                if not apuesta.empty:
                    g_loc_a = int(apuesta["Goles_Local"].iloc[0])
                    g_vis_a = int(apuesta["Goles_Visita"].iloc[0])
                    texto_apuesta = f"{g_loc_a} - {g_vis_a}"

            resultado = df_resultados[df_resultados["ID_Partido"] == p["id"]] if not df_resultados.empty else pd.DataFrame()
            
            if resultado.empty:
                st.warning(f"⏳ Tu apuesta fue: **{texto_apuesta}**. Esperando resultado oficial.")
            else:
                g_loc_r = int(resultado["Goles_Local"].iloc[0])
                g_vis_r = int(resultado["Goles_Visita"].iloc[0])
                puntos = calcular_puntos(g_loc_a, g_vis_a, g_loc_r, g_vis_r)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Tu Apuesta", texto_apuesta)
                c2.metric("Resultado Real", f"{g_loc_r} - {g_vis_r}")
                c3.metric("Puntos Obtenidos", f"+{puntos} pts")
            st.divider()
