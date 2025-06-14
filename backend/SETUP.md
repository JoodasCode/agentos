# Backend Setup Guide

## Environment Configuration

Create a `.env` file in the backend directory with the following variables:

```bash
# Environment Configuration
ENVIRONMENT=development
DEBUG=true

# API Settings
PROJECT_NAME="Agent OS V2"
LOG_LEVEL=INFO

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_MODEL=gpt-4o-mini

# Supabase Configuration (Already configured for this project)
SUPABASE_URL=https://rxchyyxsipdopwpwnxku.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ4Y2h5eXhzaXBkb3B3cHdueGt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxNDA3OTcsImV4cCI6MjA2NDcxNjc5N30.F3B_omEBQwwOwQCKMzk3ImXVPNh_SypgNFAVpC8eiRA

# Encryption (Generate a secure key for production)
MASTER_ENCRYPTION_KEY=your_base64_encoded_32_byte_key_here

# Trigger.dev Configuration
TRIGGER_DEV_API_URL=https://api.trigger.dev
TRIGGER_DEV_API_KEY=your_trigger_dev_api_key_here
TRIGGER_DEV_PROJECT_ID=proj_oszoiqgyzofujbljgxau

# Security (Generate a secure secret key for production)
SECRET_KEY=your_secret_key_here

# CORS Settings (Adjust for production)
ALLOWED_ORIGINS=["http://localhost:3000", "https://your-frontend-domain.com"]
```

## API Key Management System

The backend now includes a complete API key management system with:

### Features
- **Secure Storage**: AES-256-GCM encryption with PBKDF2 key derivation
- **Database Persistence**: Supabase integration with sophisticated schema
- **In-Memory Caching**: 5-minute TTL for performance
- **Usage Tracking**: Comprehensive logging and analytics
- **Connection Testing**: Validate API keys with external services

### Database Schema
The system uses the following Supabase tables:
- `encrypted_api_keys`: Secure storage of encrypted API keys
- `service_integrations`: Service configuration and metadata
- `api_key_usage_logs`: Usage tracking and analytics

### API Endpoints
- `POST /api/v1/api-keys/submit` - Store new API key
- `GET /api/v1/api-keys/session/{session_id}/status` - Get session status
- `POST /api/v1/api-keys/test-connection/{service}` - Test service connection
- `GET /api/v1/api-keys/integrations` - Get service configurations
- `POST /api/v1/api-keys/session/{session_id}/sync` - Sync with database
- `DELETE /api/v1/api-keys/session/{session_id}/service/{service}` - Revoke key

### Supported Services
- OpenAI (GPT models, DALL-E)
- Notion (Database operations, page creation)
- Slack (Messaging, channel management)
- GitHub (Repository management, issues)
- Resend (Email campaigns)
- Fal.ai (AI image generation)

## Security Notes

1. **Encryption Keys**: Generate secure encryption keys for production
2. **Environment Variables**: Never commit `.env` files to version control
3. **API Keys**: Store user API keys securely with proper encryption
4. **Database Access**: Use Supabase RLS policies for additional security

## Development

1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables in `.env`
3. Run the server: `uvicorn app.main:app --reload`
4. Access API docs: `http://localhost:8000/docs`

## Production Deployment

The backend is deployed on Railway at:
https://agentos-production-6348.up.railway.app

Make sure to set all environment variables in the Railway dashboard. 