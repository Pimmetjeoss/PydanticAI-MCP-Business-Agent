# 🚀 Quick Start Guide

## Snelle Installatie (Dutch/Nederlands)

1. **Installeer dependencies**:
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

2. **Start beide servers**:
   ```bash
   python start_servers.py
   ```

3. **Open je browser**:
   - Chat Interface: http://localhost:8501
   - API Documentatie: http://localhost:8000/docs

## Quick Installation (English)

1. **Install dependencies**:
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

2. **Start both servers**:
   ```bash
   python start_servers.py
   ```

3. **Open your browser**:
   - Chat Interface: http://localhost:8501
   - API Documentation: http://localhost:8000/docs

## What You Get

✅ **Modern Chat Interface** - Clean Streamlit UI with real-time messaging
✅ **Streaming Responses** - Real-time streaming using Server-Sent Events  
✅ **Model Selection** - Choose between GPT-4, Claude, and other models
✅ **Custom System Prompts** - Customize agent behavior
✅ **Chat History** - Persistent conversation history
✅ **Health Monitoring** - Real-time backend status
✅ **Tool Inspection** - View available agent capabilities
✅ **Error Handling** - Comprehensive error management
✅ **Docker Support** - Ready for containerized deployment

## Troubleshooting

**Backend shows red?** 
- Check if your main agent is properly configured
- Verify MCP server connections and API keys

**Streaming not working?**
- Toggle off "Streaming Mode" in sidebar
- Use the `/ask` endpoint as fallback

For detailed setup instructions, see `README.md`.