# Guía de Testing Local

## Setup Rápido

### 1. Configuración del Backend

```bash
cd promopro-agents-adaptation/backend

# Crear archivo .env (copiando del ejemplo)
cp env.example .env

# Editar el archivo .env y agregar tu OpenAI API Key
# OPENAI_API_KEY=sk-proj-...tu_clave_aqui...

# Instalar dependencias (recomendado: usar un entorno virtual)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# Ejecutar el backend (método individual)
python -m uvicorn api:app --reload --port 8000
```

### 2. Método Simultáneo (Recomendado)

```bash
# Solo necesitas esto - ejecuta backend Y frontend automáticamente
cd promopro-agents-adaptation/frontend
npm install
npm run dev
```

### 3. Método Separado (Opcional)

```bash
# Terminal 1: Backend
cd promopro-agents-adaptation/backend
python -m uvicorn api:app --reload --port 8000

# Terminal 2: Frontend  
cd promopro-agents-adaptation/frontend
npm run dev
```

## Testing Flow

1. **Acceder a la aplicación**: http://localhost:3000

2. **Flujo de Triaje**:
   - El agente debe saludar y mostrar los botones de Promoselect y SuitUp
   - Presionar cualquier botón debería cambiar al agente correspondiente

3. **Testing Promoselect**:
   - Selecciona "Promoselect"
   - Pregunta algo como: "Busco productos para oficina"
   - El agente debería usar la herramienta promo_search
   - Debería presentar 3 productos con formato: nombre, descripción, precio + imagen

4. **Testing SuitUp**:
   - Selecciona "SuitUp" 
   - Pregunta algo como: "Busco kits para café"
   - El agente debería usar la herramienta suitup_search
   - Debería presentar 3 kits con formato: nombre, descripción, productos, precio + imagen

## Troubleshooting

### Backend Issues

- **Error de OpenAI API Key**: Verifica que el archivo `.env` tiene la clave correcta
- **Error de archivos CSV**: Verifica que los archivos estén en `../data/`
- **Error de puerto**: Verifica que el puerto 8000 esté libre

### Frontend Issues

- **Error de conexión con backend**: Verifica que el backend esté corriendo en puerto 8000
- **Error de dependencias**: Ejecuta `npm install` nuevamente

### Testing Commands

```bash
# Verificar que el backend esté funcionando
curl http://localhost:8000/chat -X POST -H "Content-Type: application/json" -d '{"conversation_id":"","message":"Hola"}'

# Verificar que el frontend pueda comunicarse con el backend
# (debería mostrar respuesta del agente en el navegador)
```

## Datos de Prueba Sugeridos

### Para Promoselect:
- "Busco productos para oficina"
- "Necesito artículos de escritorio" 
- "Productos de menos de $50"
- "Bolígrafos personalizados"

### Para SuitUp:
- "Busco kits para café"
- "Kits ejecutivos"
- "Sets para regalos corporativos"
- "Kits de menos de $100"

## Logs Importantes

- Los logs del backend mostrarán cuando se suban los CSV a OpenAI
- Los logs mostrarán qué herramientas usan los agentes
- El frontend mostrará errores en la consola del navegador si hay problemas de conexión 