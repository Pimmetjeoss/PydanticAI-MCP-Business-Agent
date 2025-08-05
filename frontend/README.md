# PydanticAI Business Agent - Streamlit Frontend

A modern, user-friendly chat interface for interacting with your PydanticAI Business Agent. This frontend provides a web-based chat interface with streaming responses, model selection, and system prompt customization.

## 🌟 Features

- **Modern Chat Interface**: Clean, intuitive chat UI using Streamlit's latest chat components
- **Real-time Streaming**: Stream responses in real-time using Server-Sent Events (SSE)
- **Model Selection**: Choose between different AI models (GPT-4, Claude, etc.)
- **Custom System Prompts**: Customize the agent's behavior with custom system prompts
- **Chat History**: Persistent chat history within sessions
- **Health Monitoring**: Real-time backend status monitoring
- **Tool Inspection**: View available agent tools and capabilities
- **Responsive Design**: Works on desktop and mobile devices

## 🏗️ Architecture

```
frontend/
├── streamlit_app.py      # Main Streamlit application
├── fastapi_server.py     # FastAPI backend server
├── requirements.txt      # Frontend dependencies
├── start_servers.py      # Startup script for both servers
├── .env.example         # Environment configuration template
└── README.md           # This documentation
```

### Components

1. **Streamlit App** (`streamlit_app.py`): The main user interface
2. **FastAPI Server** (`fastapi_server.py`): REST API backend that interfaces with your PydanticAI agent
3. **Startup Script** (`start_servers.py`): Convenience script to run both components

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Your PydanticAI Business Agent configured and working
- Required environment variables set (see main project documentation)

### Installation

1. **Install dependencies**:
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

2. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

3. **Start the application**:
   
   **Option A: Use the startup script (recommended)**
   ```bash
   python start_servers.py
   ```
   
   **Option B: Start servers manually**
   ```bash
   # Terminal 1: Start FastAPI backend
   python fastapi_server.py
   
   # Terminal 2: Start Streamlit frontend
   streamlit run streamlit_app.py
   ```

4. **Open your browser**:
   - Streamlit UI: http://localhost:8501
   - FastAPI docs: http://localhost:8000/docs

## 📖 Usage Guide

### Basic Chat

1. Open the Streamlit interface in your browser
2. Check that the backend status shows 🟢 (green) in the sidebar
3. Type your message in the chat input at the bottom
4. Press Enter or click Send to get a response

### Configuration Options

#### Model Selection
- Use the sidebar to select different AI models
- Models are automatically loaded from your backend configuration

#### System Prompt Customization
- Edit the system prompt in the sidebar to customize agent behavior
- Click "Reset to Default" to restore the original prompt

#### Streaming vs Non-Streaming
- Toggle "Streaming Mode" to enable/disable real-time response streaming
- Streaming provides a more interactive experience
- Non-streaming may be more reliable for complex queries

### Advanced Features

#### Agent Tools Inspection
- Click "Show Tools" in the sidebar to see available agent capabilities
- View tool descriptions and understand what your agent can do

#### Chat History Management
- Chat history persists within your browser session
- Click "🗑️ Clear Chat History" to start fresh

#### Health Monitoring
- The sidebar shows real-time backend connection status
- Green (🟢): Healthy and ready
- Yellow (🟡): Connected but agent not loaded properly
- Red (🔴): Backend offline or unreachable

## 🔧 API Endpoints

The FastAPI backend provides these endpoints:

- `GET /health` - Health check and agent status
- `POST /ask` - Non-streaming chat endpoint
- `POST /chat` - Streaming chat endpoint (SSE)
- `GET /models` - Available AI models
- `GET /agent-info` - Agent capabilities and tools

## 🛠️ Development

### Running in Development Mode

1. **Backend with auto-reload**:
   ```bash
   uvicorn fastapi_server:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Frontend with auto-reload**:
   ```bash
   streamlit run streamlit_app.py --server.runOnSave true
   ```

### Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
# Backend configuration
FASTAPI_URL=http://localhost:8000

# Default settings
DEFAULT_MODEL=gpt-4
STREAM_MODE=true
LOG_LEVEL=INFO
```

### Customization

#### Adding New Models
Edit the `get_available_models()` function in `fastapi_server.py` to add new models.

#### Custom System Prompts
Modify the `DEFAULT_SYSTEM_PROMPT` in `streamlit_app.py` to change the default behavior.

#### UI Customization
The Streamlit app uses standard Streamlit components that can be easily customized with CSS.

## 🐛 Troubleshooting

### Common Issues

**1. Backend Status Shows Red (🔴)**
- Check if the FastAPI server is running on port 8000
- Verify the `FASTAPI_URL` in your configuration
- Check the main agent's environment variables and dependencies

**2. "Agent not loaded" Warning**
- Ensure your main PydanticAI agent configuration is correct
- Check MCP server connections and API keys
- Review the FastAPI server logs for initialization errors

**3. Streaming Not Working**
- Disable streaming mode in the sidebar as a fallback
- Check browser compatibility (modern browsers required for SSE)
- Verify CORS settings in the FastAPI server

**4. Connection Timeout**
- Increase timeout settings in `streamlit_app.py`
- Check network connectivity between components
- Review firewall settings if running on different machines

### Debug Mode

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file.

### Port Conflicts

If ports 8000 or 8501 are in use:
- Change the FastAPI port in `fastapi_server.py`
- Update `FASTAPI_URL` in your configuration
- Use `--server.port` flag for Streamlit

## 🔐 Security Considerations

- The current CORS configuration allows all origins (`*`) for development
- In production, specify exact allowed origins in `fastapi_server.py`
- Ensure your PydanticAI agent has proper input validation
- Consider adding rate limiting for production deployments

## 📚 Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PydanticAI Documentation](https://ai.pydantic.dev/)
- Main PydanticAI Business Agent documentation (see parent directory)

## 🤝 Contributing

This frontend is part of the larger PydanticAI Business Agent project. Please refer to the main project's contributing guidelines.

## 📄 License

Same license as the main PydanticAI Business Agent project.