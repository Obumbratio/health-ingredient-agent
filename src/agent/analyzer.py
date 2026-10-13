import logging
from typing import Any, Dict, List, Literal, Optional
from openai import OpenAI
from pydantic import BaseModel, Field
from src.config import settings

logger = logging.getLogger(__name__)


class IngredientAnalysis(BaseModel):
    name: str = Field(description="Nombre del ingrediente o compuesto químico")
    category: Literal["Natural", "Procesado", "Sintético"] = Field(
        description="Clasificación en una de las 3 categorías exactas"
    )
    function: str = Field(
        description="Función real cotidiana (ej. 'endulzante calórico', 'conservador de textura')"
    )
    risk_benefit: str = Field(
        description="Balance de riesgo/beneficio para el organismo humano"
    )
    adverse_effects_evidence: str = Field(
        description="Evidencia médica sobre efectos adversos, o indicación explícita de inocuo"
    )


class HealthAlert(BaseModel):
    profile: str = Field(description="Condición evaluada (Diabetes, Celiaquía, Embarazo, Niños, etc.)")
    severity: Literal["Informativo", "Precaución", "Peligro"] = Field(
        description="Nivel de severidad de la alerta"
    )
    warning: str = Field(description="Explicación clara de por qué representa un riesgo para este grupo")


class ProductHealthReport(BaseModel):
    product_name: str
    transparency_score: int = Field(
        ge=0,
        le=100,
        description="Puntuación de 0 a 100 basada en pureza, aditivos y transparencia"
    )
    simple_summary: str = Field(
        description="Resumen explicativo redactado en lenguaje simple, como para un niño de 10 años"
    )
    brand_safety_verdict: str = Field(
        description="Síntesis de la auditoría regulatoria de recalls de openFDA"
    )
    ingredients: List[IngredientAnalysis] = Field(
        default_factory=list,
        description="Desglose clasificado de cada ingrediente"
    )
    health_alerts: List[HealthAlert] = Field(
        default_factory=list,
        description="Alertas específicas para condiciones de salud o grupos vulnerables"
    )


class HealthIngredientAgent:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.model = settings.OPENAI_MODEL or "gpt-4o-mini"
        self.client: Optional[OpenAI] = None

        if self.api_key and self.api_key != "tu_api_key_aqui":
            client_kwargs = {"api_key": self.api_key}
            if getattr(settings, "LLM_BASE_URL", ""):
                client_kwargs["base_url"] = settings.LLM_BASE_URL
            self.client = OpenAI(**client_kwargs)
        else:
            logger.warning("LLM_API_KEY no detectada en .env. Se usarán respuestas de contingencia.")

    def _build_fallback_report(
        self,
        product_name: str,
        reason: str,
        safety_data: Dict[str, Any]
    ) -> ProductHealthReport:
        """Genera un reporte seguro y tipado si fallan los ingredientes o la API."""
        return ProductHealthReport(
            product_name=product_name,
            transparency_score=0,
            simple_summary=f"No se pudo completar el análisis exhaustivo: {reason}",
            brand_safety_verdict=safety_data.get("summary", "Sin datos regulatorios disponibles."),
            ingredients=[],
            health_alerts=[
                HealthAlert(
                    profile="General",
                    severity="Precaución",
                    warning="Verifica la etiqueta física del empaque antes de consumir este producto."
                )
            ]
        )

    def analyze_product(
        self,
        product_data: Dict[str, Any],
        safety_data: Dict[str, Any],
        health_profile: Optional[str] = None
    ) -> ProductHealthReport:
        product_name = product_data.get("name", "Producto no especificado")
        raw_ingredients = product_data.get("ingredients_list", [])
        ingredients_text = product_data.get("ingredients_text", "")

        # 1. Fallback si no hay ingredientes detectados
        if not raw_ingredients and not ingredients_text.strip():
            return self._build_fallback_report(
                product_name,
                "El producto no tiene lista de ingredientes registrada en la base de datos.",
                safety_data
            )

        # 2. Fallback si el cliente OpenAI no está disponible
        if not self.client:
            return self._build_fallback_report(
                product_name,
                "Configura tu LLM_API_KEY en el archivo .env para habilitar el agente de IA.",
                safety_data
            )

        ingredients_input = (
            ", ".join(raw_ingredients)
            if raw_ingredients
            else ingredients_text[:1200]
        )

        system_instruction = (
            "Eres un agente de transparencia médica y nutricional para personas sin conocimientos científicos. "
            "Tu misión es auditar los ingredientes de un producto y traducirlos a términos comprensibles.\n\n"
            "Reglas de clasificación obligatorias:\n"
            "1. Cada ingrediente debe asignarse únicamente a una de estas tres categorías:\n"
            "   - 'Natural': origen vegetal, animal o mineral directo sin síntesis industrial pesada.\n"
            "   - 'Procesado': componentes derivados o modificados mecánicamente/térmicamente.\n"
            "   - 'Sintético': químicos de laboratorio, aditivos artificiales, colorantes o fármacos.\n"
            "2. El campo 'simple_summary' debe explicar el impacto general del producto con claridad absoluta, "
            "como si se lo explicaras a un niño de 10 años, sin jerga médica compleja.\n"
            "3. En 'health_alerts', evalúa riesgos críticos para: Diabetes, Celiaquía/Gluten, Hipertensión, "
            "Embarazo y Niños. Si el usuario proporcionó un perfil específico, priorízalo."
        )

        user_content = (
            f"Producto: {product_name}\n"
            f"Marca: {product_data.get('brand', 'N/A')}\n"
            f"Perfil de salud del usuario: {health_profile or 'General / Sin restricciones previas'}\n"
            f"Auditoría regulatoria previa (openFDA): {safety_data.get('badge', '')} - {safety_data.get('summary', '')}\n"
            f"Ingredientes a evaluar: {ingredients_input}"
        )

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                response_format=ProductHealthReport,
                timeout=settings.REQUEST_TIMEOUT * 3
            )

            report = completion.choices[0].message.parsed
            if report:
                return report

            return self._build_fallback_report(
                product_name,
                "El modelo no generó un payload estructurado válido.",
                safety_data
            )

        except Exception as e:
            logger.error(f"Error durante el análisis del agente: {e}")
            return self._build_fallback_report(
                product_name,
                f"Error de comunicación o timeout con el proveedor de IA: {str(e)}",
                safety_data
            )
