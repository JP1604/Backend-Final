#  Online Judge - Semana 2 (SIMPLIFICADO)

Una plataforma simple para evaluar algoritmos, como HackerRank pero más fácil de entender.

##  ¿Qué hace esta plataforma?

1. **Profesores** pueden crear problemas de programación
2. **Estudiantes** pueden resolver los problemas enviando código
3. **El sistema** evalúa automáticamente el código y da un resultado

##  Estructura SIMPLE del proyecto

```
src/
├── domain/              # Las reglas del negocio
│   ├── entities/        # Los objetos principales (User, Challenge, Submission)
│   └── repositories/    # Interfaces para guardar datos
├── application/         # La lógica de la aplicación
│   ├── use_cases/      # Las acciones que se pueden hacer
│   └── dtos/           # Los formatos de datos
├── infrastructure/      # Conexiones externas
│   ├── persistence/    # Base de datos
│   ├── repositories/   # Implementaciones para guardar datos
│   └── services/       # Servicios externos (JWT, Redis)
├── presentation/        # La API REST
│   ├── controllers/    # Los endpoints de la API
│   └── middleware/     # Autenticación
└── workers/            # Procesadores de código
```

##  Tecnologías usadas

- **FastAPI**: Framework para crear la API
- **PostgreSQL**: Base de datos
- **Redis**: Cola de mensajes
- **Celery**: Procesador de tareas
- **Docker**: Para ejecutar todo junto

##  Cómo ejecutar

### Opción 1: Con Docker (RECOMENDADO)

```bash
# 1. Levantar todos los servicios
docker-compose up -d



# 3. Ver la API en el navegador
# Abrir: http://localhost:8008/docs




##  Endpoints principales

###  Autenticación
- `POST /auth/login` - Iniciar sesión

###  Challenges (Problemas)
- `GET /challenges/` - Ver todos los problemas
- `POST /challenges/` - Crear un problema (solo profesores)

###  Submissions (Envíos)
- `POST /submissions/` - Enviar solución a un problema

##  Usuarios de prueba

Se crean automáticamente estos usuarios:

- **Admin**: admin@example.com / password
- **Profesor**: professor@example.com / password  
- **Estudiante**: student@example.com / password

##  ¿Cómo funciona?

1. **Profesor** crea un challenge (problema)
2. **Estudiante** se loguea y ve los challenges
3. **Estudiante** envía su código como solución
4. **Worker** procesa el código (simula ejecución)
5. **Sistema** devuelve el resultado (ACCEPTED, WRONG_ANSWER, etc.)



