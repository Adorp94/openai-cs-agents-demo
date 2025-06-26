# 🚀 Quick Start

## Run the app

You can either run the backend independently if you want to use a separate UI, or run both the UI and backend at the same time.

### Run the backend independently

From the `backend` folder, run:

```bash
python -m uvicorn api:app --reload --port 8000
```

The backend will be available at: http://localhost:8000

### Run the UI & backend simultaneously

From the `frontend` folder, run:

```bash
npm run dev
```

This will start both the Next.js frontend (port 3000) and the Python backend (port 8000).

## Initial Setup

### 1. Environment Setup

```bash
# Create .env file in backend directory
cd backend
cp env.example .env

# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=sk-proj-your-key-here
```

### 2. Install Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies  
cd ../frontend
npm install
```

### 3. Run!

```bash
# From the frontend directory - this runs everything
npm run dev
```

Visit: http://localhost:3000

## That's it! 🎉

The system will:
1. Automatically upload your CSV files to OpenAI on first run
2. Show a business unit selector (Promoselect vs SuitUp)
3. Route you to the appropriate specialist agent
4. Search your product catalogs and present results

## Test Queries

- **Promoselect**: "Busco productos para oficina"
- **SuitUp**: "Busco kits para café" 