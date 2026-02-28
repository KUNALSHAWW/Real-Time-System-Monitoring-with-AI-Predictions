# Real-Time System Monitoring - Backend API

FastAPI backend for Real-Time System Monitoring with AI Predictions.
Optimized for **Hugging Face Spaces** Docker deployment.

## 🚀 Features

- **Real System Metrics**: Uses `psutil` for actual CPU, Memory, Disk, Network stats
- **Host Information**: Shows container hostname, OS, CPU cores
- **AI Analysis**: GROQ-powered intelligent insights (Llama 3.1)
- **Auto-Incidents**: Automatically creates incidents when thresholds exceeded
- **Predictions**: Moving Average forecasting with anomaly risk
- **Email Reports**: Send HTML reports via SMTP

## 📦 Deployment on Hugging Face Spaces (Docker)

### Step 1: Create a New Space

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Choose:
   - **SDK**: `Docker`
   - **Space name**: `system-monitor-backend` (or your choice)
   - **Visibility**: Public or Private

### Step 2: Upload Files

Upload these files to your Space:
```
├── Dockerfile
├── main.py
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── logger.py
│   └── ...
├── routers/
│   ├── __init__.py
│   ├── system_metrics.py
│   ├── ai_analysis.py
│   ├── incidents.py
│   ├── predictions.py
│   ├── reports.py
│   └── ...
└── middleware/
    └── ...
```

### Step 3: Set Secrets

Go to **Settings** → **Repository secrets** and add:

| Secret | Required | Description |
|--------|----------|-------------|
| `GROQ_API_KEY` | **Yes** | Get from [Groq Console](https://console.groq.com) |
| `EMAIL_USER` | Optional | Gmail address for reports |
| `EMAIL_PASS` | Optional | Gmail App Password |

### Step 4: Wait for Build

The Space will automatically build and deploy. Once ready:
- Your backend URL will be: `https://USERNAME-SPACE-NAME.hf.space`
- API docs: `https://USERNAME-SPACE-NAME.hf.space/docs`

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/metrics/current` | GET | Current system metrics |
| `/api/metrics/history` | GET | Metrics history |
| `/api/ai/analyze` | POST | AI-powered analysis |
| `/api/predictions/forecast/{metric}` | GET | Metric forecasts |
| `/api/incidents/list` | GET | List all incidents |
| `/api/incidents/create` | POST | Create incident |
| `/api/reports/send-report` | POST | Send email report |

## 🖥️ Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY=your_key_here

# Run server
uvicorn main:app --reload --port 8000
```

## 📊 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | - | Groq API key for AI features |
| `GROQ_MODEL` | `llama-3.1-70b-versatile` | Groq model to use |
| `EMAIL_USER` | - | SMTP email username |
| `EMAIL_PASS` | - | SMTP email password |
| `SMTP_SERVER` | `smtp.gmail.com` | SMTP server |
| `SMTP_PORT` | `587` | SMTP port |

## 🔒 Getting GROQ API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up / Sign in
3. Navigate to **API Keys**
4. Create a new key
5. Copy and save it securely

## 📧 Setting Up Gmail for Reports

1. Enable 2-Factor Authentication on your Google account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Create a new App Password for "Mail"
4. Use this password (not your regular password) as `EMAIL_PASS`

## 📝 License

MIT License
