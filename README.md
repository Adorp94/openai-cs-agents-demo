# Promotional Products AI Chat System

A production-ready AI chat system for promotional products with intelligent agent orchestration, hybrid search, and cost-optimized performance.

## 🚀 Features

- 🤖 **AI Agent Orchestration** with OpenAI's Agents SDK
- 🔍 **Hybrid Search Strategy**: Precise search + semantic fallback
- 📊 **3,395 promotional products** + 65 specialized kits
- 💰 **Cost Optimized**: 96% cheaper than Code Interpreter
- 🌐 **Bilingual**: Spanish interface with intelligent routing
- ⚡ **Real-time Chat** with agent handoffs and context preservation

## 📁 Project Structure

```
/
├── backend/          # FastAPI backend with AI agents
├── frontend/         # Next.js 14 frontend application
├── data/            # CSV product databases
├── QUICKSTART.md    # Quick setup guide
└── README.md        # This file
```

## 🏃‍♂️ Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+ and pip
- OpenAI API key

### 1. Install Dependencies

```bash
# Install frontend dependencies
npm run install:frontend

# Install backend dependencies  
npm run install:backend
```

### 2. Configure Environment

Create `backend/.env`:
```bash
OPENAI_API_KEY=your_openai_api_key
PROMO_VECTOR_STORE_ID=your_promo_vector_store_id
SUITUP_VECTOR_STORE_ID=your_suitup_vector_store_id
```

### 3. Start the Application

**Option 1: One Command (Simplest)**
```bash
./start.sh
```

**Option 2: Using npm**
```bash
npm run dev
```

**Option 3: Manual (Two Terminals)**
```bash
# Terminal 1
npm run dev:backend

# Terminal 2  
npm run dev:frontend
```

The app will be available at [http://localhost:3000](http://localhost:3000)

## 🛠️ Development

### Individual Services

```bash
# Frontend only (port 3000)
npm run dev:frontend

# Backend only (port 8000)  
npm run dev:backend
```

### Building for Production

```bash
npm run build
```

## 🔧 Technical Stack

- **Backend**: FastAPI + OpenAI Agents SDK + Vector Search
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **AI**: GPT-4.1 with function calling and guardrails
- **Search**: Pandas (precise) + OpenAI Vector Stores (semantic)
- **Database**: CSV files (3,395 products + 65 kits)

## 🎯 How It Works

### Agent Architecture

1. **Triage Agent**: Routes customers to appropriate business units
2. **Promoselect Agent**: Specializes in individual promotional products  
3. **SuitUp Agent**: Specializes in promotional product kits

### Search Strategy

1. **Precise Search** (Primary): Fast pandas filtering by keywords and price
2. **Semantic Search** (Fallback): Vector search for vague queries like "elegant corporate gifts"

This hybrid approach provides instant results for specific queries while handling natural language requests intelligently.

## 📚 Documentation

- [Quick Start Guide](./QUICKSTART.md) - Detailed setup instructions
- [Original Implementation Details](./PROMOPRO_README.md) - Complete technical documentation

## 🤝 Usage Example

1. Visit [http://localhost:3000](http://localhost:3000)
2. Choose business unit: **Promoselect** (individual products) or **SuitUp** (kits)
3. Describe what you're looking for: "Necesito regalos corporativos elegantes para un evento"
4. Specify budget: "Tengo un presupuesto de 400 pesos"
5. Get 3 tailored product recommendations with images and details

## 💡 Cost Optimization

- **Precise Search**: ~$0.001 per query
- **Semantic Search**: ~$0.0025 per query  
- **vs Code Interpreter**: ~$0.03 per session (96% savings!)

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
