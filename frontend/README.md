# Real-Time System Monitoring - Frontend Dashboard

This is the Streamlit frontend for Real-Time System Monitoring with AI Predictions.

## Deployment on Hugging Face Spaces

This frontend is configured to run on Hugging Face Spaces using Docker.

### Features
- Real-time system metrics visualization
- Interactive dashboards
- Anomaly detection alerts
- Predictive analytics charts
- Incident management

### Configuration

#### Environment Variables (Secrets in HF Spaces)
You need to set the following secret in your Hugging Face Space settings:

- `BACKEND_URL` - URL of your deployed backend (e.g., `https://your-username-backend.hf.space`)

To add this secret:
1. Go to your Space settings
2. Navigate to "Repository secrets"
3. Click "New secret"
4. Name: `BACKEND_URL`
5. Value: Your backend Space URL (without trailing slash)

### Local Development
```bash
pip install -r requirements.txt
streamlit run app_final.py
```

### Docker Build
```bash
docker build -t monitoring-frontend .
docker run -p 7860:7860 monitoring-frontend
```

### Notes
- The frontend will automatically connect to the backend URL specified in the `BACKEND_URL` environment variable
- If the backend is not available, the dashboard will show simulated data for demonstration purposes
