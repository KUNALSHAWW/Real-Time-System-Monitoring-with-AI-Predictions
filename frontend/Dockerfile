# Dockerfile for Streamlit Frontend - Production Deployment

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend code
COPY . .

# Use PORT environment variable (Render provides this)
ENV PORT=10000

# Expose the port
EXPOSE ${PORT}

# Streamlit config for production
RUN mkdir -p ~/.streamlit && \
    echo "[server]" > ~/.streamlit/config.toml && \
    echo "headless = true" >> ~/.streamlit/config.toml && \
    echo "port = \${PORT}" >> ~/.streamlit/config.toml && \
    echo "address = \"0.0.0.0\"" >> ~/.streamlit/config.toml && \
    echo "enableCORS = false" >> ~/.streamlit/config.toml && \
    echo "enableXsrfProtection = false" >> ~/.streamlit/config.toml && \
    echo "enableWebsocketCompression = true" >> ~/.streamlit/config.toml && \
    echo "[browser]" >> ~/.streamlit/config.toml && \
    echo "gatherUsageStats = false" >> ~/.streamlit/config.toml

# Run Streamlit using PORT environment variable
# Render will automatically set this to 10000
CMD streamlit run app_final.py --server.port=${PORT} --server.address=0.0.0.0
