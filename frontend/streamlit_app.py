"""
Streamlit Frontend for PydanticAI Business Agent

A modern chat interface that connects to the FastAPI backend to interact
with the PydanticAI business agent with support for streaming responses.
"""

import streamlit as st
import requests
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, AsyncGenerator
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
DEFAULT_SYSTEM_PROMPT = """You are a sophisticated business automation agent with access to multiple tools for:

- Database analysis and queries
- Email communication via Microsoft Graph
- Web research and content scraping  
- Strategic thinking and decision-making
- Workflow automation

Always be helpful, professional, and thorough in your responses. Use your tools when appropriate to provide accurate, up-to-date information."""

# Initialize session state
def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "fastapi_url" not in st.session_state:
        st.session_state.fastapi_url = FASTAPI_URL
    
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gpt-4"
    
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT
    
    if "stream_mode" not in st.session_state:
        st.session_state.stream_mode = True
    
    if "backend_status" not in st.session_state:
        st.session_state.backend_status = "unknown"

def check_backend_health() -> Dict:
    """Check if the FastAPI backend is healthy."""
    try:
        response = requests.get(f"{st.session_state.fastapi_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            st.session_state.backend_status = "healthy" if data.get("agent_loaded") else "unhealthy"
            return data
        else:
            st.session_state.backend_status = "unhealthy"
            return {"status": "error", "agent_loaded": False}
    except Exception as e:
        st.session_state.backend_status = "offline"
        return {"status": "offline", "error": str(e), "agent_loaded": False}

def get_available_models() -> List[Dict]:
    """Get available models from the backend."""
    try:
        response = requests.get(f"{st.session_state.fastapi_url}/models", timeout=5)
        if response.status_code == 200:
            return response.json().get("models", [])
        return []
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        return []

def get_agent_info() -> Dict:
    """Get information about the loaded agent."""
    try:
        response = requests.get(f"{st.session_state.fastapi_url}/agent-info", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"agent_loaded": False, "tools": [], "tools_count": 0}
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        return {"agent_loaded": False, "tools": [], "tools_count": 0, "error": str(e)}

async def stream_chat_response(message: str, system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
    """Stream chat response from the FastAPI backend."""
    payload = {
        "message": message,
        "system_prompt": system_prompt if system_prompt != DEFAULT_SYSTEM_PROMPT else None
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{st.session_state.fastapi_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    yield f"Error: {response.status} - {error_text}"
                    return
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])  # Remove 'data: ' prefix
                            if data.get("type") == "stream":
                                yield data.get("content", "")
                            elif data.get("type") == "error":
                                yield f"Error: {data.get('content', 'Unknown error')}"
                                return
                            elif data.get("type") == "done":
                                return
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        yield f"Connection error: {str(e)}"

def send_non_streaming_message(message: str, system_prompt: Optional[str] = None) -> str:
    """Send a non-streaming message to the agent."""
    payload = {
        "message": message,
        "system_prompt": system_prompt if system_prompt != DEFAULT_SYSTEM_PROMPT else None
    }
    
    try:
        response = requests.post(
            f"{st.session_state.fastapi_url}/ask",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json().get("response", "No response received")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Connection error: {str(e)}"

def render_sidebar():
    """Render the configuration sidebar."""
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        # Backend status
        health_data = check_backend_health()
        status_color = {
            "healthy": "🟢",
            "unhealthy": "🟡", 
            "offline": "🔴",
            "unknown": "⚪"
        }.get(st.session_state.backend_status, "⚪")
        
        st.markdown(f"**Backend Status:** {status_color} {st.session_state.backend_status.title()}")
        
        if health_data.get("agent_loaded"):
            st.success("Agent loaded successfully")
        elif st.session_state.backend_status == "healthy":
            st.warning("Backend healthy but agent not loaded")
        elif st.session_state.backend_status == "offline":
            st.error("Backend offline - check if FastAPI server is running")
        
        st.divider()
        
        # FastAPI URL configuration
        st.session_state.fastapi_url = st.text_input(
            "FastAPI Backend URL",
            value=st.session_state.fastapi_url,
            help="URL of the FastAPI backend server"
        )
        
        # Model selection
        models = get_available_models()
        if models:
            model_options = [f"{m['name']} ({m['provider']})" for m in models]
            model_ids = [m['id'] for m in models]
            
            try:
                current_index = model_ids.index(st.session_state.selected_model)
            except ValueError:
                current_index = 0
            
            selected_index = st.selectbox(
                "Select Model",
                range(len(model_options)),
                index=current_index,
                format_func=lambda x: model_options[x],
                help="Choose the AI model to use"
            )
            st.session_state.selected_model = model_ids[selected_index]
        else:
            st.warning("No models available from backend")
        
        # Streaming mode toggle
        st.session_state.stream_mode = st.toggle(
            "Streaming Mode",
            value=st.session_state.stream_mode,
            help="Enable real-time streaming responses"
        )
        
        st.divider()
        
        # System prompt configuration
        st.subheader("System Prompt")
        st.session_state.system_prompt = st.text_area(
            "Customize the system prompt",
            value=st.session_state.system_prompt,
            height=200,
            help="Define how the agent should behave"
        )
        
        if st.button("Reset to Default"):
            st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT
            st.rerun()
        
        st.divider()
        
        # Agent information
        if st.session_state.backend_status == "healthy":
            agent_info = get_agent_info()
            if agent_info.get("agent_loaded"):
                st.subheader("Agent Info")
                st.write(f"**Tools Available:** {agent_info.get('tools_count', 0)}")
                
                if st.button("Show Tools"):
                    tools = agent_info.get("tools", [])
                    for tool in tools:
                        st.write(f"• **{tool['name']}**: {tool['description'][:100]}...")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", type="secondary"):
            st.session_state.messages = []
            st.rerun()

def render_chat_interface():
    """Render the main chat interface."""
    st.title("💬 PydanticAI Business Agent Chat")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "timestamp" in message:
                st.caption(f"🕒 {message['timestamp']}")

    # Chat input
    if prompt := st.chat_input("Ask your business agent anything..."):
        # Add user message to chat history
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "timestamp": timestamp
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
            st.caption(f"🕒 {timestamp}")
        
        # Generate assistant response
        with st.chat_message("assistant"):
            if st.session_state.stream_mode and st.session_state.backend_status == "healthy":
                # Streaming response
                response_placeholder = st.empty()
                full_response = ""
                
                try:
                    # Use asyncio to handle streaming
                    async def get_streamed_response():
                        nonlocal full_response
                        async for chunk in stream_chat_response(prompt, st.session_state.system_prompt):
                            full_response += chunk
                            response_placeholder.write(full_response + "▌")
                        response_placeholder.write(full_response)
                    
                    # Run the async function
                    asyncio.run(get_streamed_response())
                    
                except Exception as e:
                    full_response = f"Streaming error: {str(e)}"
                    response_placeholder.error(full_response)
            else:
                # Non-streaming response
                with st.spinner("Thinking..."):
                    full_response = send_non_streaming_message(prompt, st.session_state.system_prompt)
                st.write(full_response)
            
            # Add assistant response to chat history
            response_timestamp = datetime.now().strftime("%H:%M:%S")
            st.caption(f"🕒 {response_timestamp}")
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "timestamp": response_timestamp
            })

def main():
    """Main application function."""
    # Configure page
    st.set_page_config(
        page_title="PydanticAI Business Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Create layout
    render_sidebar()
    render_chat_interface()
    
    # Footer
    st.markdown("---")
    st.markdown("Built with [Streamlit](https://streamlit.io) and [PydanticAI](https://ai.pydantic.dev)")

if __name__ == "__main__":
    main()