# 🛒 AuraCart — Intelligent AI Shopping Advisor
## (Assignment 2: GEN-AI)

AuraCart is a sophisticated, production-ready AI shopping assistant built for **Assignment 2** (Advanced Agentic Systems). It leverages a **10-agent LangGraph workflow** to transform natural language queries into comprehensive, personalized product recommendations.

---

## 🛠️ Key Professional Features
- **Intelligent Multi-Agent System**: Powered by LangGraph, involving specialized agents for preference extraction, live retrieval, sentiment analysis, scoring, and ethics checking.
- **Live Market Integration**: Fetches real-time data from **DummyJSON** and context from **DuckDuckGo**.
- **Transparent Reasoning**: Every recommendation includes a detailed scientific justification from the AI agents.
- **Price Intelligence**: Category-based market analysis to advise users on whether to "Buy Now" or "Wait".
- **Ethics & Safety Protocol**: Built-in guardrails to detect brand monopolies, quality risks, and budget violations.
- **Commercial-Grade UI**: A premium React/Vite frontend with professional glassmorphism, animated background silhouettes, and a responsive dashboard.

---

## 🏗️ System Architecture
The system follows a deterministic yet flexible state machine orchestrated by LangGraph:

1. **Preference Extraction**: Parses budget, category, and intent.
2. **Dynamic Retrieval**: Fetches SKUs from global APIs.
3. **Multi-Step Analysis**: Sentiment parsing, 100-point scoring, and bias detection.
4. **Final Consensus**: Agent 10 synthesizes all findings into a final report.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API Key (Optional for LLM enhancement)

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
# Copy .env.example to .env and add your GROQ_API_KEY
python main.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173` to start shopping.

---

## 📁 Project Structure
- `backend/`: FastAPI server and LangGraph agent logic.
- `frontend/`: React components and professional styling.
- `database/`: Persistence layer for feedback.
- `report.md`: Detailed 5-10 page academic project report.
- `architecture_diagram.png`: Visual representation of the agent workflow.

---

## 🧪 Evaluation
The system has been validated against **50+ test queries** focusing on:
- **Category Match Accuracy**
- **Budget Compliance**
- **Retrieval Latency**
- **Ethics Flagging reliability**

Run the evaluation script:
```bash
cd backend && python evaluate_50_queries.py
```

---
**Developed for Assignment 2 — Advanced Agentic Coding**
