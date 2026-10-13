# Health Ingredient Agent 🥗

Un agente inteligente para el análisis de salud y desglose de ingredientes alimenticios y fármacos, desarrollado para **GatewayHacks 2026**.

## 🚀 Características
- **Análisis de Ingredientes:** Consulta y cruce de datos con OpenFoodFacts y OpenFDA.
- **Explicación Accesible ("Nivel 10 años"):** Traduce términos químicos y aditivos complejos a explicaciones simples y comprensibles.
- **Alertas de Salud y Alérgenos:** Detección de riesgos potenciales, niveles de azúcar, sodio, ultraprocesados y aditivos de riesgo.
- **Interfaz Streamlit:** Experiencia de usuario interactiva y responsiva.

## 📦 Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/Obumbratio/health-ingredient-agent.git
cd health-ingredient-agent
```

2. Crea y activa tu entorno virtual:
```bash
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

4. Configura las variables de entorno:
```bash
cp .env.example .env
```
Edita `.env` con tus claves correspondientes (`LLM_API_KEY`, opcional `OPENFDA_API_KEY`).

5. Ejecuta la aplicación:
```bash
streamlit run app.py
```
