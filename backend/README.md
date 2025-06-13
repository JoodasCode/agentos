# Agent OS V2 - Backend

Multi-agent conversational AI platform with automation capabilities.

## Features

- 🤖 **4 Specialized Agents**: Alex (Strategy), Dana (Creative), Riley (Data), Jamie (Operations)
- 💬 **Conversational Interface**: Natural dialogue with proactive questioning
- ⚡ **Trigger.dev Integration**: Automated workflow execution
- 🚀 **Product Hunt Automation**: Complete launch workflows
- 📊 **Analytics Tracking**: Performance monitoring and insights

## API Endpoints

### Core Endpoints
- `GET /` - Service information
- `GET /health` - Health check

### Chat Endpoints
- `POST /chat/start` - Start new conversation
- `POST /chat/continue/{conversation_id}` - Continue conversation

### Automation Endpoints
- `GET /automation/capabilities` - Available automations
- `POST /automation/execute` - Execute automation workflow

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload
```

## Deployment

This backend is designed for Railway deployment with automatic scaling and environment management.

## Architecture

- **FastAPI**: High-performance async web framework
- **AgentScope**: Multi-agent orchestration (coming soon)
- **Trigger.dev**: Job queue and automation (coming soon)
- **Supabase**: Database and real-time features (coming soon) 