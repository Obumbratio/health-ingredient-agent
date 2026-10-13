import sys
from src.services.openfoodfacts import OpenFoodFactsService
from src.services.openfda import OpenFDAService
from src.agent.analyzer import HealthIngredientAgent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def test_analyzer_flow():
    print("=" * 70)
    print("HEALTH-INGREDIENT-AGENT: TEST DEL NÚCLEO DE RAZONAMIENTO")
    print("=" * 70)

    # 1. Obtener producto real desde Open Food Facts
    print("\n[1/3] Extrayendo datos de producto...")
    off_service = OpenFoodFactsService()
    results = off_service.search_by_name("Nutella", limit=1)

    if not results:
        print("❌ Error: No se pudo obtener el producto para la prueba.")
        return

    product = results[0]
    print(f"✅ Producto obtenido: {product['name']} ({product['brand']})")
    print(f"   Ingredientes detectados: {len(product['ingredients_list'])}")

    # 2. Consultar semáforo openFDA
    print("\n[2/3] Evaluando seguridad de la marca en openFDA...")
    fda_service = OpenFDAService()
    safety = fda_service.evaluate_brand_safety(
        product_name=product["name"],
        brand_name=product["brand"],
        item_type="food"
    )
    print(f"✅ Semáforo regulatorio: {safety['badge']} -> {safety['summary']}")

    # 3. Ejecutar análisis del agente de IA
    print("\n[3/3] Ejecutando clasificación tripartita y diagnóstico de salud...")
    agent = HealthIngredientAgent()
    report = agent.analyze_product(
        product_data=product,
        safety_data=safety,
        health_profile="Diabetes y Niños"
    )

    # 4. Desglose en consola
    print("\n" + "-" * 70)
    print(f"📊 REPORTE DE TRANSPARENCIA: {report.product_name}")
    print(f"⭐ Score de Transparencia de la Fórmula: {report.transparency_score}/100")
    print(f"🏛️ Veredicto Regulatorio: {report.brand_safety_verdict}")
    print("\n🧒 EXPLICACIÓN SENCILLA (NIVEL 10 AÑOS):")
    print(f"\"{report.simple_summary}\"")

    # Separación por categorías
    naturales = [i for i in report.ingredients if i.category == "Natural"]
    procesados = [i for i in report.ingredients if i.category == "Procesado"]
    sinteticos = [i for i in report.ingredients if i.category == "Sintético"]

    print("\n🌿 INGREDIENTES NATURALES:")
    for item in naturales:
        print(f"   • {item.name}: {item.function} | Balance: {item.risk_benefit}")

    print("\n⚙️ INGREDIENTES PROCESADOS:")
    for item in procesados:
        print(f"   • {item.name}: {item.function} | Evidencia: {item.adverse_effects_evidence}")

    print("\n🧪 INGREDIENTES SINTÉTICOS:")
    for item in sinteticos:
        print(f"   • {item.name}: {item.function} | Evidencia: {item.adverse_effects_evidence}")

    if report.health_alerts:
        print("\n⚠️ ALERTAS DE SALUD POR CONDICIÓN:")
        for alert in report.health_alerts:
            print(f"   [{alert.severity.upper()}] {alert.profile}: {alert.warning}")

    print("\n" + "=" * 70)
    print("PRUEBA DEL AGENTE COMPLETADA CON ÉXITO")
    print("=" * 70)


if __name__ == "__main__":
    test_analyzer_flow()
