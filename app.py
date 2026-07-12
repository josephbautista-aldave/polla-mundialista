import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection
import plotly.express as px

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
    
    # 🛡️ CAPA 4: BOTÓN DE ENFRIAMIENTO Y REFRESCO
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("### 📋 Reglas de Juego")
    st.info("""
    📲 **1. Identidad:** Juega usando tu perfil.
    ⏱️ **2. Plazos:** Bloqueo automático al inicio de cada partido.
    ➖ **3. Inactividad:** No participar suma 0 puntos.
    """)
    
    st.markdown("### 🥇 Sistema de Puntos")
    st.success("""
    * 🎯 **PLENO (5 pts):** Adivinar marcador exacto.
    * ✅ **TENDENCIA (3 pts):** Acertar ganador o empate.
    * ❌ **FALLO (0 pts):** Errar el pronóstico.
    """)

# ==========================================
# 2. BASE DE DATOS LOCAL Y AVATARES
# ==========================================
PERFILES = {
    "Alisson": "💼", "Bernarda": "🧮", "Carlos": "📈", "Claudio": "🔍",
    "Costanzo": "⚙️", "Cristian": "🔔", "Daniela": "💎", "David": "🚀",
    "Emanuel": "🛡️", "Isidora": "💻", "Joseph": "⚡", "Marco": "🧭",
    "Miguel": "🧐", "Milcka": "💸", "Nayadeth": "🪄", "Nicol": "🪙",
    "Patricio": "🐂", "Rodrigo": "🎯"
}

OPCIONES_USUARIOS = [f"{icono} {nombre}" for nombre, icono in PERFILES.items()]

PARTIDOS = [
    # --- JORNADA 1 ---
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
    {"id": "P23", "local": "Ghana 🇬🇭", "visita": "Panamá 🇵🇦", "fecha_hora": "2026-06-17 19:00"},
    {"id": "P24", "local": "Uzbekistán 🇺🇿", "visita": "Colombia 🇨🇴", "fecha_hora": "2026-06-17 22:00"},

    # --- JORNADA 2 ---
    {"id": "P25", "local": "República Checa 🇨🇿", "visita": "Sudáfrica 🇿🇦", "fecha_hora": "2026-06-18 12:00"},
    {"id": "P26", "local": "Suiza 🇨🇭", "visita": "Bosnia y Herzegovina 🇧🇦", "fecha_hora": "2026-06-18 15:00"},
    {"id": "P27", "local": "Canadá 🇨🇦", "visita": "Catar 🇶🇦", "fecha_hora": "2026-06-18 18:00"},
    {"id": "P28", "local": "México 🇲🇽", "visita": "Corea del Sur 🇰🇷", "fecha_hora": "2026-06-18 21:00"},
    {"id": "P29", "local": "Estados Unidos 🇺🇸", "visita": "Australia 🇦🇺", "fecha_hora": "2026-06-19 15:00"},
    {"id": "P30", "local": "Escocia 🏴󠁧󠁢󠁳󠁣󠁴󠁿", "visita": "Marruecos 🇲🇦", "fecha_hora": "2026-06-19 18:00"},
    {"id": "P31", "local": "Brasil 🇧🇷", "visita": "Haití 🇭🇹", "fecha_hora": "2026-06-19 20:30"},
    {"id": "P32", "local": "Turquía 🇹🇷", "visita": "Paraguay 🇵🇾", "fecha_hora": "2026-06-19 23:00"},
    {"id": "P33", "local": "Países Bajos 🇳🇱", "visita": "Suecia 🇸🇪", "fecha_hora": "2026-06-20 13:00"},
    {"id": "P34", "local": "Alemania 🇩🇪", "visita": "Costa de Marfil 🇨🇮", "fecha_hora": "2026-06-20 16:00"},
    {"id": "P35", "local": "Ecuador 🇪🇨", "visita": "Curazao 🇨🇼", "fecha_hora": "2026-06-20 20:00"},
    {"id": "P36", "local": "Japón 🇯🇵", "visita": "Túnez 🇹🇳", "fecha_hora": "2026-06-21 00:00"},
    {"id": "P37", "local": "España 🇪🇸", "visita": "Arabia Saudita 🇸🇦", "fecha_hora": "2026-06-21 12:00"},
    {"id": "P38", "local": "Bélgica 🇧🇪", "visita": "Irán 🇮🇷", "fecha_hora": "2026-06-21 15:00"},
    {"id": "P39", "local": "Uruguay 🇺🇾", "visita": "Cabo Verde 🇨🇻", "fecha_hora": "2026-06-21 18:00"},
    {"id": "P40", "local": "Nueva Zelanda 🇳🇿", "visita": "Egipto 🇪🇬", "fecha_hora": "2026-06-21 21:00"},
    {"id": "P41", "local": "Noruega 🇳🇴", "visita": "Senegal 🇸🇳", "fecha_hora": "2026-06-22 20:00"},
    {"id": "P42", "local": "Francia 🇫🇷", "visita": "Irak 🇮🇶", "fecha_hora": "2026-06-22 17:00"},
    {"id": "P43", "local": "Jordania 🇯🇴", "visita": "Argelia 🇩🇿", "fecha_hora": "2026-06-22 23:00"},
    {"id": "P44", "local": "Argentina 🇦🇷", "visita": "Austria 🇦🇹", "fecha_hora": "2026-06-22 13:00"},
    {"id": "P45", "local": "Portugal 🇵🇹", "visita": "Uzbekistán 🇺🇿", "fecha_hora": "2026-06-23 13:00"},
    {"id": "P46", "local": "Inglaterra 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "visita": "Ghana 🇬🇭", "fecha_hora": "2026-06-23 16:00"},
    {"id": "P47", "local": "Panamá 🇵🇦", "visita": "Croacia 🇭🇷", "fecha_hora": "2026-06-23 19:00"},
    {"id": "P48", "local": "Colombia 🇨🇴", "visita": "RD Congo 🇨🇩", "fecha_hora": "2026-06-23 22:00"},

    # --- JORNADA 3 ---
    {"id": "P49", "local": "República Checa 🇨🇿", "visita": "México 🇲🇽", "fecha_hora": "2026-06-24 21:00"},
    {"id": "P50", "local": "Sudáfrica 🇿🇦", "visita": "Corea del Sur 🇰🇷", "fecha_hora": "2026-06-24 21:00"},
    {"id": "P51", "local": "Escocia 🏴󠁧󠁢󠁳󠁣󠁴󠁿", "visita": "Brasil 🇧🇷", "fecha_hora": "2026-06-24 18:00"},
    {"id": "P52", "local": "Marruecos 🇲🇦", "visita": "Haití 🇭🇹", "fecha_hora": "2026-06-24 18:00"},
    {"id": "P53", "local": "Turquía 🇹🇷", "visita": "Estados Unidos 🇺🇸", "fecha_hora": "2026-06-25 22:00"},
    {"id": "P54", "local": "Paraguay 🇵🇾", "visita": "Australia 🇦🇺", "fecha_hora": "2026-06-25 22:00"},
    {"id": "P55", "local": "Ecuador 🇪🇨", "visita": "Alemania 🇩🇪", "fecha_hora": "2026-06-25 16:00"},
    {"id": "P56", "local": "Curazao 🇨🇼", "visita": "Costa de Marfil 🇨🇮", "fecha_hora": "2026-06-25 16:00"},
    {"id": "P57", "local": "Túnez 🇹🇳", "visita": "Países Bajos 🇳🇱", "fecha_hora": "2026-06-25 19:00"},
    {"id": "P58", "local": "Suecia 🇸🇪", "visita": "Japón 🇯🇵", "fecha_hora": "2026-06-25 19:00"},
    {"id": "P59", "local": "Egipto 🇪🇬", "visita": "Irán 🇮🇷", "fecha_hora": "2026-06-26 23:00"},
    {"id": "P60", "local": "Nueva Zelanda 🇳🇿", "visita": "Bélgica 🇧🇪", "fecha_hora": "2026-06-26 23:00"},
    {"id": "P61", "local": "Uruguay 🇺🇾", "visita": "España 🇪🇸", "fecha_hora": "2026-06-26 20:00"},
    {"id": "P62", "local": "Cabo Verde 🇨🇻", "visita": "Arabia Saudita 🇸🇦", "fecha_hora": "2026-06-26 20:00"},
    {"id": "P63", "local": "Senegal 🇸🇳", "visita": "Irak 🇮🇶", "fecha_hora": "2026-06-26 15:00"},
    {"id": "P64", "local": "Noruega 🇳🇴", "visita": "Francia 🇫🇷", "fecha_hora": "2026-06-26 15:00"},
    {"id": "P65", "local": "Argelia 🇩🇿", "visita": "Austria 🇦🇹", "fecha_hora": "2026-06-27 22:00"},
    {"id": "P66", "local": "Jordania 🇯🇴", "visita": "Argentina 🇦🇷", "fecha_hora": "2026-06-27 22:00"},
    {"id": "P67", "local": "Colombia 🇨🇴", "visita": "Portugal 🇵🇹", "fecha_hora": "2026-06-27 19:30"},
    {"id": "P68", "local": "RD Congo 🇨🇩", "visita": "Uzbekistán 🇺🇿", "fecha_hora": "2026-06-27 19:30"},
    {"id": "P69", "local": "Panamá 🇵🇦", "visita": "Inglaterra 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "fecha_hora": "2026-06-27 17:00"},
    {"id": "P70", "local": "Croacia 🇭🇷", "visita": "Ghana 🇬🇭", "fecha_hora": "2026-06-27 17:00"},
    {"id": "P71", "local": "Suiza 🇨🇭", "visita": "Canadá 🇨🇦", "fecha_hora": "2026-06-24 15:00"},
    {"id": "P72", "local": "Bosnia y Herzegovina 🇧🇦", "visita": "Catar 🇶🇦", "fecha_hora": "2026-06-24 15:00"},

    # --- DIECISÉISAVOS ---
    {"id": "P73", "local": "Sudáfrica 🇿🇦", "visita": "Canadá 🇨🇦", "fecha_hora": "2026-06-28 15:00"},
    {"id": "P74", "local": "Brasil 🇧🇷", "visita": "Japón 🇯🇵", "fecha_hora": "2026-06-29 13:00"},
    {"id": "P75", "local": "Alemania 🇩🇪", "visita": "Paraguay 🇵🇾", "fecha_hora": "2026-06-29 16:30"},
    {"id": "P76", "local": "Países Bajos 🇳🇱", "visita": "Marruecos 🇲🇦", "fecha_hora": "2026-06-29 21:00"},      
    {"id": "P77", "local": "Costa de Marfil 🇨🇮", "visita": "Noruega 🇳🇴", "fecha_hora": "2026-06-30 13:00"},    
    {"id": "P78", "local": "Francia 🇫🇷", "visita": "Suecia 🇸🇪", "fecha_hora": "2026-06-30 17:00"},
    
    {"id": "P79", "local": "México 🇲🇽", "visita": "Ecuador 🇪🇨", "fecha_hora": "2026-06-30 21:00"},
    {"id": "P80", "local": "Inglaterra 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "visita": "RD Congo 🇨🇩", "fecha_hora": "2026-07-01 12:00"},
    {"id": "P81", "local": "Bélgica 🇧🇪", "visita": "Senegal 🇸🇳", "fecha_hora": "2026-07-01 16:00"},
    {"id": "P82", "local": "Estados Unidos 🇺🇸", "visita": "Bosnia y Herzegovina 🇧🇦", "fecha_hora": "2026-07-01 20:00"},
    {"id": "P83", "local": "España 🇪🇸", "visita": "Austria 🇦🇹", "fecha_hora": "2026-07-02 15:00"},
    {"id": "P84", "local": "Portugal 🇵🇹", "visita": "Croacia 🇭🇷", "fecha_hora": "2026-07-02 19:00"},
    {"id": "P85", "local": "Suiza 🇨🇭", "visita": "Argelia 🇩🇿", "fecha_hora": "2026-07-02 23:00"},
    {"id": "P86", "local": "Australia 🇦🇺", "visita": "Egipto 🇪🇬", "fecha_hora": "2026-07-03 14:00"},
    {"id": "P87", "local": "Argentina 🇦🇷", "visita": "Cabo Verde 🇨🇻", "fecha_hora": "2026-07-03 18:00"},
    {"id": "P88", "local": "Colombia 🇨🇴", "visita": "Ghana 🇬🇭", "fecha_hora": "2026-07-03 21:30"},

    # --- OCTAVOS ---
    {"id": "P89", "local": "Canadá 🇨🇦", "visita": "Marruecos 🇲🇦", "fecha_hora": "2026-07-04 13:00"},
    {"id": "P90", "local": "Paraguay 🇵🇾", "visita": "Francia 🇫🇷", "fecha_hora": "2026-07-04 17:00"},
    {"id": "P91", "local": "Brasil 🇧🇷", "visita": "Noruega 🇳🇴", "fecha_hora": "2026-07-05 16:00"},
    {"id": "P92", "local": "México 🇲🇽", "visita": "Inglaterra 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "fecha_hora": "2026-07-05 20:00"},
    {"id": "P93", "local": "Portugal 🇵🇹", "visita": "España 🇪🇸", "fecha_hora": "2026-07-06 15:00"},
    {"id": "P94", "local": "Estados Unidos 🇺🇸", "visita": "Bélgica 🇧🇪", "fecha_hora": "2026-07-06 20:00"},
    
    {"id": "P95", "local": "Argentina 🇦🇷", "visita": "Egipto 🇪🇬", "fecha_hora": "2026-07-07 12:00"},
    {"id": "P96", "local": "Suiza 🇨🇭", "visita": "Colombia 🇨🇴", "fecha_hora": "2026-07-07 16:00"},

    # --- CUARTOS ---
    {"id": "P97", "local": "Francia 🇫🇷", "visita": "Marruecos 🇲🇦", "fecha_hora": "2026-07-09 16:00"},
    {"id": "P98", "local": "España 🇪🇸", "visita": "Bélgica 🇧🇪", "fecha_hora": "2026-07-10 15:00"},
    {"id": "P99", "local": "Noruega 🇳🇴", "visita": "Inglaterra 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "fecha_hora": "2026-07-11 17:00"},

    {"id": "P100", "local": "Argentina 🇦🇷", "visita": "Suiza 🇨🇭", "fecha_hora": "2026-07-11 21:00"},

    # --- SEMIFINALES ---
    {"id": "P101", "local": "Francia 🇫🇷", "visita": "España 🇪🇸", "fecha_hora": "2026-07-14 15:00"}
]

PARTIDOS = sorted(PARTIDOS, key=lambda x: datetime.strptime(x["fecha_hora"], "%Y-%m-%d %H:%M"))

COLS_APUESTAS = ["Timestamp", "Usuario", "ID_Partido", "Equipo_Local", "Equipo_Visita", "Fecha", "Goles_Local", "Goles_Visita"]
COLS_RESULTADOS = ["ID_Partido", "Equipo_Local", "Equipo_Visita", "Fecha", "Goles_Local", "Goles_Visita"]

# ==========================================
# 3. CAPA DE EXTRACCIÓN Y ESCRITURA BLINDADA
# ==========================================
def obtener_datos(hoja, columnas):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 🛡️ CAPA 2: MEMORIA CACHÉ (15 Segundos) para no saturar a Google con cada recarga
        df = conn.read(worksheet=hoja, ttl=15)
        
        if df is None or df.empty or str(df.columns[0]).startswith("Unnamed"):
            return pd.DataFrame(columns=columnas)
            
        df.columns = df.columns.str.strip()
        
        if "Usuario" in df.columns:
            df["Usuario"] = df["Usuario"].astype(str).str.strip()
        if "ID_Partido" in df.columns:
            df["ID_Partido"] = df["ID_Partido"].astype(str).str.strip()
            
        df = df.reindex(columns=columnas)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame(columns=columnas)

def guardar_nueva_apuesta(usuario, id_partido, equipo_l, equipo_v, fecha, gl, gv):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        df_fresco = conn.read(worksheet="Apuestas", ttl=0)
        
        # 🛡️ CAPA 1: CORTAFUEGOS ANTI-BORRADO
        if df_fresco is None or len(df_fresco) == 0 or str(df_fresco.columns[0]).startswith("Unnamed"):
            st.error("⚠️ ALERTA DE TRÁFICO: Servidor de Google saturado temporalmente. Para proteger los datos, no se guardó la jugada. Por favor, intenta de nuevo en 15 segundos.")
            return False

        df_fresco.columns = df_fresco.columns.str.strip()
        df_fresco = df_fresco.reindex(columns=COLS_APUESTAS).dropna(how="all")

        ahora_str = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")
        nueva_fila = pd.DataFrame([{
            "Timestamp": ahora_str, "Usuario": usuario, "ID_Partido": id_partido,
            "Equipo_Local": equipo_l, "Equipo_Visita": equipo_v, "Fecha": fecha,
            "Goles_Local": gl, "Goles_Visita": gv
        }])

        df_final = pd.concat([df_fresco, nueva_fila], ignore_index=True)
        df_final["Usuario"] = df_final["Usuario"].astype(str).str.strip()
        df_final["ID_Partido"] = df_final["ID_Partido"].astype(str).str.strip()
        df_final = df_final.drop_duplicates(subset=["Usuario", "ID_Partido"], keep='last')

        conn.update(worksheet="Apuestas", data=df_final)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error crítico de concurrencia: {e}")
        return False

def parse_goles(valor):
    try:
        if pd.isna(valor) or str(valor).strip() == "":
            return 0
        return int(float(str(valor).strip()))
    except (ValueError, TypeError):
        return 0

# ==========================================
# 4. LÓGICA DE PUNTOS
# ==========================================
def calcular_puntos(g_loc_apuesta, g_vis_apuesta, g_loc_real, g_vis_real):
    if g_loc_apuesta is None or g_vis_apuesta is None:
        return 0
        
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
# 5. GESTOR DE SESIÓN
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
                nombre_puro = seleccion_cruda.split(" ", 1)[1].strip()
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

if not df_apuestas.empty:
    mis_apuestas = df_apuestas[df_apuestas["Usuario"] == usuario_actual] 
else:
    mis_apuestas = pd.DataFrame(columns=COLS_APUESTAS)

ahora_dt = datetime.now(ZONA_HORARIA)

partidos_futuros, partidos_pasados = [], []

for p in PARTIDOS:
    fecha_partido = ZONA_HORARIA.localize(datetime.strptime(p["fecha_hora"], "%Y-%m-%d %H:%M"))
    if ahora_dt < fecha_partido:
        partidos_futuros.append(p)
    else:
        partidos_pasados.append(p)

tab_futuros, tab_pasados, tab_tribuna, tab_tabla, tab_grafico = st.tabs(["🔮 CARTILLAS", "📜 RESULTADOS", "🏟️ TRIBUNA", "🏆 POSICIONES", "📈 EVOLUCIÓN"])

# ------------------------------------------
# PESTAÑA 1: APUESTAS ABIERTAS
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
                apuesta_previa = mis_apuestas[mis_apuestas["ID_Partido"] == p["id"]]
                if not apuesta_previa.empty:
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
                    # 🛡️ CAPA 3: GUARDIA DE TIEMPO ANTI-PESTAÑAS ZOMBIES
                    ahora_check = datetime.now(ZONA_HORARIA)
                    fecha_limite = ZONA_HORARIA.localize(datetime.strptime(p["fecha_hora"], "%Y-%m-%d %H:%M"))
                    
                    if ahora_check >= fecha_limite:
                        st.error("❌ ¡Llegaste tarde! El pitazo inicial ya sonó. Refresca la página.")
                    else:
                        with st.spinner("Enviando al servidor central..."):
                            if guardar_nueva_apuesta(usuario_actual, p["id"], p["local"], p["visita"], p["fecha_hora"], gl, gv):
                                st.success("¡Transacción registrada con éxito!")
                                st.rerun()
            st.write("---")

# ------------------------------------------
# PESTAÑA 2: HISTORIAL Y PUNTOS 
# ------------------------------------------
with tab_pasados:
    if not partidos_pasados:
        st.info("Aún no se ha cerrado ninguna cartilla.")
    else:
        datos_procesados = []
        puntos_acumulados_totales = 0
        
        for p in partidos_pasados:
            texto_apuesta = "Sin pronóstico"
            g_loc_a, g_vis_a = None, None 
            
            if not mis_apuestas.empty:
                apuesta = mis_apuestas[mis_apuestas["ID_Partido"] == p["id"]]
                if not apuesta.empty:
                    g_loc_a = parse_goles(apuesta["Goles_Local"].iloc[-1])
                    g_vis_a = parse_goles(apuesta["Goles_Visita"].iloc[-1])
                    texto_apuesta = f"{g_loc_a} - {g_vis_a}"

            resultado = df_resultados[df_resultados["ID_Partido"] == p["id"]] if not df_resultados.empty else pd.DataFrame()
            
            puntos = 0
            validado = False
            g_loc_r = None
            g_vis_r = None
            
            if not resultado.empty:
                g_loc_r_str = str(resultado["Goles_Local"].iloc[-1]).strip()
                if not (pd.isna(resultado["Goles_Local"].iloc[-1]) or g_loc_r_str == "" or g_loc_r_str == "nan"):
                    g_loc_r = parse_goles(resultado["Goles_Local"].iloc[-1])
                    g_vis_r = parse_goles(resultado["Goles_Visita"].iloc[-1])
                    
                    puntos = calcular_puntos(g_loc_a, g_vis_a, g_loc_r, g_vis_r)
                    puntos_acumulados_totales += puntos
                    validado = True
            
            datos_procesados.append({
                "partido": p,
                "texto_apuesta": texto_apuesta,
                "validado": validado,
                "g_loc_r": g_loc_r,
                "g_vis_r": g_vis_r,
                "puntos": puntos,
                "acumulado": puntos_acumulados_totales
            })
            
        for data in reversed(datos_procesados):
            p = data["partido"]
            st.markdown(f"#### 🔒 {p['local']} vs {p['visita']}")
            
            if not data["validado"]:
                st.warning(f"⏳ Tu jugada: **{data['texto_apuesta']}**. Pendiente de validación oficial.")
            else:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Tu Jugada", data["texto_apuesta"])
                c2.metric("Marcador Final", f"{data['g_loc_r']} - {data['g_vis_r']}")
                c3.metric("Rendimiento", f"+{data['puntos']} Pts")
                c4.metric("Acumulado", f"{data['acumulado']} Pts")
            st.write("---")

# ------------------------------------------
# PESTAÑA 3: LA TRIBUNA
# ------------------------------------------
with tab_tribuna:
    if not partidos_pasados:
        st.info("Aún no ha comenzado ningún partido.")
    else:
        for p in reversed(partidos_pasados):
            resultado = df_resultados[df_resultados["ID_Partido"] == p["id"]] if not df_resultados.empty else pd.DataFrame()
            g_loc_r = None
            g_vis_r = None
            resultado_texto = "Pendiente"
            
            if not resultado.empty:
                g_loc_r_str = str(resultado["Goles_Local"].iloc[-1]).strip()
                if not (pd.isna(resultado["Goles_Local"].iloc[-1]) or g_loc_r_str == "" or g_loc_r_str == "nan"):
                    g_loc_r = parse_goles(resultado["Goles_Local"].iloc[-1])
                    g_vis_r = parse_goles(resultado["Goles_Visita"].iloc[-1])
                    resultado_texto = f"{g_loc_r} - {g_vis_r}"

            with st.expander(f"⚽ {p['local']} vs {p['visita']} | Marcador Final: {resultado_texto}"):
                apuestas_partido = df_apuestas[df_apuestas["ID_Partido"] == p["id"]] if not df_apuestas.empty else pd.DataFrame()
                
                datos_tribuna = []
                
                for nombre, icono in PERFILES.items():
                    apuesta_usuario = pd.DataFrame()
                    if not apuestas_partido.empty:
                        apuesta_usuario = apuestas_partido[apuestas_partido["Usuario"] == nombre]
                    
                    if not apuesta_usuario.empty:
                        gl_a = parse_goles(apuesta_usuario["Goles_Local"].iloc[-1])
                        gv_a = parse_goles(apuesta_usuario["Goles_Visita"].iloc[-1])
                        
                        if g_loc_r is not None and g_vis_r is not None:
                            pts = calcular_puntos(gl_a, gv_a, g_loc_r, g_vis_r)
                            if pts == 5:
                                pronostico = f"{gl_a} - {gv_a} 🎯"
                            elif pts == 3:
                                pronostico = f"{gl_a} - {gv_a} ✅"
                            else:
                                pronostico = f"{gl_a} - {gv_a}"
                        else:
                            pronostico = f"{gl_a} - {gv_a}" 
                    else:
                        pronostico = "-"
                    
                    datos_tribuna.append({
                        "Participante": f"{icono} {nombre}",
                        "Pronóstico": pronostico
                    })
                
                df_tribuna = pd.DataFrame(datos_tribuna)
                st.dataframe(df_tribuna, use_container_width=True, hide_index=True)

# ------------------------------------------
# PESTAÑA 4: TABLA DE LÍDERES
# ------------------------------------------
with tab_tabla:
    partidos_con_resultado = []
    for p in partidos_pasados:
        resultado = df_resultados[df_resultados["ID_Partido"] == p["id"]] if not df_resultados.empty else pd.DataFrame()
        if not resultado.empty:
            g_loc_r_str = str(resultado["Goles_Local"].iloc[-1]).strip()
            if not (pd.isna(resultado["Goles_Local"].iloc[-1]) or g_loc_r_str == "" or g_loc_r_str == "nan"):
                partidos_con_resultado.append(p)
                
    if not partidos_con_resultado:
        st.info("Aún no hay resultados para generar la tabla.")
    else:
        datos_tabla = []
        
        for nombre, icono in PERFILES.items():
            pts_totales, pj, plenos, tendencias, fallos, ausencias = 0, 0, 0, 0, 0, 0
            historial_racha = []
            
            for p in partidos_con_resultado:
                res = df_resultados[df_resultados["ID_Partido"] == p["id"]]
                g_loc_r = parse_goles(res["Goles_Local"].iloc[-1])
                g_vis_r = parse_goles(res["Goles_Visita"].iloc[-1])
                
                ap_usr = df_apuestas[(df_apuestas["ID_Partido"] == p["id"]) & (df_apuestas["Usuario"] == nombre)]
                
                if not ap_usr.empty:
                    g_loc_a = parse_goles(ap_usr["Goles_Local"].iloc[-1])
                    g_vis_a = parse_goles(ap_usr["Goles_Visita"].iloc[-1])
                    pj += 1
                    
                    pts = calcular_puntos(g_loc_a, g_vis_a, g_loc_r, g_vis_r)
                    pts_totales += pts
                    
                    if pts == 5:
                        plenos += 1
                        historial_racha.append("🎯")
                    elif pts == 3:
                        tendencias += 1
                        historial_racha.append("✅")
                    else:
                        fallos += 1
                        historial_racha.append("❌")
                else:
                    ausencias += 1
                    historial_racha.append("➖")
            
            ultimos_3 = "".join(historial_racha[-3:]) if historial_racha else "➖"
            
            datos_tabla.append({
                "Participante": f"{icono} {nombre}",
                "Pts": pts_totales,
                "PJ": pj,
                "🎯 Plenos": plenos,
                "✅ Tend.": tendencias,
                "❌ Fallos": fallos,
                "➖ Aus.": ausencias,
                "Racha (Últ 3)": ultimos_3
            })
            
        df_tabla = pd.DataFrame(datos_tabla)
        df_tabla = df_tabla.sort_values(by=["Pts", "🎯 Plenos", "✅ Tend."], ascending=[False, False, False]).reset_index(drop=True)
        
        posiciones = []
        rango_actual = 1
        for i in range(len(df_tabla)):
            if i > 0:
                prev = df_tabla.iloc[i-1]
                curr = df_tabla.iloc[i]
                if (curr["Pts"] == prev["Pts"] and 
                    curr["🎯 Plenos"] == prev["🎯 Plenos"] and 
                    curr["✅ Tend."] == prev["✅ Tend."]):
                    pass
                else:
                    rango_actual = i + 1
            
            if rango_actual == 1:
                posiciones.append("🥇 1")
            elif rango_actual == 2:
                posiciones.append("🥈 2")
            elif rango_actual == 3:
                posiciones.append("🥉 3")
            else:
                posiciones.append(str(rango_actual))
                
        df_tabla.insert(0, "Pos", posiciones)
        
        st.dataframe(df_tabla, use_container_width=True, hide_index=True)
        st.caption("🔍 **Leyenda de Racha:** 🎯 Pleno (5 pts) | ✅ Tendencia (3 pts) | ❌ Fallo (0 pts) | ➖ Ausencia")

# ------------------------------------------
# PESTAÑA 5: GRÁFICO EVOLUTIVO
# ------------------------------------------
with tab_grafico:
    partidos_con_resultado = []
    for p in partidos_pasados:
        resultado = df_resultados[df_resultados["ID_Partido"] == p["id"]] if not df_resultados.empty else pd.DataFrame()
        if not resultado.empty:
            g_loc_r_str = str(resultado["Goles_Local"].iloc[-1]).strip()
            if not (pd.isna(resultado["Goles_Local"].iloc[-1]) or g_loc_r_str == "" or g_loc_r_str == "nan"):
                partidos_con_resultado.append(p)
    
    if not partidos_con_resultado:
        st.info("Aún no hay resultados oficiales registrados para generar la carrera.")
    else:
        acumulados = {nombre: 0 for nombre in PERFILES.keys()}
        datos_grafico = []
        nombres_eje_x = []
        
        for p in partidos_con_resultado:
            etiqueta_partido = f"{p['local']} vs {p['visita']}"
            nombres_eje_x.append(etiqueta_partido)
            
            res = df_resultados[df_resultados["ID_Partido"] == p["id"]]
            g_loc_r = parse_goles(res["Goles_Local"].iloc[-1])
            g_vis_r = parse_goles(res["Goles_Visita"].iloc[-1])
            
            apuestas_p = df_apuestas[df_apuestas["ID_Partido"] == p["id"]] if not df_apuestas.empty else pd.DataFrame()
            
            for nombre, icono in PERFILES.items():
                g_loc_a, g_vis_a = None, None
                ap_usr = apuestas_p[apuestas_p["Usuario"] == nombre] if not apuestas_p.empty else pd.DataFrame()
                
                if not ap_usr.empty:
                    g_loc_a = parse_goles(ap_usr["Goles_Local"].iloc[-1])
                    g_vis_a = parse_goles(ap_usr["Goles_Visita"].iloc[-1])
                
                puntos_ganados = calcular_puntos(g_loc_a, g_vis_a, g_loc_r, g_vis_r)
                acumulados[nombre] += puntos_ganados
                
                datos_grafico.append({
                    "Partido": etiqueta_partido,
                    "Participante": f"{icono} {nombre}",
                    "Puntos": acumulados[nombre]
                })
        
        df_grafico = pd.DataFrame(datos_grafico)
        
        partido_limite = st.select_slider(
            "Selecciona hasta qué partido viajar:",
            options=nombres_eje_x,
            value=nombres_eje_x[-1],
            label_visibility="collapsed"
        )
        
        df_filtrado = df_grafico[df_grafico["Partido"] == partido_limite].copy()
        
        fig = px.bar(
            df_filtrado, 
            x="Puntos", 
            y="Participante", 
            text="Puntos",
            color="Participante",
            color_discrete_map={"⚡ Joseph": "RoyalBlue"}, 
            orientation='h',
            height=750 
        )
        
        fig.update_layout(
            yaxis={'categoryorder':'total ascending', 'tickfont': {'size': 14}}, 
            xaxis_title="Puntos Acumulados",
            yaxis_title="",
            showlegend=False, 
            template="presentation",
            margin=dict(l=0, r=0, t=20, b=0) 
        )
        
        fig.update_traces(
            textposition='inside', 
            textfont=dict(size=14, weight='bold') 
        )
        st.plotly_chart(fig, use_container_width=True)
