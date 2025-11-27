import { useState } from 'react';
import { Sparkles, Loader, Check, X, RefreshCw } from 'lucide-react';
import './AIAssistant.css';

const AIAssistant = ({ onApplySuggestion, currentChallenge }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [topic, setTopic] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [error, setError] = useState('');
  const [selectedSuggestion, setSelectedSuggestion] = useState(null);

  // 🔑 API config
  const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY;
  const OPENAI_PROJECT_ID = import.meta.env.VITE_OPENAI_PROJECT_ID; // opcional
  const OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions';
  const OPENAI_MODEL = 'gpt-4.1-nano';

  const generateSuggestions = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic or category');
      return;
    }

    if (!OPENAI_API_KEY) {
      setError('Falta la API key. Configura VITE_OPENAI_API_KEY en tu archivo .env');
      return;
    }

    setLoading(true);
    setError('');
    setSuggestions([]);

    try {
      console.log('OpenAI: Generating challenge for:', topic);
      const result = await generateWithOpenAI(topic);

      if (result && result.length > 0) {
        setSuggestions(result);
        setSelectedSuggestion(0);
      } else {
        setError('La IA no devolvió ninguna sugerencia.');
      }
    } catch (err) {
      console.error('AI Generation Error:', err);
      setError(err.message || 'Error llamando a OpenAI');
    } finally {
      setLoading(false);
    }
  };

  const generateWithOpenAI = async (topic) => {
    const prompt = `
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
"${topic}"

El reto debe:
- Ser adecuado para un curso universitario de programación / backend.
- Poder resolverse en alguno de estos lenguajes: Java, Python, Node.js o C++.
- Tener una dificultad clara (easy, medium o hard).
- Usar entradas/salidas por consola estándar (stdin / stdout).

====================
FORMATO DEL RETO
====================
Debes generar EXACTAMENTE UN reto completo con:

1) Un título claro y específico.
2) Un enunciado detallado que incluya secciones marcadas:
   - **Descripción:** contexto y objetivo del problema.
   - **Entrada:** formato detallado de los datos de entrada.
   - **Salida:** formato exacto de la salida.
   - **Restricciones:** límites numéricos, tamaño máximo de entrada, 
     tiempo límite (en milisegundos) y memoria límite (en MB).
3) Una dificultad: easy, medium o hard.
4) Una lista de tags relevantes (ej: ["arrays", "sorting", "greedy"]).
5) Ejemplos de uso con entrada/salida y explicación.
6) Casos de prueba pensados para archivos .in/.out del juez online:
   - Varios casos simples y otros más complejos.
   - Algunos públicos (is_hidden = false) y otros ocultos (is_hidden = true).

====================
FORMATO DE SALIDA (OBLIGATORIO)
====================
Devuelve ÚNICAMENTE un JSON VÁLIDO, SIN COMENTARIOS NI TEXTO EXTRA,
con la siguiente estructura EXACTA:

{
  "title": "Título específico del desafío",
  "description": "Enunciado completo del problema. Debe incluir secciones con encabezados: \\n\\n**Descripción:**\\n...\\n\\n**Entrada:**\\n...\\n\\n**Salida:**\\n...\\n\\n**Restricciones:**\\n- ...",
  "difficulty": "easy",
  "tags": ["tag1", "tag2", "tag3"],
  "examples": [
    {
      "input": "ejemplo de entrada real\\npueden ser varias líneas",
      "output": "salida esperada real\\npueden ser varias líneas",
      "explanation": "explica por qué la salida es correcta"
    },
    {
      "input": "otro ejemplo de entrada",
      "output": "otra salida esperada",
      "explanation": "otra explicación breve"
    }
  ],
  "testCases": [
    {
      "input": "caso_de_prueba_1",
      "expected_output": "salida_1",
      "is_hidden": false
    },
    {
      "input": "caso_de_prueba_2",
      "expected_output": "salida_2",
      "is_hidden": false
    },
    {
      "input": "caso_de_prueba_3_mas_complejo",
      "expected_output": "salida_3",
      "is_hidden": true
    },
    {
      "input": "caso_de_prueba_4_borde",
      "expected_output": "salida_4",
      "is_hidden": true
    },
    {
      "input": "caso_de_prueba_5_grande",
      "expected_output": "salida_5",
      "is_hidden": true
    }
  ],
  "limits": {
    "timeLimitMs": 1500,
    "memoryLimitMb": 256
  }
}

REGLAS FINALES:
- NO envuelvas el JSON en bloques de código markdown (no uses \`\`\`).
- NO añadas explicaciones fuera del JSON.
- Asegúrate de que sea JSON sintácticamente válido.
`;

    // Construimos headers
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${OPENAI_API_KEY}`,
    };

    // Si estás usando una clave sk-proj-..., envía también el project id
    if (OPENAI_PROJECT_ID) {
      headers['OpenAI-Project'] = OPENAI_PROJECT_ID;
    }

    const response = await fetch(OPENAI_API_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        model: OPENAI_MODEL,
        messages: [
          {
            role: 'system',
            content:
              'Eres un experto en crear desafíos de programación. Siempre respondes con JSON válido.',
          },
          {
            role: 'user',
            content: prompt,
          },
        ],
        temperature: 0.7,
        max_tokens: 2000,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('OpenAI API Error:', errorData);

      if (response.status === 401) {
        throw new Error(
          '401 Unauthorized: revisa tu API key (VITE_OPENAI_API_KEY) y, si es sk-proj-..., también VITE_OPENAI_PROJECT_ID.'
        );
      }

      if (response.status === 429) {
        throw new Error('Límite de peticiones excedido (429). Intenta de nuevo más tarde.');
      }

      throw new Error(
        `OpenAI API error: ${response.status} - ${
          errorData.error?.message || 'Unknown error'
        }`
      );
    }

    const data = await response.json();
    console.log('OpenAI API Full Response:', data);

    const text = data.choices?.[0]?.message?.content;
    if (!text) {
      throw new Error('Respuesta vacía de OpenAI');
    }

    console.log('OpenAI Raw Text:', text);

    // Intentamos extraer el JSON (por si viene envuelto en ```json ... ```)
    let jsonText = text;
    const jsonMatch = text.match(/```json\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
      jsonText = jsonMatch[1];
    } else {
      const cleanMatch = text.match(/\{[\s\S]*\}/);
      if (cleanMatch) jsonText = cleanMatch[0];
    }

    const suggestion = JSON.parse(jsonText);
    console.log('✅ OpenAI generated suggestion:', suggestion);

    return [suggestion];
  };

  const applySuggestion = () => {
    if (selectedSuggestion === null || !suggestions[selectedSuggestion]) return;
    const suggestion = suggestions[selectedSuggestion];
    onApplySuggestion(suggestion);
    setIsOpen(false);
    setSuggestions([]);
    setTopic('');
  };

  const regenerateSuggestion = () => {
    generateSuggestions();
  };

  return (
    <>
      {/* Botón para abrir/cerrar el asistente */}
      <button
        type="button"
        className="ai-assistant-toggle"
        onClick={() => setIsOpen(!isOpen)}
        title="Open AI Assistant"
      >
        <Sparkles size={20} />
        AI Assistant
      </button>

      {isOpen && (
        <div className="modal-overlay" onClick={() => setIsOpen(false)}>
          <div
            className="modal-content ai-assistant-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <div className="ai-header-title">
                <Sparkles size={24} className="ai-icon" />
                <h3>AI Challenge Assistant</h3>
              </div>
              <button className="btn-close" onClick={() => setIsOpen(false)}>
                <X size={20} />
              </button>
            </div>

            <div className="ai-assistant-content">
              {/* Input de tema */}
              <div className="ai-input-section">
                <label>What topic or category do you want to create a challenge about?</label>
                <div className="ai-input-group">
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g., Binary Trees, Sorting Algorithms, Dynamic Programming..."
                    className="ai-topic-input"
                    onKeyDown={(e) => e.key === 'Enter' && generateSuggestions()}
                  />
                  <button
                    type="button"
                    onClick={generateSuggestions}
                    disabled={loading || !topic.trim()}
                    className="btn-generate"
                  >
                    {loading ? <Loader size={18} className="spin" /> : <Sparkles size={18} />}
                    Generate
                  </button>
                </div>
                {error && <div className="ai-error">{error}</div>}
              </div>

              {/* Resultado de la IA */}
              {suggestions.length > 0 && (
                <div className="ai-suggestions">
                  <div className="ai-suggestion-header">
                    <h4>Generated Suggestion</h4>
                    <button
                      type="button"
                      onClick={regenerateSuggestion}
                      className="btn-regenerate"
                      title="Generate another suggestion"
                    >
                      <RefreshCw size={16} />
                      Regenerate
                    </button>
                  </div>

                  {suggestions.map((suggestion, index) => (
                    <div
                      key={index}
                      className={`ai-suggestion-card ${
                        selectedSuggestion === index ? 'selected' : ''
                      }`}
                      onClick={() => setSelectedSuggestion(index)}
                    >
                      <div className="suggestion-title">
                        <h5>{suggestion.title}</h5>
                        <span className={`difficulty-badge ${suggestion.difficulty}`}>
                          {suggestion.difficulty}
                        </span>
                      </div>

                      <div className="suggestion-description">{suggestion.description}</div>

                      <div className="suggestion-tags">
                        {suggestion.tags?.map((tag, i) => (
                          <span key={i} className="tag">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}

                  <div className="ai-actions">
                    <button
                      type="button"
                      onClick={applySuggestion}
                      className="btn-apply"
                      disabled={selectedSuggestion === null}
                    >
                      <Check size={18} />
                      Apply Suggestion
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setSuggestions([]);
                        setSelectedSuggestion(null);
                      }}
                      className="btn-discard"
                    >
                      <X size={18} />
                      Discard
                    </button>
                  </div>
                </div>
              )}

              {/* Mensaje inicial */}
              {suggestions.length === 0 && !loading && (
                <div className="ai-info">
                  <Sparkles size={48} className="ai-info-icon" />
                  <h4>How the AI Assistant helps you:</h4>
                  <ul>
                    <li>🎯 Generate challenge ideas based on topics</li>
                    <li>📝 Create problem descriptions and constraints</li>
                    <li>✅ Propose example test cases with input/output</li>
                    <li>🏷️ Suggest relevant tags and difficulty levels</li>
                  </ul>
                  <p className="ai-disclaimer">
                    <strong>Note:</strong> AI suggestions should be reviewed and validated by the
                    instructor before publishing.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AIAssistant;
