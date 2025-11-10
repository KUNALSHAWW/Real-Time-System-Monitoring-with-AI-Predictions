# Quick Start Guide - Real-Time System Monitoring

## 🎯 5-Minute Setup

### Step 1: Clone & Setup Environment (2 min)

```bash
# Navigate to project
cd "real time system monitoring with AI predictions"

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Or (macOS/Linux)
source venv/bin/activate
```

### Step 2: Prepare .env File (2 min)

```bash
# Copy example to actual .env
cp .env.example .env

# Edit .env and add your API keys:
# - GROQ_API_KEY (get from https://console.groq.com/keys)
# - HUGGINGFACE_API_TOKEN (get from https://huggingface.co/settings/tokens)
```

### Step 3: Install & Run (1 min)

**Option A: Docker (Recommended)**
```bash
# Ensure Docker is running, then:
docker-compose up -d

# Services available at:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:8501
# - Prometheus: http://localhost:9090
```

**Option B: Local Installation**

```bash
# Install backend
cd backend
pip install -r requirements.txt
python main.py
# Runs on http://localhost:8000

# In new terminal - install & run frontend
cd frontend
pip install -r requirements.txt
streamlit run app.py
# Opens at http://localhost:8501

# In another terminal - run ML notebook
cd ml_engine
jupyter notebook model_training.ipynb
```

---

## 📋 Pre-Requisites Checklist

### Required APIs (Provide Manually)

- [ ] **GROQ API Key**
  - Get from: https://console.groq.com/keys
  - Cost: Free tier available
  - Used for: Fast LLM inference

- [ ] **Hugging Face Token**
  - Get from: https://huggingface.co/settings/tokens
  - Cost: Free (community models)
  - Used for: Model downloads & inference

### Optional (Can Use Local Defaults)

- [ ] **OpenAI API Key** (for fallback)
  - Get from: https://platform.openai.com/api-keys
  - Cost: ~$0.002/1K tokens

- [ ] **Ollama** (local LLM - free)
  - Download from: https://ollama.ai
  - Installation: `ollama serve` then `ollama pull llama2`

### Databases (Auto-Setup with Docker)

- PostgreSQL 13+ (or use Docker)
- Redis 7+ (or use Docker)
- InfluxDB 2.0+ (or use Docker)

---

## 🔧 Manual Database Setup (If Not Using Docker)

### PostgreSQL
```bash
# Create database
createdb system_monitoring

# Update .env
DATABASE_URL=postgresql://user:password@localhost:5432/system_monitoring
```

### Redis
```bash
# Start Redis
redis-server

# Update .env
REDIS_HOST=localhost
REDIS_PORT=6379
```

### InfluxDB
```bash
# Start InfluxDB (if installed locally)
influxd

# Generate token and update .env
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_token
INFLUXDB_ORG=your_org
INFLUXDB_BUCKET=system_metrics
```

---

## 🚀 After Installation

### 1. Access Dashboard
```
http://localhost:8501
```
- Login with demo: username=`admin`, password=`admin123`
- View metrics, anomalies, and predictions

### 2. Check API Docs
```
http://localhost:8000/docs
```
- Interactive API documentation
- Try out endpoints directly

### 3. Run ML Training
```bash
cd ml_engine
jupyter notebook model_training.ipynb

# Run cells in order:
# 1. Environment Setup
# 2. API Authentication
# 3-6. Model Initialization
# 8. Train anomaly detection models
# 12. Run validation tests
```

### 4. Monitor Backend Logs
```bash
# If running locally
tail -f logs/app.log

# If running in Docker
docker logs monitoring-backend -f
```

---

## ⚡ Test the System

### Test Backend
```bash
curl http://localhost:8000/health

# Response:
# {"status":"healthy","timestamp":"2024-11-10T...","environment":"development"}
```

### Test API with Sample Data
```bash
# Get CPU metrics
curl http://localhost:8000/api/v1/metrics/cpu

# Post custom metric
curl -X POST http://localhost:8000/api/v1/metrics/custom \
  -H "Content-Type: application/json" \
  -d '{"metric_name":"test_cpu","value":75.5}'
```

### Test LLM Integration
```bash
# Check available models
curl http://localhost:8000/api/v1/analysis/models

# Submit analysis
curl -X POST http://localhost:8000/api/v1/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"Why is CPU high?","context":{}}'
```

---

## 🔑 Environment Variables Summary

```env
# Critical - Must Provide
GROQ_API_KEY=your_key_here
HUGGINGFACE_API_TOKEN=your_token_here

# Database URLs
DATABASE_URL=postgresql://user:pass@localhost:5432/db
INFLUXDB_URL=http://localhost:8086
REDIS_HOST=localhost

# Optional
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=optional
```

---

## 📊 Project Structure at a Glance

```
📁 Project Root/
├── 📁 backend/           ← FastAPI REST API
├── 📁 frontend/          ← Streamlit Dashboard
├── 📁 ml_engine/         ← ML Models & LLM Integration
├── 📁 data_pipeline/     ← Data Collection & Processing
├── .env                  ← Your API keys go HERE
├── .env.example          ← Template
├── docker-compose.yml    ← One-command startup
└── README.md            ← Full documentation
```

---

## 🐛 Common Issues & Solutions

### Issue: "GROQ_API_KEY not found"
**Solution**: Make sure you created `.env` file and added your key

### Issue: "Connection refused to database"
**Solution**: Either use Docker (`docker-compose up`) or ensure PostgreSQL is running

### Issue: "Ollama not available"
**Solution**: Download from https://ollama.ai and run `ollama serve`

### Issue: "Port already in use"
**Solution**: Change ports in docker-compose.yml or kill existing process

---

## 📚 Next Steps

1. **Read Full Documentation**: See [README.md](./README.md)
2. **Explore API**: Visit http://localhost:8000/docs
3. **Run ML Training**: Open `ml_engine/model_training.ipynb`
4. **Deploy to Production**: See [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)

---

## 🆘 Need Help?

- Check [README.md](./README.md) for detailed docs
- Review API docs at http://localhost:8000/docs
- Check logs: `docker logs monitoring-backend`
- Open GitHub issue with error details

---

**Ready to go! Start with Docker:**
```bash
docker-compose up -d
# Then visit http://localhost:8501
```

Happy Monitoring! 🚀
