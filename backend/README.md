# Real-Time System Monitoring - Backend API

This is the FastAPI backend for Real-Time System Monitoring with AI Predictions.

## Deployment on Hugging Face Spaces

This backend is configured to run on Hugging Face Spaces using Docker.

### Features
- Real-time system metrics monitoring
- AI-powered anomaly detection
- Predictive analytics
- WebSocket support for live updates
- RESTful API endpoints

### API Endpoints
- `GET /health` - Health check
- `GET /` - API information
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

### Environment Variables
No additional environment variables required for basic deployment.

For production use, you may want to configure:
- `GROQ_API_KEY` - For AI analysis features
- Database connection strings (if using external database)

### Local Development
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Docker Build
```bash
docker build -t monitoring-backend .
docker run -p 7860:7860 monitoring-backend
```
