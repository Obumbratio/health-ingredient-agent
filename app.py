import streamlit as st
from datetime import datetime
from typing import Optional

from src.config import settings
from src.services.openfoodfacts import OpenFoodFactsService
from src.services.openfda import OpenFDAService
from src.agent.analyzer import HealthIngredientAgent, ProductHealthReport

# Configuración inicial de la página
st.set_page_config(
    page_title="Health Ingredient Agent | Transparency & Safety",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de estilos de alto contraste y tipografía accesible
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Contenedor explicativo nivel 10 años */
    .kids-card {
        background-color: #0d1b2a;
        border: 2px solid #415a77;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
        color: #e0e1dd;
    }
    .kids-card-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #70d6ff;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .kids-card-body {
        font-size: 1.05rem;
        line-height: 1.6;
        color: #f8f9fa;
    }

    /* Badges de estado regulatorio */
    .badge-safe {
        background-color: #1b4332;
        color: #d8f3dc;
        border: 1px solid #40916c;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-warning {
        background-color: #5c4d00;
        color: #fff3bf;
        border: 1px solid #ffd43b;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-danger {
        background-color: #5a1818;
        color: #ffc9c9;
        border: 1px solid #fa5252;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Inicialización de recursos cacheados
@st.cache_resource
def load_services():
    return OpenFoodFactsService(), OpenFDAService(), HealthIngredientAgent()

off_service, fda_service, agent = load_services()

# Gestión del estado de la sesión
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None
if "current_safety" not in st.session_state:
    st.session_state.current_safety = None
if "current_report" not in st.session_state:
    st.session_state.current_report = None

# Barra lateral: Configuración, perfil de salud y telemetría de servicios
with st.sidebar:
    st.title("🥗 Health Agent")
    st.caption("AI-Powered Health & Transparency Platform")
    st.divider()

    st.subheader("👤 Perfil de Salud Activo")
    selected_profile = st.selectbox(
        "Filtro médico y nutricional:",
        [
            "General / Sin restricciones",
            "Diabetes Tipo 1 / Tipo 2",
            "Hipertensión Arterial",
            "Celiaquía / Intolerancia al Gluten",
            "Embarazo y Lactancia",
            "Infantil (Menores de 10 años)"
        ]
    )
    st.caption("El agente adapta automáticamente las alertas de toxicidad y alérgenos a esta condición.")
    st.divider()

    st.subheader("🔌 Estado de los Conectores")
    st.markdown("• **Open Food Facts:** 🟢 En línea (Datos globales)")
    st.markdown("• **openFDA Enforcement:** 🟢 En línea (Recalls oficiales)")
    if agent.client:
        st.markdown(f"• **Agente IA ({settings.OPENAI_MODEL}):** 🟢 Conectado")
    else:
        st.markdown("• **Agente IA:** 🟡 Modo Contingencia (Sin API Key)")

    st.divider()
    st.info("💡 **Inclusión y Accesibilidad:** Plataforma diseñada para democratizar prospectos y etiquetas en lenguaje libre de jerga científica.")

# Función auxiliar para exportación a Markdown
def build_markdown_dossier(product: dict, safety: dict, report: ProductHealthReport, profile: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    md = f"""# REPORTE DE TRANSPARENCIA: {product.get('name', '').upper()}
**Fecha de Inspección:** {timestamp}  
**Marca Fabricante:** {product.get('brand', 'N/A')}  
**Perfil Evaluado:** {profile}  
**Semáforo Regulatorio de Recalls:** {safety.get('badge', '')} - {safety.get('summary', '')}  
**Score de Transparencia de la Fórmula:** {report.transparency_score}/100  

---

## 1. Explicación en Lenguaje Sencillo (Nivel 10 años)
{report.simple_summary}

---

## 2. Veredicto Regulatorio
{report.brand_safety_verdict}

---

## 3. Desglose de Ingredientes Evaluados
"""
    for ing in report.ingredients:
        md += f"- **[{ing.category.upper()}] {ing.name}:** {ing.function}\n"
        md += f"  - *Balance Riesgo/Beneficio:* {ing.risk_benefit}\n"
        md += f"  - *Evidencia Médica:* {ing.adverse_effects_evidence}\n\n"

    if report.health_alerts:
        md += "---\n\n## 4. Alertas de Salud por Condición\n"
        for alert in report.health_alerts:
            md += f"- **[{alert.severity.upper()}] {alert.profile}:** {alert.warning}\n"

    md += "\n---\n*Generado de forma autónoma por Health Ingredient Agent.*"
    return md

# Encabezado principal
st.title("Auditoría de Transparencia en Alimentos y Medicamentos")
st.markdown(
    "Ingresa el nombre de cualquier producto o fármaco comercial para auditar sus ingredientes, "
    "verificar su semáforo oficial de retiros sanitarios y traducirlo a lenguaje accesible."
)

# Barra de búsqueda
search_col, btn_col = st.columns([5, 1])
with search_col:
    query = st.text_input(
        "Nombre del producto o código:",
        placeholder="Ejemplos: Nutella, Oreo, Galletas Marías, Yogurt Chobani...",
        label_visibility="collapsed"
    )
with btn_col:
    search_clicked = st.button("🔍 Buscar", use_container_width=True)

if search_clicked and query.strip():
    with st.spinner("Consultando bases de datos de alimentos..."):
        st.session_state.search_results = off_service.search_by_name(query, limit=4)
        st.session_state.selected_product = None
        st.session_state.current_report = None

# Visualización de resultados de búsqueda (Tarjetas de selección)
if st.session_state.search_results:
    st.subheader("Selecciona el producto a auditar:")
    card_cols = st.columns(len(st.session_state.search_results))

    for idx, prod in enumerate(st.session_state.search_results):
        with card_cols[idx]:
            with st.container(border=True):
                img_url = prod.get("image_url")
                if img_url:
                    st.image(img_url, use_container_width=True)
                else:
                    st.markdown("📦 *Sin imagen disponible*")
                
                st.markdown(f"**{prod.get('name', 'Sin nombre')[:35]}**")
                st.caption(f"Marca: {prod.get('brand', 'N/A')[:25]}")
                st.caption(f"NutriScore: `{prod.get('nutriscore', 'N/A')}`")

                if st.button("Auditar 🔬", key=f"btn_prod_{idx}", use_container_width=True):
                    st.session_state.selected_product = prod
                    with st.spinner("Verificando retiros en openFDA y analizando fórmula..."):
                        # Auditoría de marca en openFDA
                        safety = fda_service.evaluate_brand_safety(
                            product_name=prod.get("name", ""),
                            brand_name=prod.get("brand", ""),
                            item_type="food"
                        )
                        st.session_state.current_safety = safety

                        # Razonamiento estructurado del agente IA
                        report = agent.analyze_product(
                            product_data=prod,
                            safety_data=safety,
                            health_profile=selected_profile
                        )
                        st.session_state.current_report = report
                    st.rerun()

# Vista del Dossier de Salud Interactivo
if st.session_state.selected_product and st.session_state.current_report:
    prod = st.session_state.selected_product
    safety = st.session_state.current_safety
    report = st.session_state.current_report

    st.divider()

    # Encabezado del Dossier
    head_img_col, head_info_col = st.columns([1, 3])

    with head_img_col:
        if prod.get("image_url"):
            st.image(prod.get("image_url"), use_container_width=True)
        else:
            st.info("📦 Foto oficial no disponible.")

    with head_info_col:
        st.subheader(prod.get("name", "Producto"))
        st.markdown(f"**Fabricante / Marca:** `{prod.get('brand', 'No especificada')}`")
        
        # Semáforo de recalls
        status_type = safety.get("status", "SAFE")
        if status_type == "SAFE":
            badge_html = f"<div class='badge-safe'>{safety.get('badge')} | {safety.get('summary')}</div>"
        elif status_type == "WARNING":
            badge_html = f"<div class='badge-warning'>{safety.get('badge')} | {safety.get('summary')}</div>"
        else:
            badge_html = f"<div class='badge-danger'>{safety.get('badge')} | {safety.get('summary')}</div>"
        st.markdown(badge_html, unsafe_allow_html=True)

        st.metric(
            label="Puntaje de Transparencia de la Fórmula",
            value=f"{report.transparency_score} / 100",
            help="Basado en pureza, balance natural vs sintético y ausencia de aditivos sospechosos."
        )

    # Bloque: Explicación accesible nivel 10 años
    st.markdown(
        f"""
        <div class="kids-card">
            <div class="kids-card-title">🧒 ¿Qué le hace esto a mi cuerpo? (Explicado fácil)</div>
            <div class="kids-card-body">{report.simple_summary}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Columnas Tripartitas de Ingredientes
    st.subheader("🔬 Desglose Tripartito de Ingredientes")
    col_nat, col_proc, col_sint = st.columns(3)

    naturales = [i for i in report.ingredients if i.category == "Natural"]
    procesados = [i for i in report.ingredients if i.category == "Procesado"]
    sinteticos = [i for i in report.ingredients if i.category == "Sintético"]

    with col_nat:
        st.markdown(f"#### 🌿 Naturales ({len(naturales)})")
        if not naturales:
            st.caption("No se detectaron ingredientes de origen directo.")
        for ing in naturales:
            with st.container(border=True):
                st.markdown(f"**{ing.name}**")
                st.caption(f"Función: {ing.function}")
                st.markdown(f"⚖️ **Balance:** {ing.risk_benefit}")
                st.markdown(f"🧪 **Evidencia:** {ing.adverse_effects_evidence}")

    with col_proc:
        st.markdown(f"#### ⚙️ Procesados ({len(procesados)})")
        if not procesados:
            st.caption("Sin ingredientes de procesamiento intermedio.")
        for ing in procesados:
            with st.container(border=True):
                st.markdown(f"**{ing.name}**")
                st.caption(f"Función: {ing.function}")
                st.markdown(f"⚠️ **Efecto metabólico:** {ing.risk_benefit}")
                st.markdown(f"🧪 **Evidencia:** {ing.adverse_effects_evidence}")

    with col_sint:
        st.markdown(f"#### 🧪 Sintéticos ({len(sinteticos)})")
        if not sinteticos:
            st.caption("Fórmula libre de conservadores o químicos sintéticos detectados.")
        for ing in sinteticos:
            with st.container(border=True):
                st.markdown(f"**{ing.name}**")
                st.caption(f"Función química: {ing.function}")
                st.markdown(f"🚨 **Riesgo:** {ing.risk_benefit}")
                st.markdown(f"🔬 **Toxicidad / Alérgenos:** {ing.adverse_effects_evidence}")

    # Alertas de salud por condición
    if report.health_alerts:
        st.subheader("⚠️ Alertas de Salud para Grupos Vulnerables")
        for alert in report.health_alerts:
            if alert.severity == "Peligro":
                st.error(f"**[{alert.profile}]** {alert.warning}")
            elif alert.severity == "Precaución":
                st.warning(f"**[{alert.profile}]** {alert.warning}")
            else:
                st.info(f"**[{alert.profile}]** {alert.warning}")

    # Exportación del Dossier
    st.divider()
    dossier_text = build_markdown_dossier(prod, safety, report, selected_profile)
    clean_filename = prod.get("name", "producto").replace(" ", "_").lower()

    st.download_button(
        label=f"📥 Descargar Reporte de Auditoría (.md)",
        data=dossier_text,
        file_name=f"Auditoria_{clean_filename}.md",
        mime="text/markdown",
        use_container_width=True
    )
