import streamlit as st
import pandas as pd
import logging
from datetime import datetime
import pytz
from typing import List, Dict
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURACIÓN Y LOGGING
# ==========================================
st.set_page_config(
    page_title="🏆 Sistema de Pronósticos BGL 2026", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="expanded"
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
ZONA_HORARIA = pytz.timezone('America/Santiago')

# ==========================================
# 2. MODELO DE DATOS Y ESTRUCTURA DEL TORNEO
# ==========================================
class DataModel:
    COLS_PRONOSTICOS = ["Timestamp", "Usuario", "Fase", "Partido", "Goles_Local", "Goles_Visita"]
    COLS_RESULTADOS = ["Timestamp", "Fase", "Partido", "Goles_Local", "Goles_Visita"]
    
    # Base de datos expandida con Fases y Grupos específicos
    PARTIDOS_DATA: List[Dict[str, str]] = [
        # Fase de Grupos
        {"id": "1", "etapa": "Fase de Grupos", "grupo": "Grupo A", "local": "México", "visita": "Polonia", "bandera_L": "🇲🇽", "bandera_V": "🇵🇱", "sede": "CDMX"},
        {"id": "2", "etapa": "Fase de Grupos", "grupo": "Grupo A", "local": "Argentina", "visita": "Polonia", "bandera_L": "🇦🇷", "bandera_V": "🇵🇱", "sede": "NY/NJ"},
        {"id": "3", "etapa": "Fase de Grupos", "grupo": "Grupo B", "local": "Canadá", "visita": "Marruecos", "bandera_L": "🇨🇦", "bandera_V": "🇲🇦", "sede": "Toronto"},
        {"id": "4", "etapa": "Fase de Grupos", "grupo": "Grupo B", "local": "Inglaterra", "visita": "Marruecos", "bandera_L": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "bandera_V": "🇲🇦", "sede": "Miami"},
        {"id": "5", "etapa": "Fase de Grupos", "grupo": "Grupo C", "local": "Chile", "visita": "Uruguay", "bandera_L": "🇨🇱", "bandera_V": "🇺🇾", "sede": "Los Angeles"},
        {"id": "6", "etapa": "Fase de Grupos", "grupo": "Grupo C", "local": "Uruguay", "visita": "Francia", "bandera_L": "🇺🇾", "bandera_V": "🇫🇷", "sede": "Dallas"},
        # Fases Eliminatorias (Ejemplos dinámicos)
        {"id": "7", "etapa": "Octavos de Final", "grupo": "Eliminatoria", "local": "1A", "visita": "2B", "bandera_L": "❓", "bandera_V": "❓", "sede": "Atlanta"},
        {"id": "8", "etapa": "Cuartos de Final", "grupo": "Eliminatoria", "local": "Ganador O1", "visita": "Ganador O2", "bandera_L": "🏆", "bandera_V": "🏆", "sede": "Houston"},
        {"id": "9", "etapa": "Semifinal", "grupo": "Eliminatoria", "local": "Ganador C1", "visita": "Ganador C2", "bandera_L": "🔥", "bandera_V": "🔥", "sede": "Boston"},
        {"id": "10", "etapa": "La Gran Final", "grupo": "Final", "local": "Finalista 1", "visita": "Finalista 2", "bandera_L": "👑", "bandera_V": "👑", "sede": "New York / New Jersey"}
    ]

    @classmethod
    def obtener_fases(cls) -> List[str]:
        """Extrae las etapas únicas del torneo."""
        fases = []
        for p in cls.PARTIDOS_DATA:
            if p['etapa'] not in fases:
                fases.append(p['etapa'])
        return fases

    @classmethod
    def obtener_partidos_por_fase(cls, etapa: str) -> List[str]:
        return [
            f"{p['bandera_L']} {p['local']} vs {p['visita']} {p['bandera_V']} | {p['grupo']} | 📍 {p['sede']}"
            for p in cls.PARTIDOS_DATA if p['etapa'] == etapa
        ]

# ==========================================
# 3. MANAGER TRANSACCIONAL (BASE DE DATOS)
# ==========================================
class DatabaseManager:
    @staticmethod
    def _obtener_conexion():
        return st.connection("gsheets", type=GSheetsConnection)

    @classmethod
    def cargar(cls, sheet_name: str, columns: List[str]) -> pd.DataFrame:
        conn = cls._obtener_conexion()
        try:
            df = conn.read(worksheet=sheet_name, ttl=30)
            if df is None or df.empty:
                return pd.DataFrame(columns=columns)
            
            # Auto-reparación de columnas faltantes por retrocompatibilidad
            for col in columns:
                if col not in df.columns:
                    df[col] = "Fase de Grupos" if col == "Fase" else ""
            return df.dropna(subset=["Partido"])
        except Exception:
            return pd.DataFrame(columns=columns)

    @classmethod
    def guardar(cls, sheet_name: str, new_row_df: pd.DataFrame, subset_drop: List[str]) -> bool:
        conn = cls._obtener_conexion()
        try:
            df_existente = conn.read(worksheet=sheet_name, ttl=0)
            if df_existente is None or df_existente.empty:
                df_existente = pd.DataFrame(columns=new_row_df.columns)
            else:
                for col in new_row_df.columns:
                    if col not in df_existente.columns:
                        df_existente[col] = ""
                df_existente = df_existente.dropna(subset=["Partido"])
                
            df_actualizado = pd.concat([df_existente, new_row_df], ignore_index=True)
            df_actualizado = df_actualizado.drop_duplicates(subset=subset_drop, keep='last')
            
            conn.update(worksheet=sheet_name, data=df_actualizado)
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"⚠️ Falla I/O en Google Sheets: {e}")
            return False

# ==========================================
# 4. MOTOR DE LÓGICA DEL MUNDIAL REAL
# ==========================================
class TournamentEngine:
    """Calcula las posiciones reales de los países en el Mundial."""
    
    @staticmethod
    def calcular_tabla_grupos(df_resultados: pd.DataFrame) -> pd.DataFrame:
        if df_resultados.empty:
            return pd.DataFrame()
            
        estadisticas = []
        
        # Procesamos solo los resultados que pertenecen a Fase de Grupos
        for _, row in df_resultados.iterrows():
            if "Fase de Grupos" not in str(row.get('Fase', '')):
                continue
                
            partido = row['Partido']
            try:
                # Extraer info del string del partido: "🇲🇽 México vs Polonia 🇵🇱 | Grupo A | ..."
                equipos_str = partido.split('|')[0].strip()
                grupo = partido.split('|')[1].strip()
                local_str, visita_str = equipos_str.split(' vs ')
                
                # Limpiar emojis
                local = ''.join([c for c in local_str if c.isalpha() or c.isspace()]).strip()
                visita = ''.join([c for c in visita_str if c.isalpha() or c.isspace()]).strip()
                
                g_local = int(row['Goles_Local'])
                g_visita = int(row['Goles_Visita'])
                
                # Lógica de Puntos FIFA: 3 Ganador, 1 Empate, 0 Perdedor
                pts_l = 3 if g_local > g_visita else (1 if g_local == g_visita else 0)
                pts_v = 3 if g_visita > g_local else (1 if g_local == g_visita else 0)
                
                estadisticas.append({"Grupo": grupo, "Equipo": local, "Pts": pts_l, "PJ": 1, "GF": g_local, "GC": g_visita, "DIF": g_local - g_visita})
                estadisticas.append({"Grupo": grupo, "Equipo": visita, "Pts": pts_v, "PJ": 1, "GF": g_visita, "GC": g_local, "DIF": g_visita - g_local})
            except Exception:
                continue
                
        if not estadisticas:
            return pd.DataFrame()
            
        df_stats = pd.DataFrame(estadisticas)
        
        # Agrupar por país y sumar métricas
        tabla_oficial = df_stats.groupby(["Grupo", "Equipo"]).agg({
            "Pts": "sum", "PJ": "sum", "GF": "sum", "GC": "sum", "DIF": "sum"
        }).reset_index()
        
        # Ordenar por Grupo, Puntos, Diferencia de Goles y Goles a Favor
        tabla_oficial = tabla_oficial.sort_values(by=["Grupo", "Pts", "DIF", "GF"], ascending=[True, False, False, False]).reset_index(drop=True)
        return tabla_oficial

# ==========================================
# 5. MOTOR DE RANKING CORPORATIVO BGL
# ==========================================
class AnalyticsEngine:
    """Calcula los puntos de los usuarios de BanGlobal."""
    
    @staticmethod
    def procesar_ranking(df_p: pd.DataFrame, df_r: pd.DataFrame) -> pd.DataFrame:
        if df_p.empty or df_r.empty:
            return pd.DataFrame()

        df = pd.merge(df_p, df_r, on="Partido", suffixes=('_P', '_R'))
        puntos, exactos, tendencias = [], [], []

        for _, row in df.iterrows():
            try:
                gl_p, gv_p = int(row['Goles_Local_P']), int(row['Goles_Visita_P'])
                gl_r, gv_r = int(row['Goles_Local_R']), int(row['Goles_Visita_R'])
                
                if gl_p == gl_r and gv_p == gv_r:
                    puntos.append(5) # Pleno
                    exactos.append(1)
                    tendencias.append(0)
                elif (gl_p > gv_p and gl_r > gv_r) or (gl_p < gv_p and gl_r < gv_r) or (gl_p == gv_p and gl_r == gv_r):
                    puntos.append(1) # Tendencia
                    exactos.append(0)
                    tendencias.append(1)
                else:
                    puntos.append(0); exactos.append(0); tendencias.append(0)
            except ValueError:
                puntos.append(0); exactos.append(0); tendencias.append(0)

        df['Puntos'] = puntos
        df['Exactos'] = exactos
        df['Tendencias'] = tendencias
        
        ranking = df.groupby("Usuario").agg(
            Puntos=('Puntos', 'sum'),
            Plenos=('Exactos', 'sum'),
            Aciertos=('Tendencias', 'sum'),
            Jugados=('Partido', 'count')
        ).reset_index()
        
        ranking['Eficiencia'] = (ranking['Puntos'] / (ranking['Jugados'] * 5) * 100).round(1).astype(str) + "%"
        
        ranking = ranking.sort_values(by=["Puntos", "Plenos", "Jugados"], ascending=[False, False, True]).reset_index(drop=True)
        ranking.index += 1 
        
        return ranking

# ==========================================
# 6. INTERFAZ Y RENDERIZADO
# ==========================================
class UserInterface:
    def __init__(self):
        self.db = DatabaseManager()
        self.ranking_engine = AnalyticsEngine()
        self.tournament_engine = TournamentEngine()
        
        self.df_pron = self.db.cargar("Pronosticos", DataModel.COLS_PRONOSTICOS)
        self.df_res = self.db.cargar("Resultados", DataModel.COLS_RESULTADOS)

    def render_sidebar(self):
        st.sidebar.title("⚽ Operaciones Mundial")
        menu = st.sidebar.radio("Navegación:", [
            "🏆 Ranking de la Oficina",
            "🌍 Tabla Oficial del Mundial",
            "📝 Ingresar Pronóstico", 
            "📊 Control de Gestión", 
            "⚙️ Consola Admin"
        ])
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Métricas de Puntaje:**\n- Pleno Exacto: **5 pts**\n- Tendencia: **1 pt**")
        return menu

    def view_ranking(self):
        st.title("🏆 Ranking de la Oficina")
        ranking_df = self.ranking_engine.procesar_ranking(self.df_pron, self.df_res)
        
        if not ranking_df.empty:
            c1, c2, c3 = st.columns(3)
            with c2: st.metric("🥇 1er Lugar", f"{ranking_df.iloc[0]['Usuario']}", f"{ranking_df.iloc[0]['Puntos']} pts")
            if len(ranking_df) > 1:
                with c1: st.metric("🥈 2do Lugar", f"{ranking_df.iloc[1]['Usuario']}", f"{ranking_df.iloc[1]['Puntos']} pts", delta_color="off")
            if len(ranking_df) > 2:
                with c3: st.metric("🥉 3er Lugar", f"{ranking_df.iloc[2]['Usuario']}", f"{ranking_df.iloc[2]['Puntos']} pts", delta_color="off")
            
            st.dataframe(ranking_df, use_container_width=True)
        else:
            st.info("ℹ️ Esperando consolidación de resultados para calcular jerarquías.")

    def view_tabla_mundial(self):
        st.title("🌍 Posiciones Reales del Torneo")
        st.markdown("Así van los grupos reales según los resultados inyectados por el administrador. Analiza esto antes de lanzar tus predicciones para Octavos.")
        
        tabla_mundial = self.tournament_engine.calcular_tabla_grupos(self.df_res)
        
        if not tabla_mundial.empty:
            grupos = tabla_mundial['Grupo'].unique()
            # Crear una cuadrícula de 2 columnas para mostrar los grupos ordenados
            cols = st.columns(2)
            for idx, grupo in enumerate(grupos):
                with cols[idx % 2]:
                    st.subheader(f"📊 {grupo}")
                    df_grupo = tabla_mundial[tabla_mundial['Grupo'] == grupo].drop(columns=['Grupo']).reset_index(drop=True)
                    df_grupo.index += 1
                    # Destacar visualmente a los dos primeros que clasifican
                    st.dataframe(df_grupo.style.apply(lambda x: ['background: #1e3a8a' if x.name in [1, 2] else '' for i in x], axis=1), use_container_width=True)
        else:
            st.warning("⚠️ No hay resultados oficiales procesados en la Fase de Grupos aún.")

    def view_pronosticos(self):
        st.title("📝 Ingreso de Pronósticos")
        
        # Filtro de fase interactivo
        fase_activa = st.radio("Filtra por Etapa del Torneo:", DataModel.obtener_fases(), horizontal=True)
        opciones_filtradas = DataModel.obtener_partidos_por_fase(fase_activa)
        
        with st.form("form_pronostico", clear_on_submit=False):
            st.markdown(f"**Partidos disponibles para: {fase_activa}**")
            usuario_input = st.text_input("👤 Tu Identificador (Ej: Daniela, Yeison, Milcka):")
            partido_seleccionado = st.selectbox("⚔️ Partido:", opciones_filtradas)
            
            equipos = partido_seleccionado.split('|')[0].strip() if partido_seleccionado else "Local vs Visita"
            local, visita = equipos.split(' vs ') if ' vs ' in equipos else ("Local", "Visita")
            
            c1, c2 = st.columns(2)
            with c1: g_local = st.number_input(f"Goles {local}:", min_value=0, max_value=20, step=1, value=0)
            with c2: g_visita = st.number_input(f"Goles {visita}:", min_value=0, max_value=20, step=1, value=0)
                
            if st.form_submit_button("💾 Ejecutar Transacción", type="primary"):
                usuario_limpio = usuario_input.strip().title()
                if not usuario_limpio or not partido_seleccionado:
                    st.error("⚠️ Faltan parámetros requeridos.")
                else:
                    timestamp_actual = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")
                    nuevo_registro = pd.DataFrame([{
                        "Timestamp": timestamp_actual, 
                        "Usuario": usuario_limpio, 
                        "Fase": fase_activa,
                        "Partido": partido_seleccionado, 
                        "Goles_Local": g_local, 
                        "Goles_Visita": g_visita
                    }])
                    
                    with st.spinner("Conectando con GSheets..."):
                        if self.db.guardar("Pronosticos", nuevo_registro, subset_drop=["Usuario", "Partido"]):
                            st.success(f"✅ ¡Guardado para {usuario_limpio}! El sistema registrará los puntos cuando finalice el encuentro.")
                            st.balloons()

    def view_dashboard(self):
        st.title("📊 Control de Gestión y KPIs")
        if not self.df_pron.empty:
            k1, k2, k3 = st.columns(3)
            k1.metric("Registros Históricos", len(self.df_pron))
            k2.metric("Headcount Participante", self.df_pron['Usuario'].nunique())
            k3.metric("Fase Más Activa", self.df_pron['Fase'].mode()[0] if 'Fase' in self.df_pron else "N/A")
            
            st.markdown("### Participación Consolidada")
            actividad = self.df_pron['Usuario'].value_counts().reset_index()
            actividad.columns = ['Usuario', 'Volumen de Transacciones']
            st.dataframe(actividad, hide_index=True, use_container_width=True)
        else:
            st.warning("Data insuficiente.")

    def view_admin(self):
        st.title("⚙️ Consola Admin")
        if "admin_auth" not in st.session_state:
            st.session_state["admin_auth"] = False

        if not st.session_state["admin_auth"]:
            if st.button("Validar") if st.text_input("🔑 Token de Acceso:", type="password") == "Mundial2026!" else False:
                st.session_state["admin_auth"] = True
                st.rerun()
        else:
            st.success("✅ Acceso a la capa de escritura autorizado.")
            if st.button("Logout"):
                st.session_state["admin_auth"] = False
                st.rerun()
                
            fase_admin = st.selectbox("1. Selecciona Fase a Cerrar:", DataModel.obtener_fases())
            partidos_admin = DataModel.obtener_partidos_por_fase(fase_admin)
            
            with st.form("form_resultados"):
                partido_res = st.selectbox("2. Partido Finalizado:", partidos_admin)
                c1, c2 = st.columns(2)
                with c1: g_loc = st.number_input("⚽ Goles Reales Local:", min_value=0, max_value=20, step=1, value=0)
                with c2: g_vis = st.number_input("⚽ Goles Reales Visita:", min_value=0, max_value=20, step=1, value=0)
                    
                if st.form_submit_button("🚨 Procesar Impactos", type="primary"):
                    ts = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")
                    nuevo_res = pd.DataFrame([{"Timestamp": ts, "Fase": fase_admin, "Partido": partido_res, "Goles_Local": g_loc, "Goles_Visita": g_vis}])
                    with st.spinner("Recalculando tablas y rankings..."):
                        if self.db.guardar("Resultados", nuevo_res, subset_drop=["Partido"]):
                            st.success("✅ Base de datos reconciliada. Las tablas del Mundial y el Ranking han sido actualizadas.")

def main():
    try:
        app = UserInterface()
        menu = app.render_sidebar()
        
        if menu == "🏆 Ranking de la Oficina": app.view_ranking()
        elif menu == "🌍 Tabla Oficial del Mundial": app.view_tabla_mundial()
        elif menu == "📝 Ingresar Pronóstico": app.view_pronosticos()
        elif menu == "📊 Control de Gestión": app.view_dashboard()
        elif menu == "⚙️ Consola Admin": app.view_admin()
    except Exception as e:
        st.error(f"Error de sistema crítico: {e}")

if __name__ == "__main__":
    main()
