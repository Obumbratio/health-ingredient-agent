import logging
from typing import Any, Dict, List, Optional
import requests
from src.config import settings

logger = logging.getLogger(__name__)


class OpenFoodFactsService:
    SEARCH_URLS = [
        "https://world.openfoodfacts.net/cgi/search.pl",
        "https://world.openfoodfacts.org/cgi/search.pl"
    ]
    PRODUCT_URLS = [
        "https://world.openfoodfacts.net/api/v2/product",
        "https://world.openfoodfacts.org/api/v2/product"
    ]

    def __init__(self):
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json"
        }
        self.timeout = settings.REQUEST_TIMEOUT

    def search_by_name(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Busca productos por texto libre y normaliza los resultados con reintento/mirror."""
        if not query.strip():
            return []

        params = {
            "search_terms": query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": limit,
            "fields": (
                "code,product_name,product_name_es,product_name_en,"
                "brands,image_url,image_front_url,ingredients_text,"
                "ingredients_text_es,ingredients_text_en,ingredients,"
                "nutriscore_grade,categories"
            )
        }

        for search_url in self.SEARCH_URLS:
            try:
                response = requests.get(
                    search_url,
                    headers=self.headers,
                    params=params,
                    timeout=self.timeout
                )
                if response.status_code != 200:
                    continue

                data = response.json()
                products_raw = data.get("products", [])
                normalized_products = []

                for p in products_raw:
                    # Priorizar nombres e ingredientes en español si existen
                    name = (
                        p.get("product_name_es")
                        or p.get("product_name")
                        or p.get("product_name_en")
                        or "Producto sin nombre"
                    )
                    ingredients_text = (
                        p.get("ingredients_text_es")
                        or p.get("ingredients_text")
                        or p.get("ingredients_text_en")
                        or ""
                    )
                    image = p.get("image_url") or p.get("image_front_url") or ""

                    # Extraer lista estructurada de ingredientes si existe
                    raw_ingredients_list = p.get("ingredients", [])
                    parsed_ingredients = [
                        ing.get("text") for ing in raw_ingredients_list if ing.get("text")
                    ]

                    # Si no hay lista estructurada, partir el texto por comas
                    if not parsed_ingredients and ingredients_text:
                        parsed_ingredients = [
                            i.strip() for i in ingredients_text.split(",") if i.strip()
                        ]

                    normalized_products.append({
                        "id": p.get("code", ""),
                        "name": name,
                        "brand": p.get("brands", "Marca no especificada"),
                        "image_url": image,
                        "ingredients_text": ingredients_text,
                        "ingredients_list": parsed_ingredients,
                        "nutriscore": p.get("nutriscore_grade", "N/A").upper(),
                        "categories": p.get("categories", "")
                    })

                return normalized_products

            except requests.RequestException as e:
                logger.warning(f"Aviso consultando Open Food Facts ({search_url}): {e}")
                continue

        logger.error("Error consultando Open Food Facts en todos los mirrors disponibles.")
        return []

    def get_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Obtiene un producto específico a partir de su código de barras."""
        for product_url in self.PRODUCT_URLS:
            url = f"{product_url}/{barcode}.json"
            try:
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                if response.status_code != 200:
                    continue

                data = response.json()
                if data.get("status") != 1:
                    return None

                p = data.get("product", {})
                return {
                    "id": p.get("code", barcode),
                    "name": p.get("product_name_es") or p.get("product_name", "Producto desconocido"),
                    "brand": p.get("brands", "Marca no especificada"),
                    "image_url": p.get("image_url") or p.get("image_front_url") or "",
                    "ingredients_text": p.get("ingredients_text_es") or p.get("ingredients_text", ""),
                    "nutriscore": p.get("nutriscore_grade", "N/A").upper()
                }
            except requests.RequestException as e:
                logger.warning(f"Aviso consultando Open Food Facts ({url}): {e}")
                continue

        return None
