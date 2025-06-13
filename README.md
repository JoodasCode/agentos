# Agent OS V2 - Multi-Agent Conversational Platform

A full-stack conversational AI platform with specialized agents and automation capabilities.

## 🤖 Features

- **4 Specialized Agents**: Alex (Strategy), Dana (Creative), Riley (Data), Jamie (Operations)
- **Conversational Interface**: Natural dialogue with proactive questioning
- **Trigger.dev Integration**: Automated workflow execution (coming soon)
- **Product Hunt Automation**: Complete launch workflows
- **Real-time Chat**: Beautiful, responsive chat interface
- **Modern Stack**: Next.js + FastAPI + Shadcn UI

## 🏗️ Architecture

```
agent_os_v2/
├── frontend/          # Next.js + TypeScript + Shadcn UI
├── backend/           # FastAPI + Python
└── README.md
```

## 🚀 Quick Start

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

## 📡 API Endpoints

### Core
- `GET /` - Service information
- `GET /health` - Health check

### Chat
- `POST /chat/start` - Start new conversation
- `POST /chat/continue/{id}` - Continue conversation

### Automation
- `GET /automation/capabilities` - Available automations
- `POST /automation/execute` - Execute workflows

## 🎨 UI Components

Built with **Shadcn UI** for beautiful, accessible components:
- Conversational chat interface
- Agent avatars with personality-based colors
- Real-time conversation state tracking
- Automation readiness indicators

## 🔧 Tech Stack

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Shadcn UI
- Lucide React Icons

**Backend:**
- FastAPI
- Python 3.9+
- Uvicorn
- Pydantic

**Coming Soon:**
- AgentScope integration
- Trigger.dev automation
- Supabase database
- Real-time WebSocket support

## 🚀 Deployment

Ready for deployment on:
- **Frontend**: Vercel, Netlify
- **Backend**: Railway, Render, Fly.io

## 🤝 Contributing

This is the foundation for a powerful multi-agent platform. Future enhancements include:
- Real AgentScope integration
- Trigger.dev job execution
- Database persistence
- WebSocket real-time updates
- Advanced agent personalities 