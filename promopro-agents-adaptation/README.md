# Promocionales Agents - Sistema de Chat para Productos Promocionales

Este es un sistema de chat de agentes de IA adaptado para una empresa de productos promocionales, basado en el demo de OpenAI Customer Service Agents.

## Estructura del Proyecto

```
promopro-agents-adaptation/
├── backend/                 # Backend Python con FastAPI
│   ├── main.py             # Orquestación principal de agentes
│   ├── tools.py            # Herramientas de búsqueda CSV
│   ├── file_uploader.py    # Utilidad para subir CSV a OpenAI
│   ├── requirements.txt    # Dependencias Python
│   └── env.example        # Variables de entorno de ejemplo
├── frontend/               # Frontend Next.js
│   ├── app/               # Aplicación Next.js 14
│   ├── components/        # Componentes React
│   │   ├── business-unit-selector.tsx  # Selector de unidades de negocio
│   │   └── Chat.tsx       # Componente de chat adaptado
│   └── ...
└── data/                  # Archivos CSV de productos
    ├── promo.csv          # Productos promocionales individuales
    └── suitup.csv         # Kits de productos promocionales
```

## Características

### Unidades de Negocio

1. **Promoselect** - Productos promocionales individuales
   - Busca en base de datos de productos individuales
   - Campos: sku, precio, categorias, nombre, descripcion, medidas, imagenes_url
   - Presenta 3 opciones con formato: nombre, descripción, precio + imagen

2. **SuitUp** - Kits de productos promocionales
   - Busca en base de datos de kits especializados
   - Campos: precio, nombre, descripcion, productos, imagen
   - Presenta 3 opciones con formato: nombre, descripción, productos, precio + imagen

### Agentes de IA

- **Agente de Triaje**: Saluda y muestra selector de unidades de negocio
- **Agente Promoselect**: Especialista en productos individuales
- **Agente SuitUp**: Especialista en kits promocionales

### Estrategia de Búsqueda

El sistema implementa una **búsqueda híbrida** optimizada:

1. **Búsqueda Precisa (Primaria)**: 
   - Filtrado directo con pandas en memoria
   - Búsqueda por palabras clave, categoría y rango de precios
   - Sin costo adicional, respuesta instantánea

2. **Búsqueda Semántica (Fallback)**:
   - Se activa cuando la búsqueda precisa no encuentra resultados
   - Maneja consultas vagas como "regalo corporativo elegante"
   - Búsqueda por palabras individuales como respaldo

Esta estrategia elimina la dependencia costosa de Code Interpreter ($0.03/sesión) mientras mantiene capacidades de búsqueda avanzadas.

## Configuración

### 1. Backend

1. Crear archivo `.env` basado en `env.example`:
```bash
cd backend
cp env.example .env
```

2. Configurar las variables de entorno:
```env
OPENAI_API_KEY=tu_clave_api_de_openai
PROMO_CSV_PATH=../data/promo.csv
SUITUP_CSV_PATH=../data/suitup.csv
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```
   
   Las dependencias incluyen: pandas, fastapi, openai-agents, pydantic, uvicorn

4. Ejecutar el servidor:
```bash
python -m uvicorn api:app --reload --port 8000
```

### 2. Frontend

1. Instalar dependencias:
```bash
cd frontend
npm install
```

2. Ejecutar en modo desarrollo:
```bash
npm run dev
```

### Ejecutar todo simultáneamente (recomendado)

Desde el directorio `frontend`:
```bash
npm run dev
```

Esto ejecutará automáticamente tanto el frontend como el backend.

## Uso

1. Accede a `http://localhost:3000`
2. El agente de triaje te saludará y mostrará dos botones:
   - **Promoselect**: Para productos promocionales individuales
   - **SuitUp**: Para kits de productos promocionales
3. Selecciona tu opción y el agente especializado te ayudará a encontrar productos
4. Describe qué tipo de productos buscas
5. El agente buscará en la base de datos y te presentará 3 opciones relevantes

## Adaptaciones Realizadas

### Desde el Demo Original

- ✅ Reemplazado selector de asientos por selector de unidades de negocio
- ✅ Adaptado contexto de aerolínea a productos promocionales
- ✅ Implementado búsqueda híbrida (precisa + semántica)
- ✅ Optimizado performance con búsqueda en memoria pandas
- ✅ Adaptado agentes para Promoselect y SuitUp
- ✅ Modificado UI con componentes españoles
- ✅ Configurado proxy API en Next.js

### Arquitectura

El sistema utiliza:
- **Agents SDK de OpenAI** para orquestación de agentes
- **Pandas** para búsqueda optimizada en memoria
- **FastAPI** para API backend
- **Next.js 14** para frontend
- **Tailwind CSS** para estilos

## Testing Local

1. Asegúrate de tener tu `OPENAI_API_KEY` configurada
2. Ejecuta el backend: `cd backend && python main.py`
3. Ejecuta el frontend: `cd frontend && npm run dev`
4. Visita `http://localhost:3000`
5. Prueba seleccionando diferentes unidades de negocio
6. Haz búsquedas como "productos para oficina" o "kits para café"

## Próximos Pasos

- [ ] Persistir file_ids en base de datos
- [ ] Agregar guardrails para prevenir conversaciones fuera de tema
- [ ] Integrar directamente con API de Airtable
- [ ] Añadir autenticación y sesiones de usuario
- [ ] Implementar analytics y métricas

## Estructura de Datos

### promo.csv
- `sku`: Código del producto
- `precio`: Precio en MXN
- `categorias`: Categorías del producto
- `nombre`: Nombre del producto
- `descripcion`: Descripción detallada
- `medidas`: Dimensiones físicas
- `imagenes_url`: URL de la imagen

### suitup.csv
- `precio`: Precio del kit en MXN
- `nombre`: Nombre del kit
- `descripcion`: Descripción del kit
- `productos`: Lista de productos incluidos
- `imagen`: URL de la imagen del kit 