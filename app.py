import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURACIÓN BÁSICA Y NUEVO DISEÑO UI
# ==========================================
st.set_page_config(page_title="BANBET | Mundial 2026", page_icon="🏆", layout="centered")
ZONA_HORARIA = pytz.timezone('America/Santiago')

# Nuevo banner visual más mundialero y colorido
st.markdown("""
    <style>
    .banner-mundial {
        background: linear-gradient(135deg, #004d98 0%, #00a94f 50%, #fcd116 100%);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .titulo-principal {
        color: white;
        font-size: 3.2rem;
        font-weight: 900;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    .subtitulo {
        color: #f8f9fa;
        font-size: 1.2rem;
        font-weight: 500;
        margin: 5px 0 0 0;
    }
    </style>
    <div class="banner-mundial">
        <h1 class="titulo-principal">🏆 BANBET 2026 ⚽</h1>
        <p class="subtitulo">Quiniela Oficial BanGlobal</p>
    </div>
""", unsafe_allow_html=True)

# Barra lateral limpia, reservada para futuras gráficas
with st.sidebar:
    st.markdown("### 📊 Panel de Análisis")
    st.info("Próximamente: Gráficas de rendimiento, estadísticas de la oficina y tabla de líderes.")

# ==========================================
# 2. BASE DE DATOS LOCAL (USUARIOS Y PARTIDOS)
# ==========================================
USUARIOS = [
    "Selecciona tu nombre...",
    "Alisson", "Bernarda", "Carlos", "Claudio", "Costanzo", "Cristian",
    "Daniela", "David", "Emanuel", "Isidora", "Joseph", "Marco",
    "Miguel", "Milcka", "Nayadeth", "Nicol", "Patricio", "Rodrigo"
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

COLS_APUESTAS = ["Timestamp", "Usuario", "ID_Partido", "Equipo_Local", "Equipo_Visita", "Fecha", "Goles_Local", "Goles_Visita"]
COLS_RESULTADOS = ["ID_Partido", "Equipo_Local", "Equipo_Visita", "Fecha", "Goles_Local", "Goles_Visita"]

# ==========================================
# 3. CAPA DE DATOS AUTO-REPARABLE
# ==========================================
def obtener_datos(hoja, columnas):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=hoja, ttl=0)
        
        if df is None or df.empty or str(df.columns[0]).startswith("Unnamed"):
            return pd.DataFrame(columns=columnas)
            
        for col in columnas:
            if col not in df.columns:
                df[col] = None
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame(columns=columnas)

def guardar_datos_seguro(hoja, df_nuevo):
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
# 5. GESTOR DE SESIÓN (PSEUDO-LOGIN)
# ==========================================
if "usuario_activo" not in st.session_state:
    st.session_state.usuario_activo = None

# Vista de "Login"
if st.session_state.usuario_activo is None:
    st.markdown("### 🔐 Ingresa a tu cuenta")
    seleccion = st.selectbox("Busca tu nombre en la lista:", USUARIOS)
    
    if st.button("Entrar a BANBET", type="primary", use_container_width=True):
        if seleccion != "Selecciona tu nombre...":
            st.session_state.usuario_activo = seleccion
            st.rerun() # Recarga la app y entra al sistema
        else:
            st.error("⚠️ Debes seleccionar un nombre válido para continuar.")
    st.stop() # Detiene la ejecución para que no vean nada más hasta "loguearse"

# ==========================================
# 6. MOTOR DE INTERFAZ (VISTA CONECTADA)
# ==========================================
# Si el código llega aquí, es porque el usuario ya ingresó correctamente
usuario_actual = st.session_state.usuario_activo

col1, col2 = st.columns([3, 1])
with col1:
    st.success(f"👤 Jugador Activo: **{usuario_actual}**")
with col2:
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state.usuario_activo = None
        st.rerun()

df_apuestas = obtener_datos("Apuestas", COLS_APUESTAS)
df_resultados = obtener_datos("Resultados", COLS_RESULTADOS)

mis_apuestas = df_apuestas[df_apuestas["Usuario"] == usuario_actual] if not df_apuestas.empty else pd.DataFrame(columns=COLS_APUESTAS)
ahora_dt = datetime.now(ZONA_HORARIA)

partidos_futuros, partidos_pasados = [], []

for p in PARTIDOS:
    fecha_partido = ZONA_HORARIA.localize(datetime.strptime(p["fecha_hora"], "%Y-%m-%d %H:%M"))
    if ahora_dt < fecha_partido:
        partidos_futuros.append(p)
    else:
        partidos_pasados.append(p)

tab_futuros, tab_pasados = st.tabs(["🔮 CARTILLAS ABIERTAS", "📜 HISTORIAL Y RESULTADOS"])

# ------------------------------------------
# PESTAÑA: APUESTAS ABIERTAS
# ------------------------------------------
with tab_futuros:
    if not partidos_futuros:
        st.success("🎉 ¡Has completado todos tus pronósticos! No hay partidos próximos por ahora.")
        
    for p in partidos_futuros:
        with st.container():
            st.markdown(f"### {p['local']} vs {p['visita']}")
            fecha_obj = datetime.strptime(p["fecha_hora"], "%Y-%m-%d %H:%M")
            st.caption(f"⏱️ Cierre de apuestas: **{fecha_obj.strftime('%d/%m/%Y')}** a las **{fecha_obj.strftime('%H:%M')} hrs**.")
            
            g_loc_previo, g_vis_previo = 0, 0
            if not mis_apuestas.empty:
                apuesta_previa = mis_apuestas[mis_apuestas["ID_Partido"] == p["id"]]
                if not apuesta_previa.empty:
                    try:
                        g_loc_previo = int(apuesta_previa["Goles_Local"].iloc[0])
                        g_vis_previo = int(apuesta_previa["Goles_Visita"].iloc[0])
                        st.info(f"✅ Tu jugada guardada: **{g_loc_previo} - {g_vis_previo}**")
                    except Exception:
                        pass
            
            with st.form(key=f"form_{p['id']}_{usuario_actual}"):
                c1, c2 = st.columns(2)
                with c1:
                    gl = st.number_input(f"Marcador {p['local'].split(' ')[0]}", min_value=0, max_value=20, step=1, value=g_loc_previo, key=f"loc_{p['id']}_{usuario_actual}")
                with c2:
                    gv = st.number_input(f"Marcador {p['visita'].split(' ')[0]}", min_value=0, max_value=20, step=1, value=g_vis_previo, key=f"vis_{p['id']}_{usuario_actual}")
                
                if st.form_submit_button("💾 Guardar Pronóstico", type="primary"):
                    with st.spinner("Sincronizando con BANBET..."):
                        ahora_str = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")
                        
                        nueva_apuesta = pd.DataFrame([{
                            "Timestamp": ahora_str, 
                            "Usuario": usuario_actual, 
                            "ID_Partido": p["id"], 
                            "Equipo_Local": p["local"],
                            "Equipo_Visita": p["visita"],
                            "Fecha": p["fecha_hora"],
                            "Goles_Local": gl, 
                            "Goles_Visita": gv
                        }])
                        
                        df_base = df_apuestas if not df_apuestas.empty else pd.DataFrame(columns=COLS_APUESTAS)
                        df_final = pd.concat([df_base, nueva_apuesta], ignore_index=True)
                        df_final = df_final.drop_duplicates(subset=["Usuario", "ID_Partido"], keep='last')
                        
                        if guardar_datos_seguro("Apuestas", df_final):
                            st.success("¡Transacción registrada con éxito!")
                            st.rerun()
            st.write("---")

# ------------------------------------------
# PESTAÑA: HISTORIAL
# ------------------------------------------
with tab_pasados:
    if not partidos_pasados:
        st.info("Aún no se ha jugado ningún partido.")
        
    for p in partidos_pasados:
        st.markdown(f"#### 🔒 {p['local']} vs {p['visita']}")
        
        texto_apuesta = "Ausente (0-0)"
        g_loc_a, g_vis_a = 0, 0
        
        if not mis_apuestas.empty:
            apuesta = mis_apuestas[mis_apuestas["ID_Partido"] == p["id"]]
            if not apuesta.empty:
                g_loc_a = int(apuesta["Goles_Local"].iloc[0])
                g_vis_a = int(apuesta["Goles_Visita"].iloc[0])
                texto_apuesta = f"{g_loc_a} - {g_vis_a}"

        resultado = df_resultados[df_resultados["ID_Partido"] == p["id"]] if not df_resultados.empty else pd.DataFrame()
        
        if resultado.empty:
            st.warning(f"⏳ Tu jugada: **{texto_apuesta}**. Pendiente de validación oficial.")
        else:
            g_loc_r = int(resultado["Goles_Local"].iloc[0])
            g_vis_r = int(resultado["Goles_Visita"].iloc[0])
            puntos = calcular_puntos(g_loc_a, g_vis_a, g_loc_r, g_vis_r)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Tu Jugada", texto_apuesta)
            c2.metric("Marcador Final", f"{g_loc_r} - {g_vis_r}")
            c3.metric("Puntos", f"+{puntos}")
        st.write("---")
