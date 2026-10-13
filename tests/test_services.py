import sys
from src.services.openfoodfacts import OpenFoodFactsService
from src.services.openfda import OpenFDAService

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_services_test():
    print("=" * 65)
    print("HEALTH-INGREDIENT-AGENT: VERIFICACIÓN DE APIS Y SERVICIOS")
    print("=" * 65)

    # 1. Probar Open Food Facts
    print("\n[1/2] Consultando Open Food Facts para: 'Nutella'...")
    off = OpenFoodFactsService()
    foods = off.search_by_name("Nutella", limit=2)

    if not foods:
        print("❌ Error: No se recibieron datos de Open Food Facts.")
    else:
        sample = foods[0]
        print("✅ Open Food Facts responde correctamente:")
        print(f"   • Nombre:        {sample['name']}")
        print(f"   • Marca:         {sample['brand']}")
        print(f"   • NutriScore:    {sample['nutriscore']}")
        print(f"   • URL Imagen:    {sample['image_url'] or 'Sin imagen disponible'}")
        print(f"   • Ingredientes:  {len(sample['ingredients_list'])} detectados")
        if sample['ingredients_list']:
            print(f"     Primeros 3:    {', '.join(sample['ingredients_list'][:3])}...")

    # 2. Probar openFDA Enforcement (Recalls)
    print("\n" + "-" * 65)
    print("[2/2] Consultando openFDA (Auditoría de seguridad y recalls)...")
    fda = OpenFDAService()
    
    # Prueba de recall conocido (Jif Peanut Butter / Salmonella)
    safety_check = fda.evaluate_brand_safety(
        product_name="Jif Peanut Butter",
        brand_name="J. M. Smucker",
        item_type="food"
    )

    print(f"✅ openFDA responde correctamente:")
    print(f"   • Semáforo asignado: {safety_check['badge']}")
    print(f"   • Diagnóstico:       {safety_check['summary']}")
    if safety_check['details']:
        rec = safety_check['details'][0]
        print(f"   • Razón detectada:   {rec.get('reason_for_recall', 'N/A')[:120]}...")

    print("\n" + "=" * 65)
    print("INTEGRACIÓN DE DATOS LISTA PARA EL AGENTE ANALIZADOR")
    print("=" * 65)


if __name__ == "__main__":
    run_services_test()
