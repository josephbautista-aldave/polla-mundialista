import streamlit as st
import pandas as pd
import logging
from datetime import datetime
import pytz
from typing import List, Dict, Optional, Tuple
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURACIÓN GLOBAL Y LOGGING
# ==========================================
st.set_page_config(
    page_title="🏆 Polla Mundial Enterprise 2026", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de Logging para auditoría en el servidor
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ZONA_HORARIA = pytz.timezone('America/Santiago')

# ==========================================
# 2. MODELO DE DATOS (CONSTANTES)
# ==========================================
class DataModel:
    """Clase estática para almacenar la configuración de datos estructurales."""
    COLS_PRONOSTICOS = ["Timestamp", "Usuario", "Partido", "Goles_Local", "Goles_Visita"]
    COLS_RESULTADOS = ["Timestamp", "Partido", "Goles_Local", "Goles_Visita"]
    
    # Base de datos local extendida (Fase de Grupos representativa)
    PARTIDOS_DATA: List[Dict[str, str]] = [
        {"id": "1", "fase": "Grupo A", "local": "México", "visita": "Polonia", "bandera_L": "🇲🇽", "bandera_V": "🇵🇱", "sede": "Estadio Azteca, CDMX", "fecha": "11 Jun"},
        {"id": "2", "fase": "Grupo B", "local": "Canadá", "visita": "Marruecos", "bandera_L": "🇨🇦", "bandera_V": "🇲🇦", "sede": "BMO Field, Toronto", "fecha": "12 Jun"},
        {"id": "3", "fase": "Grupo C", "local": "USA", "visita": "Gales", "bandera_L": "🇺🇸", "bandera_V": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "sede": "SoFi Stadium, LA", "fecha": "12 Jun"},
        {"id": "4", "fase": "Grupo D", "local": "Argentina", "visita": "Francia", "bandera_L": "🇦🇷", "bandera_V": "🇫🇷", "sede": "MetLife Stadium, NY/NJ", "fecha": "13 Jun"},
        {"id": "5", "fase": "Grupo E", "local": "Chile", "visita": "Uruguay", "bandera_L": "🇨🇱", "bandera_V": "🇺🇾", "sede": "Hard Rock Stadium, Miami", "fecha": "14 Jun"},
        {"id": "6", "fase": "Grupo F", "local": "Brasil", "visita": "Inglaterra", "bandera_L": "🇧🇷", "bandera_V": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "sede": "AT&T Stadium, Dallas", "fecha": "15 Jun"},
        {"id": "7", "fase": "Grupo G", "local": "España", "visita": "Portugal", "bandera_L": "🇪🇸", "bandera_V": "🇵🇹", "sede": "Mercedes-Benz Stadium, Atlanta", "fecha": "16 Jun"},
        {"id": "8", "fase": "Grupo H", "local": "Alemania", "visita": "Japón", "bandera_L": "🇩🇪", "bandera_V": "🇯🇵", "sede": "NRG Stadium, Houston", "fecha": "16 Jun"},
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
    """Maneja todas las transacciones I/O con Google Sheets con tolerancia a fallos."""
    
    @staticmethod
    def _obtener_conexion():
        return st.connection("gsheets", type=GSheetsConnection)

    @classmethod
    def cargar(cls, sheet_name: str, columns: List[str], ttl: int = 60) -> pd.DataFrame:
        conn = cls._obtener_conexion()
        try:
            df = conn.read(worksheet=sheet_name, ttl=ttl)
            if df is None or df.empty:
                logger.info(f"Hoja '{sheet_name}' leída, pero está vacía.")
                return pd.DataFrame(columns=columns)
            return df.dropna(how="all")
        except Exception as e:
            logger.error(f"Error al cargar {sheet_name}: {str(e)}")
            st.error(f"⚠️ Falla de conectividad al cargar: {sheet_name}. Operando en modo de contingencia.")
            return pd.DataFrame(columns=columns)

    @classmethod
    def guardar(cls, sheet_name: str, new_row_df: pd.DataFrame, subset_drop: List[str]) -> bool:
        conn = cls._obtener_conexion()
        try:
            # Lectura en crudo para asegurar el último estado
            df_existente = conn.read(worksheet=sheet_name, ttl=0)
            if df_existente is None or df_existente.empty:
                df_existente = pd.DataFrame(columns=new_row_df.columns)
            else:
                df_existente = df_existente.dropna(how="all")
                
            # Integridad de datos: Concatenar y eliminar duplicados (upsert logic)
            df_actualizado = pd.concat([df_existente, new_row_df], ignore_index=True)
            df_actualizado = df_actualizado.drop_duplicates(subset=subset_drop, keep='last')
            
            # Commit a GSheets
            conn.update(worksheet=sheet_name, data=df_actualizado)
            st.cache_data.clear()
            logger.info(f"Transacción exitosa en '{sheet_name}'.")
            return True
        except Exception as e:
            logger.error(f"Falla crítica de escritura en {sheet_name}: {str(e)}")
            st.error("⚠️ Falla transaccional. No se pudo consolidar el registro en la base de datos.")
            return False

# ==========================================
# 4. MOTOR ANALÍTICO Y DE CÁLCULO
# ==========================================
class AnalyticsEngine:
    """Procesa DataFrames para generar KPIs, rankings y métricas de control de gestión."""
    
    @staticmethod
    def procesar_ranking(df_p: pd.DataFrame, df_r: pd.DataFrame) -> pd.DataFrame:
        """Cruza pronósticos con resultados reales y asigna puntajes."""
        columnas_vacias = ["Usuario", "Puntos", "Aciertos Exactos (3pts)", "Acierto Tendencia (1pt)", "Efectividad (%)"]
        
        if df_p.empty or df_r.empty:
            return pd.DataFrame(columns=columnas_vacias)

        # Inner join por partido
        df = pd.merge(df_p, df_r, on="Partido", suffixes=('_P', '_R'))
        puntos, exactos, tendencias = [], [], []

        for _, row in df.iterrows():
            try:
                gl_p, gv_p = int(row['Goles_Local_P']), int(row['Goles_Visita_P'])
                gl_r, gv_r = int(row['Goles_Local_R']), int(row['Goles_Visita_R'])
                
                # Lógica del negocio
                if gl_p == gl_r and gv_p == gv_r:
                    puntos.append(3); exactos.append(1); tendencias.append(0)
                elif (gl_p > gv_p and gl_r > gv_r) or (gl_p < gv_p and gl_r < gv_r) or (gl_p == gv_p and gl_r == gv_r):
                    puntos.append(1); exactos.append(0); tendencias.append(1)
                else:
                    puntos.append(0); exactos.append(0); tendencias.append(0)
            except ValueError:
                puntos.append(0); exactos.append(0); tendencias.append(0)

        df['Puntos'] = puntos
        df['Exactos'] = exactos
        df['Tendencias'] = tendencias
        
        # Agrupación y generación de KPIs
        ranking = df.groupby("Usuario").agg(
            Puntos=('Puntos', 'sum'),
            Aciertos_Exactos=('Exactos', 'sum'),
            Tendencias=('Tendencias', 'sum'),
            Partidos_Jugados=('Partido', 'count')
        ).reset_index()
        
        # Cálculo de Efectividad (Puntos Obtenidos / Puntos Posibles)
        ranking['Efectividad (%)'] = (ranking['Puntos'] / (ranking['Partidos_Jugados'] * 3)) * 100
        ranking['Efectividad (%)'] = ranking['Efectividad (%)'].round(1).astype(str) + "%"
        
        # Orden jerárquico estricto
        ranking = ranking.sort_values(
            by=["Puntos", "Aciertos_Exactos", "Partidos_Jugados"], 
            ascending=[False, False, True]
        ).reset_index(drop=True)
        ranking.index += 1 
        
        return ranking.rename(columns={
            "Aciertos_Exactos": "Aciertos Exactos (3pts)",
            "Tendencias": "Acierto Tendencia (1pt)",
            "Partidos_Jugados": "Pronósticos Evaluados"
        })

# ==========================================
# 5. CONTROLADORES DE INTERFAZ DE USUARIO (UI)
# ==========================================
class UserInterface:
    """Gestiona el renderizado de las distintas vistas de la aplicación."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.analytics = AnalyticsEngine()
        self.opciones_partidos = DataModel.obtener_opciones_partidos()
        
        # Carga en memoria
        self.df_pron = self.db.cargar("Pronosticos", DataModel.COLS_PRONOSTICOS)
        self.df_res = self.db.cargar("Resultados", DataModel.COLS_RESULTADOS)

    def render_sidebar(self) -> str:
        st.sidebar.title("⚽ Mundial BGL 2026")
        menu = st.sidebar.radio("Módulos del Sistema:", [
            "🏆 Tabla de Posiciones", 
            "📝 Ingreso de Pronósticos", 
            "📊 Dashboard de Gestión", 
            "⚙️ Consola de Administración"
        ])

        st.sidebar.markdown("---")
        with st.sidebar.expander("📖 Reglamento del Sistema", expanded=True):
            st.markdown("""
            * 🎯 **Acierto Exacto:** 3 Puntos
            * 📈 **Tendencia (Ganador/Empate):** 1 Punto
            * ❌ **Fallo:** 0 Puntos
            * 🔄 *El sistema preserva únicamente la última transacción por usuario y partido.*
            """)

        if st.sidebar.button("🔄 Refrescar Caché", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        return menu

    def view_ranking(self):
        st.title("🏆 Clasificación General Oficial")
        st.markdown("Monitor de rendimiento en tiempo real actualizado con resultados consolidados.")
        
        ranking_df = self.analytics.procesar_ranking(self.df_pron, self.df_res)
        
        if not ranking_df.empty:
            c1, c2, c3 = st.columns(3)
            with c2: st.metric("🥇 Líder Actual", f"{ranking_df.iloc[0]['Usuario']}", f"{ranking_df.iloc[0]['Puntos']} pts")
            if len(ranking_df) > 1:
                with c1: st.metric("🥈 Segundo Lugar", f"{ranking_df.iloc[1]['Usuario']}", f"{ranking_df.iloc[1]['Puntos']} pts", delta_color="off")
            if len(ranking_df) > 2:
                with c3: st.metric("🥉 Tercer Lugar", f"{ranking_df.iloc[2]['Usuario']}", f"{ranking_df.iloc[2]['Puntos']} pts", delta_color="off")
            
            st.markdown("---")
            st.dataframe(ranking_df, use_container_width=True, hide_index=False)
        else:
            st.info("ℹ️ Esperando la validación del primer resultado oficial para generar las métricas de rendimiento.")

    def view_pronosticos(self):
        st.title("📝 Módulo de Ingreso de Pronósticos")
        
        with st.form("form_pronostico", clear_on_submit=False):
            usuario_input = st.text_input("👤 Identificador de Usuario (Conserva tu formato):", placeholder="Ingresa tu nombre de pila...")
            partido_seleccionado = st.selectbox("⚔️ Seleccionar Evento:", self.opciones_partidos)
            
            equipos = partido_seleccionado.split('|')[0].strip()
            local, visita = equipos.split(' vs ')
            
            st.markdown(f"### 🏟️ {local} 🆚 {visita}")
            c1, c2 = st.columns(2)
            with c1: g_local = st.number_input(f"Marcador {local}:", min_value=0, max_value=20, step=1, value=0)
            with c2: g_visita = st.number_input(f"Marcador {visita}:", min_value=0, max_value=20, step=1, value=0)
                
            submit = st.form_submit_button("💾 Consolidar Pronóstico", type="primary")
            
            if submit:
                usuario_limpio = usuario_input.strip().title()
                if not usuario_limpio:
                    st.error("⚠️ Validación fallida: El campo de usuario es obligatorio.")
                else:
                    timestamp_actual = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")
                    nuevo_registro = pd.DataFrame([{
                        "Timestamp": timestamp_actual, 
                        "Usuario": usuario_limpio, 
                        "Partido": partido_seleccionado, 
                        "Goles_Local": g_local, 
                        "Goles_Visita": g_visita
                    }])
                    
                    with st.spinner("Ejecutando transacción I/O..."):
                        if self.db.guardar("Pronosticos", nuevo_registro, subset_drop=["Usuario", "Partido"]):
                            st.success(f"✅ Transacción confirmada. Registro asignado a **{usuario_limpio}**.")
                            st.balloons()

    def view_dashboard(self):
        st.title("📊 Dashboard de Control de Gestión")
        st.markdown("Análisis macro de la participación y volumen transaccional de los usuarios.")
        
        if not self.df_pron.empty:
            self.df_pron['Goles_Totales'] = pd.to_numeric(self.df_pron['Goles_Local']) + pd.to_numeric(self.df_pron['Goles_Visita'])
            
            # Fila de KPIs
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Volumen Total", len(self.df_pron), help="Cantidad de pronósticos en la base de datos.")
            k2.metric("Usuarios Únicos", self.df_pron['Usuario'].nunique(), help="Personas que han participado.")
            k3.metric("Promedio Goles Esperados", round(self.df_pron['Goles_Totales'].mean(), 2))
            k4.metric("Evento con Mayor Tracción", self.df_pron['Partido'].value_counts().idxmax().split('|')[0].strip())
            
            st.markdown("---")
            c_graf, c_tab = st.columns([2, 1])
            
            with c_graf:
                st.subheader("📈 Distribución de Participación por Evento")
                conteo_p = self.df_pron['Partido'].value_counts().reset_index()
                conteo_p.columns = ['Evento', 'Frecuencia']
                conteo_p['Evento'] = conteo_p['Evento'].apply(lambda x: x.split('|')[0].strip())
                st.bar_chart(conteo_p.set_index('Evento'), color="#1abc9c")
                
            with c_tab:
                st.subheader("👥 Nivel de Actividad")
                actividad = self.df_pron['Usuario'].value_counts().reset_index()
                actividad.columns = ['Usuario', 'Registros Ingresados']
                st.dataframe(actividad, hide_index=True, use_container_width=True)
                
            with st.expander("🔍 Ver Data Transaccional Cruda (Últimos 15 movimientos)"):
                st.dataframe(self.df_pron.sort_values(by="Timestamp", ascending=False).head(15), use_container_width=True)
        else:
            st.warning("⚠️ Data insuficiente. El motor analítico requiere registros de entrada para generar las visualizaciones.")

    def view_admin(self):
        st.title("⚙️ Consola de Administración y Cierre")
        st.markdown("Módulo restringido para la inyección de resultados oficiales y recálculo de métricas.")
        
        # Gestión de estado de autenticación
        if "admin_auth" not in st.session_state:
            st.session_state["admin_auth"] = False

        if not st.session_state["admin_auth"]:
            pwd = st.text_input("🔑 Credenciales de Acceso (Admin):", type="password")
            if st.button("Validar Acceso"):
                if pwd == "Mundial2026!":
                    st.session_state["admin_auth"] = True
                    logger.info("Inicio de sesión de administrador exitoso.")
                    st.rerun()
                else:
                    logger.warning("Intento de acceso de administrador fallido.")
                    st.error("❌ Credenciales inválidas.")
        else:
            st.success("✅ Conectado a la Consola de Operaciones Core")
            if st.button("Cerrar Sesión Segura"):
                st.session_state["admin_auth"] = False
                st.rerun()
                
            st.markdown("### 📥 Consolidar Evento Oficial")
            with st.form("form_resultados"):
                partido_res = st.selectbox("⚔️ Seleccionar Evento Finalizado:", self.opciones_partidos)
                c1, c2 = st.columns(2)
                with c1: g_loc = st.number_input("⚽ Resultado Real Local:", min_value=0, max_value=20, step=1, value=0)
                with c2: g_vis = st.number_input("⚽ Resultado Real Visita:", min_value=0, max_value=20, step=1, value=0)
                    
                if st.form_submit_button("🚨 Impactar Base de Datos Global", type="primary"):
                    timestamp_actual = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")
                    nuevo_res = pd.DataFrame([{
                        "Timestamp": timestamp_actual, 
                        "Partido": partido_res, 
                        "Goles_Local": g_loc, 
                        "Goles_Visita": g_vis
                    }])
                    
                    with st.spinner("Calculando impactos y reestructurando jerarquías..."):
                        if self.db.guardar("Resultados", nuevo_res, subset_drop=["Partido"]):
                            st.success("✅ Base oficial actualizada. Jerarquías y KPIs recalculados.")

# ==========================================
# 6. FUNCIÓN MAIN (PUNTO DE ENTRADA)
# ==========================================
def main():
    """Inicializa la aplicación y gestiona el enrutamiento de las vistas."""
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
        logger.critical(f"Caída catastrófica en runtime: {str(e)}")
        st.error("⚠️ El sistema ha encontrado un error crítico irrecuperable. Los ingenieros han sido notificados en los logs.")

if __name__ == "__main__":
    main()
