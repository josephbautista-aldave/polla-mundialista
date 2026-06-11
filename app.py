import streamlit as st
import pandas as pd
import logging
from datetime import datetime
import pytz
from typing import List, Dict
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURACIÓN GLOBAL Y LOGGING
# ==========================================
st.set_page_config(
    page_title="🏆 Polla Mundial BanGlobal 2026", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="expanded"
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ZONA_HORARIA = pytz.timezone('America/Santiago')

# ==========================================
# 2. MODELO DE DATOS
# ==========================================
class DataModel:
    COLS_PRONOSTICOS = ["Timestamp", "Usuario", "Partido", "Goles_Local", "Goles_Visita"]
    COLS_RESULTADOS = ["Timestamp", "Partido", "Goles_Local", "Goles_Visita"]
    
    PARTIDOS_DATA: List[Dict[str, str]] = [
        {"id": "1", "fase": "Grupo A", "local": "México", "visita": "Polonia", "bandera_L": "🇲🇽", "bandera_V": "🇵🇱", "sede": "Estadio Azteca, CDMX", "fecha": "11 Jun"},
        {"id": "2", "fase": "Grupo B", "local": "Canadá", "visita": "Marruecos", "bandera_L": "🇨🇦", "bandera_V": "🇲🇦", "sede": "BMO Field, Toronto", "fecha": "12 Jun"},
        {"id": "3", "fase": "Grupo C", "local": "USA", "visita": "Gales", "bandera_L": "🇺🇸", "bandera_V": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "sede": "SoFi Stadium, LA", "fecha": "12 Jun"},
        {"id": "4", "fase": "Grupo D", "local": "Argentina", "visita": "Francia", "bandera_L": "🇦🇷", "bandera_V": "🇫🇷", "sede": "MetLife Stadium, NY/NJ", "fecha": "13 Jun"},
        {"id": "5", "fase": "Grupo E", "local": "Chile", "visita": "Uruguay", "bandera_L": "🇨🇱", "bandera_V": "🇺🇾", "sede": "Hard Rock Stadium, Miami", "fecha": "14 Jun"},
        {"id": "6", "fase": "Grupo F", "local": "Brasil", "visita": "Inglaterra", "bandera_L": "🇧🇷", "bandera_V": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "sede": "AT&T Stadium, Dallas", "fecha": "15 Jun"},
    ]

    @classmethod
    def obtener_opciones_partidos(cls) -> List[str]:
        return [
            f"{p['bandera_L']} {p['local']} vs {p['visita']} {p['bandera_V']} | {p['fase']} | 📍 {p['sede']} ({p['fecha']})"
            for p in cls.PARTIDOS_DATA
        ]

# ==========================================
# 3. CAPA DE INTEGRACIÓN DE BASE DE DATOS
# ==========================================
class DatabaseManager:
    @staticmethod
    def _obtener_conexion():
        return st.connection("gsheets", type=GSheetsConnection)

    @classmethod
    def cargar(cls, sheet_name: str, columns: List[str], ttl: int = 60) -> pd.DataFrame:
        conn = cls._obtener_conexion()
        try:
            df = conn.read(worksheet=sheet_name, ttl=ttl)
            if df is None or df.empty:
                return pd.DataFrame(columns=columns)
            return df.dropna(how="all")
        except Exception as e:
            logger.error(f"Error 400/500 al cargar {sheet_name}: {str(e)}")
            st.error(f"⚠️ Error de lectura en la pestaña '{sheet_name}'. Asegúrate de que los encabezados estén escritos en la fila 1 de tu Google Sheet.")
            return pd.DataFrame(columns=columns)

    @classmethod
    def guardar(cls, sheet_name: str, new_row_df: pd.DataFrame, subset_drop: List[str]) -> bool:
        conn = cls._obtener_conexion()
        try:
            df_existente = conn.read(worksheet=sheet_name, ttl=0)
            if df_existente is None or df_existente.empty:
                df_existente = pd.DataFrame(columns=new_row_df.columns)
            else:
                df_existente = df_existente.dropna(how="all")
                
            df_actualizado = pd.concat([df_existente, new_row_df], ignore_index=True)
            df_actualizado = df_actualizado.drop_duplicates(subset=subset_drop, keep='last')
            
            conn.update(worksheet=sheet_name, data=df_actualizado)
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error("⚠️ Falla transaccional. Revisa los permisos de edición de tu Google Sheet.")
            return False

# ==========================================
# 4. MOTOR ANALÍTICO Y DE CÁLCULO (CON BONUS)
# ==========================================
class AnalyticsEngine:
    @staticmethod
    def procesar_ranking(df_p: pd.DataFrame, df_r: pd.DataFrame) -> pd.DataFrame:
        columnas_vacias = ["Usuario", "Puntos Totales", "Aciertos Exactos (Bonus)", "Acierto Tendencia", "Efectividad (%)"]
        
        if df_p.empty or df_r.empty:
            return pd.DataFrame(columns=columnas_vacias)

        df = pd.merge(df_p, df_r, on="Partido", suffixes=('_P', '_R'))
        puntos, exactos, tendencias = [], [], []

        for _, row in df.iterrows():
            try:
                gl_p, gv_p = int(row['Goles_Local_P']), int(row['Goles_Visita_P'])
                gl_r, gv_r = int(row['Goles_Local_R']), int(row['Goles_Visita_R'])
                
                # LÓGICA DE BONUS APLICADA
                if gl_p == gl_r and gv_p == gv_r:
                    puntos.append(5)  # 3 Puntos Base + 2 Puntos Bonus por Pleno
                    exactos.append(1)
                    tendencias.append(0)
                elif (gl_p > gv_p and gl_r > gv_r) or (gl_p < gv_p and gl_r < gv_r) or (gl_p == gv_p and gl_r == gv_r):
                    puntos.append(1)  # 1 Punto por acertar tendencia
                    exactos.append(0)
                    tendencias.append(1)
                else:
                    puntos.append(0)
                    exactos.append(0)
                    tendencias.append(0)
            except ValueError:
                puntos.append(0); exactos.append(0); tendencias.append(0)

        df['Puntos'] = puntos
        df['Exactos'] = exactos
        df['Tendencias'] = tendencias
        
        ranking = df.groupby("Usuario").agg(
            Puntos=('Puntos', 'sum'),
            Aciertos_Exactos=('Exactos', 'sum'),
            Tendencias=('Tendencias', 'sum'),
            Partidos_Jugados=('Partido', 'count')
        ).reset_index()
        
        # Efectividad calculada sobre un máximo teórico de 5 pts por partido
        ranking['Efectividad (%)'] = (ranking['Puntos'] / (ranking['Partidos_Jugados'] * 5)) * 100
        ranking['Efectividad (%)'] = ranking['Efectividad (%)'].round(1).astype(str) + "%"
        
        ranking = ranking.sort_values(
            by=["Puntos", "Aciertos_Exactos", "Partidos_Jugados"], 
            ascending=[False, False, True]
        ).reset_index(drop=True)
        ranking.index += 1 
        
        return ranking.rename(columns={
            "Puntos": "Puntos Totales",
            "Aciertos_Exactos": "Aciertos Exactos (5pts)",
            "Tendencias": "Acierto Tendencia (1pt)",
            "Partidos_Jugados": "Pronósticos Evaluados"
        })

# ==========================================
# 5. CONTROLADORES DE INTERFAZ DE USUARIO (UI)
# ==========================================
class UserInterface:
    def __init__(self):
        self.db = DatabaseManager()
        self.analytics = AnalyticsEngine()
        self.opciones_partidos = DataModel.obtener_opciones_partidos()
        
        self.df_pron = self.db.cargar("Pronosticos", DataModel.COLS_PRONOSTICOS)
        self.df_res = self.db.cargar("Resultados", DataModel.COLS_RESULTADOS)

    def render_sidebar(self) -> str:
        st.sidebar.title("⚽ Mundial 2026")
        menu = st.sidebar.radio("Módulos del Sistema:", [
            "🏆 Tabla de Posiciones", 
            "📝 Ingreso de Pronósticos", 
            "📊 Dashboard de Gestión", 
            "⚙️ Consola de Administración"
        ])

        st.sidebar.markdown("---")
        with st.sidebar.expander("📖 Reglamento con Bonus", expanded=True):
            st.markdown("""
            * 🔥 **Acierto Exacto (Pleno):** 5 Puntos *(3 Base + 2 Bonus)*
            * 📈 **Tendencia (Ganador/Empate):** 1 Punto
            * ❌ **Fallo:** 0 Puntos
            * 🔄 *Se toma tu último pronóstico guardado.*
            """)

        if st.sidebar.button("🔄 Refrescar Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        return menu

    def view_ranking(self):
        st.title("🏆 Clasificación General Oficial")
        st.markdown("Monitor de rendimiento en tiempo real actualizado con el sistema de Bonus.")
        
        ranking_df = self.analytics.procesar_ranking(self.df_pron, self.df_res)
        
        if not ranking_df.empty:
            c1, c2, c3 = st.columns(3)
            with c2: st.metric("🥇 Líder Actual", f"{ranking_df.iloc[0]['Usuario']}", f"{ranking_df.iloc[0]['Puntos Totales']} pts")
            if len(ranking_df) > 1:
                with c1: st.metric("🥈 Segundo Lugar", f"{ranking_df.iloc[1]['Usuario']}", f"{ranking_df.iloc[1]['Puntos Totales']} pts", delta_color="off")
            if len(ranking_df) > 2:
                with c3: st.metric("🥉 Tercer Lugar", f"{ranking_df.iloc[2]['Usuario']}", f"{ranking_df.iloc[2]['Puntos Totales']} pts", delta_color="off")
            
            st.markdown("---")
            st.dataframe(ranking_df, use_container_width=True, hide_index=False)
        else:
            st.info("ℹ️ Esperando la validación del primer resultado oficial para generar las métricas.")

    def view_pronosticos(self):
        st.title("📝 Módulo de Ingreso de Pronósticos")
        
        with st.form("form_pronostico", clear_on_submit=False):
            usuario_input = st.text_input("👤 Identificador de Usuario:", placeholder="Ej: Daniela, Yeison, Pato, Milcka...")
            partido_seleccionado = st.selectbox("⚔️ Seleccionar Evento:", self.opciones_partidos)
            
            equipos = partido_seleccionado.split('|')[0].strip()
            local, visita = equipos.split(' vs ')
            
            st.markdown(f"### 🏟️ {local} 🆚 {visita}")
            c1, c2 = st.columns(2)
            with c1: g_local = st.number_input(f"Marcador {local}:", min_value=0, max_value=20, step=1, value=0)
            with c2: g_visita = st.number_input(f"Marcador {visita}:", min_value=0, max_value=20, step=1, value=0)
                
            if st.form_submit_button("💾 Consolidar Pronóstico", type="primary"):
                usuario_limpio = usuario_input.strip().title()
                if not usuario_limpio:
                    st.error("⚠️ El campo de usuario es obligatorio.")
                else:
                    timestamp_actual = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")
                    nuevo_registro = pd.DataFrame([{
                        "Timestamp": timestamp_actual, 
                        "Usuario": usuario_limpio, 
                        "Partido": partido_seleccionado, 
                        "Goles_Local": g_local, 
                        "Goles_Visita": g_visita
                    }])
                    
                    with st.spinner("Ejecutando transacción..."):
                        if self.db.guardar("Pronosticos", nuevo_registro, subset_drop=["Usuario", "Partido"]):
                            st.success(f"✅ ¡Jugada registrada para **{usuario_limpio}**! Ve por el Bonus.")
                            st.balloons()

    def view_dashboard(self):
        st.title("📊 Dashboard Analítico y KPIs")
        
        if not self.df_pron.empty:
            self.df_pron['Goles_Totales'] = pd.to_numeric(self.df_pron['Goles_Local']) + pd.to_numeric(self.df_pron['Goles_Visita'])
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Volumen Total", len(self.df_pron))
            k2.metric("Usuarios Únicos", self.df_pron['Usuario'].nunique())
            k3.metric("Prom. Goles Esperados", round(self.df_pron['Goles_Totales'].mean(), 2))
            k4.metric("Partido + Popular", self.df_pron['Partido'].value_counts().idxmax().split('|')[0].strip())
            
            st.markdown("---")
            c_graf, c_tab = st.columns([2, 1])
            
            with c_graf:
                st.subheader("📈 Concentración de Pronósticos")
                conteo_p = self.df_pron['Partido'].value_counts().reset_index()
                conteo_p.columns = ['Evento', 'Frecuencia']
                conteo_p['Evento'] = conteo_p['Evento'].apply(lambda x: x.split('|')[0].strip())
                st.bar_chart(conteo_p.set_index('Evento'), color="#FF4B4B")
                
            with c_tab:
                st.subheader("👥 Nivel de Actividad")
                actividad = self.df_pron['Usuario'].value_counts().reset_index()
                actividad.columns = ['Usuario', 'Registros']
                st.dataframe(actividad, hide_index=True, use_container_width=True)
        else:
            st.warning("⚠️ Sin datos suficientes para generar gráficos de control.")

    def view_admin(self):
        st.title("⚙️ Consola de Cierre Oficial")
        
        if "admin_auth" not in st.session_state:
            st.session_state["admin_auth"] = False

        if not st.session_state["admin_auth"]:
            pwd = st.text_input("🔑 Clave de Acceso:", type="password")
            if st.button("Validar"):
                if pwd == "Mundial2026!":
                    st.session_state["admin_auth"] = True
                    st.rerun()
                else:
                    st.error("❌ Credenciales inválidas.")
        else:
            st.success("✅ Acceso Concedido")
            if st.button("Cerrar Sesión"):
                st.session_state["admin_auth"] = False
                st.rerun()
                
            with st.form("form_resultados"):
                partido_res = st.selectbox("⚔️ Seleccionar Evento Finalizado:", self.opciones_partidos)
                c1, c2 = st.columns(2)
                with c1: g_loc = st.number_input("⚽ Resultado Real Local:", min_value=0, max_value=20, step=1, value=0)
                with c2: g_vis = st.number_input("⚽ Resultado Real Visita:", min_value=0, max_value=20, step=1, value=0)
                    
                if st.form_submit_button("🚨 Procesar Puntos y Bonus", type="primary"):
                    timestamp_actual = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")
                    nuevo_res = pd.DataFrame([{
                        "Timestamp": timestamp_actual, 
                        "Partido": partido_res, 
                        "Goles_Local": g_loc, 
                        "Goles_Visita": g_vis
                    }])
                    
                    with st.spinner("Calculando impactos..."):
                        if self.db.guardar("Resultados", nuevo_res, subset_drop=["Partido"]):
                            st.success("✅ ¡Base oficial actualizada! El ranking ha calculado los nuevos puntos.")

# ==========================================
# 6. PUNTO DE ENTRADA
# ==========================================
def main():
    try:
        app = UserInterface()
        menu = app.render_sidebar()
        
        if menu == "🏆 Tabla de Posiciones":
            app.view_ranking()
        elif menu == "📝 Ingreso de Pronósticos":
            app.view_pronosticos()
        elif menu == "📊 Dashboard de Gestión":
            app.view_dashboard()
        elif menu == "⚙️ Consola de Administración":
            app.view_admin()
            
    except Exception as e:
        st.error(f"⚠️ Error de sistema. Contacta al administrador. Detalle: {e}")

if __name__ == "__main__":
    main()
