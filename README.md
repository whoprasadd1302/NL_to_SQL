# MitraAI

MitraAI is an intelligent, multilingual conversational AI assistant built with FastAPI, Next.js, and Ollama.

## Architecture

- **Backend**: FastAPI with Ollama LLM integration (default: `qwen3:8b`)
- **Frontend**: Next.js 15 (React 19, TypeScript, Tailwind CSS)

---

## Project Structure

```text
MitraAI/
├── backend/
│   ├── app/
│   │   ├── config.py       # Configuration and environment settings
│   │   ├── llm.py          # Ollama LLM client integration
│   │   └── main.py         # FastAPI application and endpoints
│   ├── requirements.txt    # Python dependencies
│   └── .env                # Backend environment configuration
├── frontend/
│   ├── src/
│   │   └── app/            # Next.js App Router pages and components
│   ├── package.json        # Frontend dependencies and scripts
│   └── ...
└── README.md
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- [Ollama](https://ollama.com/) running locally with your desired model:
  ```bash
  ollama run qwen3:8b
  ```

---

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend will start at `http://localhost:8000`.

---

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## API Endpoints

- `GET /`: Service information and status
- `GET /health`: Health check
- `POST /chat`: Send a prompt and receive a conversational response
  - Request: `{"message": "Hello"}`
  - Response: `{"response": "..."}`
