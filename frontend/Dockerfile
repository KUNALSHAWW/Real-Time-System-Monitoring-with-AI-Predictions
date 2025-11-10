# Dockerfile for Streamlit Frontend

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend code
COPY frontend/ .

# Expose port
EXPOSE 8501

# Streamlit config
RUN mkdir -p ~/.streamlit && \
    echo "[server]" > ~/.streamlit/config.toml && \
    echo "headless = true" >> ~/.streamlit/config.toml && \
    echo "port = 8501" >> ~/.streamlit/config.toml && \
    echo "enableCORS = false" >> ~/.streamlit/config.toml

# Run Streamlit
CMD ["streamlit", "run", "app.py"]
