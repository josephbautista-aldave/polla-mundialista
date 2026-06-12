import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURACIÓN BÁSICA Y NUEVO DISEÑO UI
# ==========================================
st.set_page_config(page_title="BANBET Mundial 2026", page_icon="🌍", layout="centered")
ZONA_HORARIA = pytz.timezone('America/Santiago')

st.markdown("""
    <style>
    .banner-mundial {
        background: linear-gradient(135deg, #8A1538 0%, #004d98 50%, #00a94f 100%);
        padding: 30px 15px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        border: 2px solid #E3A126;
    }
    .titulo-principal {
        color: #FFFFFF !important;
        font-size: 3.5rem !important;
        font-weight: 900 !important;
        margin: 0;
        letter-spacing: 2px;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.9);
    }
    .subtitulo {
        color: #FCD116 !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        margin: 10px 0 0 0;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 1px 1px 4px rgba(0,0,0,0.8);
    }
    </style>
    <div class="banner-mundial">
        <h1 class="titulo-principal">🌍 BANBET 2026 🏆</h1>
        <p class="subtitulo">Pronósticos Oficiales BanGlobal</p>
    </div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; font-size: 4rem; margin-bottom: 5px;">
        🏟️⚽🎟️
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📋 Reglas del Juego")
    st.info("""
    📲 **1. Selecciona tu perfil:** Usa tu avatar de la matriz.
    ⏱️ **2. Apuesta a tiempo:** El sistema bloquea las cartillas al pitazo inicial de cada partido.
    """)
    
    st.markdown("### 🥇 Sistema de Puntos")
    st.success("""
    * 🎯 **PLENO (5 pts):** Adivinar marcador exacto.
    * 📈 **TENDENCIA (3 pts):** Acertar ganador/empate pero fallar en goles.
    * ❌ **FALLO (0 pts):** Errar el pronóstico.
    """)
    
    st.markdown("---")
    st.markdown("### 📊 Próximamente")
    st.warning("📈 **Dashboard de Líderes:** Las gráficas de rendimiento y tabla de posiciones se activarán una vez avanzado el torneo. ¡Asegura tus puntos!")

# ==========================================
# 2. BASE DE DATOS LOCAL Y AVATARES
# ==========================================
PERFILES = {
    "Alisson": "👩🏽", "Bernarda": "👩🏻", "Carlos": "👨🏻", "Claudio": "👨🏼",
    "Costanzo": "👨🏽", "Cristian": "👨🏻‍🦱", "Daniela": "👩🏼‍💼", "David": "👨🏻‍💻",
    "Emanuel": "👨🏽‍🦱", "Isidora": "👩🏻‍🦰", "Joseph": "👨🏻‍🚀", "Marco": "👨🏼‍🏫",
    "Miguel": "👨🏽‍🔧", "Milcka": "👩🏻‍💻", "Nayadeth": "👩🏽‍🏫", "Nicol": "👩🏻‍⚕️",
    "Patricio": "👨🏼‍💻", "Rodrigo": "👨🏻‍💼"
}

OPCIONES_USUARIOS = [f"{icono} {nombre}" for nombre, icono in PERFILES.items()]

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
# 3. CAPA DE EXTRACCIÓN Y LIMPIEZA DE DATOS
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

def parse_goles(valor):
    """
    Función blindada: Convierte cualquier dato de Excel a un número entero seguro.
    Si recibe celdas vacías, letras o errores, devuelve 0 sin romper el código.
    """
    try:
        if pd.isna(valor) or str(valor).strip() == "":
            return 0
        return int(float(str(valor).strip()))
    except (ValueError, TypeError):
        return 0

# ==========================================
# 4. LÓGICA DE PUNTOS (5-3-0)
# ==========================================
def calcular_puntos(g_loc_apuesta, g_vis_apuesta, g_loc_real, g_vis_real):
    try:
        gl_a, gv_a = int(g_loc_apuesta), int(g_vis_apuesta)
        gl_r, gv_r = int(g_loc_real), int(g_vis_real)
        
        if gl_a == gl_r and gv_a == gv_r:
            return 5
        elif (gl_a > gv_a and gl_r > gv_r) or (gl_a < gv_a and gl_r < gv_r) or (gl_a == gv_a and gl_r == gv_r):
            return 3
        return 0
    except (ValueError, TypeError):
        return 0

# ==========================================
# 5. GESTOR DE SESIÓN (LOGIN SIN SALTOS)
# ==========================================
if "usuario_activo" not in st.session_state:
    st.session_state.usuario_activo = None

if st.session_state.usuario_activo is None:
    with st.form("form_login"):
        st.markdown("### 🔐 Selecciona tu credencial")
        st.caption("Toca tu avatar y luego presiona el botón azul para ingresar de forma segura.")
        
        seleccion_cruda = st.radio("Perfiles Oficiales:", OPCIONES_USUARIOS, index=None, horizontal=True, label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        btn_ingresar = st.form_submit_button("🚀 Ingresar a BANBET", type="primary", use_container_width=True)
        
        if btn_ingresar:
            if seleccion_cruda is not None:
                nombre_puro = seleccion_cruda.split(" ", 1)[1]
                st.session_state.usuario_activo = nombre_puro
                st.rerun() 
            else:
                st.error("⚠️ Operación rechazada. Debes seleccionar tu perfil antes de continuar.")
    st.stop() 

# ==========================================
# 6. MOTOR DE INTERFAZ (VISTA CONECTADA)
# ==========================================
usuario_actual = st.session_state.usuario_activo
avatar_actual = PERFILES.get(usuario_actual, "👤")

col1, col2 = st.columns([2, 1])
with col1:
    st.success(f"Sesión activa: **{avatar_actual} {usuario_actual}**")
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

tab_futuros, tab_pasados = st.tabs(["🔮 CARTILLAS ABIERTAS", "📜 RESULTADOS Y PUNTOS"])

# ------------------------------------------
# PESTAÑA: APUESTAS ABIERTAS
# ------------------------------------------
with tab_futuros:
    if not partidos_futuros:
        st.success("🎉 ¡Has completado todos tus pronósticos! Espera a que rueden los balones.")
        
    for p in partidos_futuros:
        with st.container():
            st.markdown(f"### ⚽ {p['local']} vs {p['visita']}")
            fecha_obj = datetime.strptime(p["fecha_hora"], "%Y-%m-%d %H:%M")
            st.caption(f"⏱️ Pitazo inicial: **{fecha_obj.strftime('%d/%m/%Y')}** a las **{fecha_obj.strftime('%H:%M')} hrs**.")
            
            g_loc_previo, g_vis_previo = 0, 0
            if not mis_apuestas.empty:
                # Usamos .iloc[-1] para asegurarnos de tomar siempre la última actualización que hizo el usuario
                apuesta_previa = mis_apuestas[mis_apuestas["ID_Partido"] == p["id"]]
                if not apuesta_previa.empty:
                    # Limpieza blindada usando nuestra nueva función
                    g_loc_previo = parse_goles(apuesta_previa["Goles_Local"].iloc[-1])
                    g_vis_previo = parse_goles(apuesta_previa["Goles_Visita"].iloc[-1])
                    st.info(f"✅ Tu jugada guardada: **{g_loc_previo} - {g_vis_previo}**")
            
            with st.form(key=f"form_{p['id']}_{usuario_actual}"):
                c1, c2 = st.columns(2)
                with c1:
                    gl = st.number_input(f"Marcador {p['local'].split(' ')[0]}", min_value=0, max_value=20, step=1, value=g_loc_previo, key=f"loc_{p['id']}_{usuario_actual}")
                with c2:
                    gv = st.number_input(f"Marcador {p['visita'].split(' ')[0]}", min_value=0, max_value=20, step=1, value=g_vis_previo, key=f"vis_{p['id']}_{usuario_actual}")
                
                if st.form_submit_button("💾 Guardar y Asegurar Jugada", type="primary"):
                    with st.spinner("Enviando al servidor central..."):
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
# PESTAÑA: HISTORIAL Y PUNTOS
# ------------------------------------------
with tab_pasados:
    if not partidos_pasados:
        st.info("Aún no se ha cerrado ninguna cartilla.")
        
    for p in partidos_pasados:
        st.markdown(f"#### 🔒 {p['local']} vs {p['visita']}")
        
        texto_apuesta = "Ausente (0-0)"
        g_loc_a, g_vis_a = 0, 0
        
        if not mis_apuestas.empty:
            apuesta = mis_apuestas[mis_apuestas["ID_Partido"] == p["id"]]
            if not apuesta.empty:
                # Extracción blindada
                g_loc_a = parse_goles(apuesta["Goles_Local"].iloc[-1])
                g_vis_a = parse_goles(apuesta["Goles_Visita"].iloc[-1])
                texto_apuesta = f"{g_loc_a} - {g_vis_a}"

        resultado = df_resultados[df_resultados["ID_Partido"] == p["id"]] if not df_resultados.empty else pd.DataFrame()
        
        # Validación extra: Verificamos que realmente haya datos de goles y no celdas vacías o con "X" en Resultados
        if resultado.empty or pd.isna(resultado["Goles_Local"].iloc[-1]) or str(resultado["Goles_Local"].iloc[-1]).strip() == "":
            st.warning(f"⏳ Tu jugada: **{texto_apuesta}**. Pendiente de validación oficial.")
        else:
            # Extracción blindada del resultado oficial
            g_loc_r = parse_goles(resultado["Goles_Local"].iloc[-1])
            g_vis_r = parse_goles(resultado["Goles_Visita"].iloc[-1])
            puntos = calcular_puntos(g_loc_a, g_vis_a, g_loc_r, g_vis_r)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Tu Jugada", texto_apuesta)
            c2.metric("Marcador Final", f"{g_loc_r} - {g_vis_r}")
            c3.metric("Rendimiento", f"+{puntos} Pts")
        st.write("---")
