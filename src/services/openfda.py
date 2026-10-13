import logging
from typing import Any, Dict, List
import requests
from src.config import settings

logger = logging.getLogger(__name__)


class OpenFDAService:
    FOOD_ENFORCEMENT_URL = "https://api.fda.gov/food/enforcement.json"
    DRUG_ENFORCEMENT_URL = "https://api.fda.gov/drug/enforcement.json"
    DRUG_LABEL_URL = "https://api.fda.gov/drug/label.json"

    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT
        self.api_key = settings.OPENFDA_API_KEY

    def _build_params(self, search_query: str, limit: int = 3) -> Dict[str, Any]:
        params = {"search": search_query, "limit": limit}
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    def search_food_recalls(self, term: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Busca retiros de alimentos por nombre de empresa o descripción de producto."""
        clean_term = term.replace('"', "")
        query = f'(recalling_firm:"{clean_term}"+OR+product_description:"{clean_term}")'
        params = self._build_params(query, limit)

        try:
            response = requests.get(self.FOOD_ENFORCEMENT_URL, params=params, timeout=self.timeout)
            if response.status_code == 200:
                results = response.json().get("results", [])
                return [
                    {
                        "recall_number": r.get("recall_number"),
                        "recalling_firm": r.get("recalling_firm"),
                        "product_description": r.get("product_description"),
                        "reason_for_recall": r.get("reason_for_recall"),
                        "status": r.get("status"),
                        "classification": r.get("classification"),
                        "recall_initiation_date": r.get("recall_initiation_date")
                    }
                    for r in results
                ]
            return []
        except requests.RequestException as e:
            logger.warning(f"Aviso en consulta openFDA Food Enforcement: {e}")
            return []

    def search_drug_recalls(self, term: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Busca retiros de medicamentos por nombre o laboratorio fabricante."""
        clean_term = term.replace('"', "")
        query = f'(recalling_firm:"{clean_term}"+OR+product_description:"{clean_term}")'
        params = self._build_params(query, limit)

        try:
            response = requests.get(self.DRUG_ENFORCEMENT_URL, params=params, timeout=self.timeout)
            if response.status_code == 200:
                results = response.json().get("results", [])
                return [
                    {
                        "recall_number": r.get("recall_number"),
                        "recalling_firm": r.get("recalling_firm"),
                        "product_description": r.get("product_description"),
                        "reason_for_recall": r.get("reason_for_recall"),
                        "status": r.get("status"),
                        "classification": r.get("classification")
                    }
                    for r in results
                ]
            return []
        except requests.RequestException as e:
            logger.warning(f"Aviso en consulta openFDA Drug Enforcement: {e}")
            return []

    def evaluate_brand_safety(
        self,
        product_name: str,
        brand_name: str,
        item_type: str = "food"
    ) -> Dict[str, Any]:
        """
        Determina el semáforo regulatorio de la marca y producto:
        - RED: Este producto específico tiene orden de retiro activa.
        - YELLOW: La marca tiene retiros de otros productos (sospecha/contaminación).
        - GREEN: Sin registros de recalls encontrados.
        """
        search_fn = self.search_food_recalls if item_type == "food" else self.search_drug_recalls

        # 1. Buscar coincidencias específicas del producto
        product_recalls = search_fn(product_name, limit=3)

        # 2. Buscar si la marca tiene historial de retiros
        brand_recalls = []
        if brand_name and brand_name.lower() not in ["marca no especificada", "generic", ""]:
            brand_recalls = search_fn(brand_name, limit=5)

        if product_recalls:
            return {
                "badge": "🔴 ROJO",
                "status": "DANGER",
                "summary": "Este producto coincide con registros oficiales de retiro del mercado (Recall).",
                "details": product_recalls
            }

        if brand_recalls:
            return {
                "badge": "🟡 AMARILLO",
                "status": "WARNING",
                "summary": "El producto no está retirado, pero el fabricante tiene retiros en otras líneas.",
                "details": brand_recalls[:2]
            }

        return {
            "badge": "🟢 VERDE",
            "status": "SAFE",
            "summary": "Sin registros de recalls activos encontrados para esta marca o producto.",
            "details": []
        }
