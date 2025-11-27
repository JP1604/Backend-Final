# AI Assistant - GitHub Copilot Integration

## Descripción

El módulo 9 del sistema es un **Asistente Creativo con IA** que ayuda a profesores y administradores a crear desafíos (challenges) de programación. Este asistente utiliza un **generador inteligente local** que crea sugerencias completas basadas en patrones de programación competitiva y está integrado directamente en el flujo de creación de challenges.

## Funcionalidades

### 1. Generación de Ideas de Retos
- El administrador/profesor ingresa un tema o categoría (ej: "Árboles binarios", "Búsqueda binaria")
- La IA sugiere retos completos con:
  - Título descriptivo
  - Descripción del problema
  - Formato de entrada y salida
  - Ejemplos de casos de prueba
  - Nivel de dificultad
  - Tags relevantes

### 2. Propuesta de Casos de Prueba
- Genera automáticamente casos de prueba con entrada y salida esperada
- Separa casos públicos (visibles para estudiantes) y privados (solo para evaluación)
- Los casos sirven como base para los archivos .in y .out

### 3. Gestión de Test Cases
- Después de crear un challenge, se abre automáticamente el **Test Case Manager**
- Permite:
  - Agregar, editar y eliminar casos de prueba
  - Alternar visibilidad (público/privado)
  - Ver resumen de casos públicos vs privados
  - Validar que haya al menos un caso de prueba

## Cómo Funciona el Generador de IA

El sistema incluye un **generador inteligente integrado** que:

- ✅ **Funciona sin conexión:** No requiere API externa ni tokens
- ✅ **Respuestas instantáneas:** Genera sugerencias en menos de 1 segundo
- ✅ **Patrones profesionales:** Basado en plataformas como Codeforces, LeetCode, HackerRank
- ✅ **Detecta contexto:** Analiza el tema y genera desafíos relevantes
- ✅ **Múltiples categorías:** Arrays, Strings, Sorting, Búsqueda, Árboles, DP, Clima, Matemáticas, etc.
- ✅ **Casos de prueba completos:** Genera test cases públicos y privados automáticamente

### Categorías Soportadas:

| Tema | Ejemplo de Desafío |
|------|-------------------|
| Arrays / Arreglos | Suma de elementos, búsqueda de máximo |
| Strings / Cadenas | Palíndromos, validación de texto |
| Sorting / Ordenamiento | Ordenar array ascendente/descendente |
| Binary Search / Búsqueda | Búsqueda binaria en array ordenado |
| Trees / Árboles | Altura de árbol binario, recorridos |
| Dynamic Programming / DP | Fibonacci, subsecuencias |
| Clima / Weather | Análisis de temperaturas, promedios |
| Math / Matemáticas | Calculadora, operaciones aritméticas |
| **Cualquier otro tema** | Genera desafío genérico adaptado |

## Configuración (Opcional)

### Integración con APIs Externas de IA

Si en el futuro deseas integrar con servicios como OpenAI, Anthropic Claude, o Google Gemini:

1. **Obtener API Key** del servicio deseado
2. **Configurar en variables de entorno** (.env)
3. **Modificar AIAssistant.jsx** para hacer la llamada HTTP
4. **Mantener generador local** como fallback

**Nota:** El generador local actual es completamente funcional y recomendado para desarrollo y producción sin costos adicionales.

## Configuración Anterior de GitHub Copilot (Deprecated)

### ⚠️ Importante: GitHub Copilot API No Disponible

GitHub Copilot **no tiene una API REST pública**. Solo funciona a través de:
- Extensión de VS Code
- Extensión de JetBrains
- GitHub CLI (limitado)

Por esto, el sistema usa un **generador local inteligente** que:
- No requiere tokens ni autenticación
- Funciona offline
- Genera sugerencias de alta calidad
- Es más rápido y confiable

Si aún así deseas experimentar con GitHub Student Pack:

1. **Verificar acceso:**
   - Ve a [GitHub Education](https://education.github.com/)
   - Activa GitHub Student Developer Pack
   - Esto incluye GitHub Copilot gratis para VS Code

2. **Usar en VS Code:**
   - Instala la extensión "GitHub Copilot" en VS Code
   - Autentica con tu cuenta de estudiante
   - Copilot te ayudará mientras escribes código

**Sin embargo, este proyecto usa su propio generador que no requiere nada de esto.**

## Uso del Asistente

### Paso 1: Crear un Challenge

1. Entra a un curso como profesor/administrador
2. Click en **"Create Challenge"**
3. Verás el botón **"AI Assistant"** con icono de estrella

### Paso 2: Usar el AI Assistant

1. Click en **"AI Assistant"**
2. Ingresa un tema o categoría (ejemplos):
   - "dame un reto que tenga que ver con el clima"
   - "Árboles binarios"
   - "Algoritmos de ordenamiento"
   - "Búsqueda binaria"
   - "Programación dinámica"
   - "Grafos y caminos"
   - "temperatura"
   - "cadenas y palíndromos"
   - "matemáticas básicas"
3. Click en **"Generate"**
4. La IA generará una sugerencia completa con:
   - Título del reto
   - Descripción detallada
   - Ejemplos de entrada/salida
   - Casos de prueba públicos y privados
   - Tags y nivel de dificultad

### Paso 3: Aplicar la Sugerencia

1. Revisa la sugerencia generada
2. Si quieres otra versión, click en **"Regenerate"**
3. Click en **"Apply Suggestion"** para usar los datos
4. Los campos del formulario se llenarán automáticamente
5. Puedes editar cualquier campo antes de crear

### Paso 4: Gestionar Test Cases

1. Después de crear el challenge, se abre automáticamente **"Test Case Manager"**
2. Los casos de prueba sugeridos por la IA ya están cargados
3. Puedes:
   - **Agregar más casos:** Click en "Add Test Case"
   - **Editar casos:** Modifica input y expected output
   - **Eliminar casos:** Click en el ícono de basura
   - **Cambiar visibilidad:** Click en el ícono de ojo
     - 👁️ Público (visible para estudiantes)
     - 👁️‍🗨️ Privado (solo para evaluación)
4. Click en **"Save Test Cases"** para guardar

## Validaciones

### El Asistente NO reemplaza al profesor:
- ✅ Las sugerencias deben ser **revisadas y validadas**
- ✅ El profesor puede **editar cualquier campo**
- ✅ Los casos de prueba deben ser **verificados**
- ✅ El profesor tiene **control total** sobre el contenido

### Validaciones Técnicas:
- Al menos 1 caso de prueba es requerido
- El expected output es obligatorio
- El input es opcional (si el problema no requiere entrada)
- No se puede guardar sin validar los campos requeridos

## Arquitectura del Sistema

### Componentes Creados:

1. **AIAssistant.jsx** - Componente principal del asistente
   - Interfaz para ingresar temas
   - Llamadas a GitHub Copilot API
   - Generador local de fallback
   - Display de sugerencias

2. **TestCaseManager.jsx** - Gestor de casos de prueba
   - CRUD de test cases
   - Toggle de visibilidad público/privado
   - Validaciones de campos
   - Integración con API backend

3. **Estilos CSS:**
   - `AIAssistant.css` - Estilos del asistente
   - `TestCaseManager.css` - Estilos del gestor

4. **API Integration:**
   - Nueva API `testCasesAPI` en `services/api.js`
   - Endpoints para crear, listar, actualizar y eliminar test cases

### Flujo de Datos:

```
Usuario ingresa tema
    ↓
AI Assistant genera sugerencia
    ↓
Usuario aplica sugerencia
    ↓
Formulario se llena automáticamente
    ↓
Usuario crea challenge
    ↓
Test Case Manager se abre automáticamente
    ↓
Casos de prueba (de IA) precargados
    ↓
Usuario valida/edita casos
    ↓
Guarda test cases → Backend
```

## Ventajas del Sistema

1. **Acelera la creación de contenido:** Reduce tiempo de 30+ minutos a 5 minutos
2. **Mejora la calidad:** Sugerencias consistentes y bien estructuradas
3. **Facilita la validación:** Casos de prueba pre-generados
4. **Flexibilidad:** El profesor siempre tiene control total
5. **Escalabilidad:** Fácil generar múltiples desafíos similares

## Notas Importantes

⚠️ **Generador Local vs APIs Externas:**
- El sistema actual usa un generador local inteligente
- **No requiere** tokens, API keys, ni conexión a internet
- Las sugerencias son de alta calidad y basadas en patrones profesionales
- Para proyectos en producción, esto es **más confiable** que depender de APIs externas

⚠️ **Validación Manual:**
- Siempre revisar las sugerencias generadas
- Verificar que los test cases sean correctos
- Ajustar dificultad según el nivel del curso
- El generador es una **herramienta de asistencia**, no un reemplazo del profesor

⚠️ **Privacidad y Seguridad:**
- Ningún dato se envía a servicios externos
- Todo el procesamiento es local en el navegador
- Ideal para entornos educativos con restricciones de privacidad

## Próximas Mejoras

- [ ] Integración con múltiples modelos de IA (OpenAI, Claude, etc.)
- [ ] Histórico de sugerencias generadas
- [ ] Templates personalizables por profesor
- [ ] Validación automática de casos de prueba con scripts
- [ ] Sugerencias basadas en desafíos anteriores del curso
