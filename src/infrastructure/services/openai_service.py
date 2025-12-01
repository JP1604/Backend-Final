"""
OpenAI Service for AI Assistant
Handles integration with OpenAI API to generate challenge suggestions
"""
import os
import json
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API to generate programming challenges"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.project_id = os.getenv("OPENAI_PROJECT_ID")  # Optional
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not configured in environment variables")
    
    async def generate_challenge_suggestion(self, topic: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a programming challenge suggestion based on a given topic.
        
        Args:
            topic: The topic or category for the challenge (e.g., "Binary Trees")
            language: Optional preferred programming language
            
        Returns:
            Dictionary containing challenge details including title, description, 
            test cases, examples, etc.
            
        Raises:
            ValueError: If API key is not configured
            Exception: If OpenAI API call fails
        """
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            )
        
        prompt = self._build_prompt(topic, language)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                # Add project ID if configured (for sk-proj-... keys)
                if self.project_id:
                    headers["OpenAI-Project"] = self.project_id
                
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Eres un experto en crear desafíos de programación para "
                                "cursos universitarios. Siempre respondes con JSON válido."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_completion_tokens": 2500,
                    "response_format": {"type": "json_object"}
                }
                
                logger.info(f"Sending request to OpenAI for topic: {topic}")
                response = await client.post(self.api_url, headers=headers, json=payload)
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"OpenAI API error {response.status_code}: {error_detail}")
                    
                    if response.status_code == 401:
                        raise Exception(
                            "OpenAI API authentication failed. Check your API key."
                        )
                    elif response.status_code == 429:
                        raise Exception(
                            "OpenAI API rate limit exceeded. Please try again later."
                        )
                    else:
                        raise Exception(
                            f"OpenAI API error: {response.status_code} - {error_detail}"
                        )
                
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if not content:
                    raise Exception("Empty response from OpenAI API")
                
                # Parse JSON response
                suggestion = json.loads(content)
                logger.info(f"Successfully generated challenge suggestion: {suggestion.get('title')}")
                
                return suggestion
                
        except httpx.TimeoutException:
            logger.error("OpenAI API request timed out")
            raise Exception("Request to OpenAI API timed out. Please try again.")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            raise Exception("Invalid JSON response from OpenAI API")
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise
    
    def _build_prompt(self, topic: str, language: Optional[str] = None) -> str:
        """Build the prompt for OpenAI API"""
        
        language_constraint = ""
        if language:
            language_constraint = f"\n- El reto debe estar optimizado para resolverse en {language.upper()}."
        
        return f"""
Eres el ASISTENTE CREATIVO de una plataforma de juez online universitario para evaluar algoritmos.
La plataforma sigue Clean Architecture y se usa en cursos de programación. 
Los profesores (ADMIN) crean retos y casos de prueba; los estudiantes (STUDENT) solo ven retos publicados 
y envían sus soluciones, que se ejecutan en contenedores aislados con límites de tiempo y memoria.

Tu ÚNICO trabajo es ayudar al PROFESOR a crear NUEVOS RETOS de programación. 
NO evalúas código, solo generas enunciados y casos de prueba que luego serán revisados por humanos.

====================
TEMA DEL RETO
====================
Crea un reto de programación basado en el siguiente tema o categoría:
"{topic}"{language_constraint}

El reto debe:
- Ser adecuado para un curso universitario de programación / backend.
- Poder resolverse en alguno de estos lenguajes: Java, Python, Node.js o C++.
- Tener una dificultad clara (Easy, Medium o Hard).
- Usar entradas/salidas por consola estándar (stdin / stdout).
- Incluir restricciones claras de tiempo y memoria.

====================
FORMATO DEL RETO
====================
Debes generar EXACTAMENTE UN reto completo con:

1) Un título claro y específico (máximo 100 caracteres).
2) Un enunciado detallado que incluya secciones marcadas:
   - **Descripción:** contexto y objetivo del problema.
   - **Entrada:** formato detallado de los datos de entrada (línea por línea).
   - **Salida:** formato exacto de la salida esperada.
   - **Restricciones:** límites numéricos, tamaño máximo de entrada.
   - **Ejemplos:** al menos 2 ejemplos con explicación.
3) Una dificultad: "Easy", "Medium" o "Hard" (capitalizado).
4) Una lista de 3-5 tags relevantes (ej: ["arrays", "sorting", "greedy"]).
5) Ejemplos de uso con entrada/salida y explicación detallada.
6) Casos de prueba pensados para archivos .in/.out del juez online:
   - Al menos 5 casos de prueba
   - Los primeros 2 deben ser públicos (is_hidden = false)
   - Los siguientes 3+ deben ser ocultos (is_hidden = true)
   - Incluir casos borde, casos grandes, casos con valores mínimos/máximos

====================
FORMATO DE SALIDA (OBLIGATORIO)
====================
Devuelve ÚNICAMENTE un JSON VÁLIDO, SIN COMENTARIOS NI TEXTO EXTRA,
con la siguiente estructura EXACTA:

{{
  "title": "Título específico del desafío (máx 100 chars)",
  "description": "Enunciado completo del problema con secciones:\\n\\n**Descripción:**\\n...\\n\\n**Entrada:**\\n...\\n\\n**Salida:**\\n...\\n\\n**Restricciones:**\\n- Límites numéricos\\n- Tiempo límite: {{timeLimitMs}}ms\\n- Memoria límite: {{memoryLimitMb}}MB\\n\\n**Ejemplos:**\\n...explicaciones...",
  "difficulty": "Easy|Medium|Hard",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "examples": [
    {{
      "input": "ejemplo de entrada\\npueden ser varias líneas",
      "output": "salida esperada\\npueden ser varias líneas",
      "explanation": "Explicación clara de por qué esta es la salida correcta"
    }},
    {{
      "input": "segundo ejemplo",
      "output": "segunda salida",
      "explanation": "Segunda explicación"
    }}
  ],
  "testCases": [
    {{
      "input": "caso_simple_1",
      "expected_output": "salida_1",
      "is_hidden": false,
      "order_index": 1
    }},
    {{
      "input": "caso_simple_2",
      "expected_output": "salida_2",
      "is_hidden": false,
      "order_index": 2
    }},
    {{
      "input": "caso_complejo_3",
      "expected_output": "salida_3",
      "is_hidden": true,
      "order_index": 3
    }},
    {{
      "input": "caso_borde_4",
      "expected_output": "salida_4",
      "is_hidden": true,
      "order_index": 4
    }},
    {{
      "input": "caso_grande_5",
      "expected_output": "salida_5",
      "is_hidden": true,
      "order_index": 5
    }}
  ],
  "limits": {{
    "timeLimitMs": 1500,
    "memoryLimitMb": 256
  }}
}}

REGLAS FINALES:
- NO envuelvas el JSON en bloques de código markdown.
- NO añadas explicaciones fuera del JSON.
- Asegúrate de que sea JSON sintácticamente válido.
- Los valores de difficulty deben ser: "Easy", "Medium" o "Hard" (con mayúscula inicial).
- Incluye MÍNIMO 5 casos de prueba.
- Los primeros 2 casos deben tener is_hidden: false.
- Los casos deben estar ordenados por order_index.
"""
