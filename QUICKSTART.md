# Quick Start Guide

## Prerequisites
- Node.js 18+ and npm
- Python 3.8+ and pip
- OpenAI API key

## Setup

### 1. Environment Configuration
Create `backend/.env`:
```bash
OPENAI_API_KEY=your_openai_api_key_here
PROMO_VECTOR_STORE_ID=vs_6863e9b0ae9c81918645507c8809af6e
SUITUP_VECTOR_STORE_ID=vs_6863e9c28cdc81919e3095ed53065330
```

### 2. Install Dependencies
```bash
# Frontend dependencies
cd frontend && npm install && cd ..

# Backend dependencies (will use existing venv)
cd backend && source venv/bin/activate && pip install -r requirements.txt && cd ..
```

## Manual Startup (Recommended)

### Terminal 1 - Backend
```bash
cd backend
source venv/bin/activate
python -m uvicorn api:app --reload --port 8000
```

### Terminal 2 - Frontend  
```bash
cd frontend
npm run dev
```

Visit: [http://localhost:3000](http://localhost:3000)

## Automatic Startup

If you prefer to run both servers with one command:
```bash
npm run dev
```

## Testing

1. Open [http://localhost:3000](http://localhost:3000)
2. Click "Promoselect" or "SuitUp" 
3. Ask: "Necesito regalos corporativos elegantes"
4. Specify budget: "Tengo 400 pesos"
5. Get product recommendations!

## Troubleshooting

- **Backend not connecting**: Make sure the virtual environment is activated
- **Frontend errors**: Clear cache with `cd frontend && rm -rf .next`
- **Port conflicts**: Backend uses 8000, frontend uses 3000 