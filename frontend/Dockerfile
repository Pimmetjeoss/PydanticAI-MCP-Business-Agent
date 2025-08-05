# Multi-stage Dockerfile for PydanticAI Business Agent Frontend

FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy parent directory dependencies (the main agent)
COPY ../mcp_business_agent /app/mcp_business_agent

# Expose ports
EXPOSE 8000 8501

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Starting PydanticAI Business Agent Frontend..."\n\
\n\
# Start FastAPI server in background\n\
echo "Starting FastAPI backend..."\n\
python fastapi_server.py &\n\
FASTAPI_PID=$!\n\
\n\
# Wait for FastAPI to start\n\
sleep 5\n\
\n\
# Start Streamlit frontend\n\
echo "Starting Streamlit frontend..."\n\
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501\n\
\n\
# Cleanup on exit\n\
trap "kill $FASTAPI_PID" EXIT\n\
wait\n\
' > /app/start.sh && chmod +x /app/start.sh

# Default command
CMD ["/app/start.sh"]