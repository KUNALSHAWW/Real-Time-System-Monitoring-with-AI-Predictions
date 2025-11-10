import os

# Project Information
PROJECT_NAME = "Real-Time System Monitoring with AI Predictions"
VERSION = "1.0.0"
AUTHOR = "Enterprise Development Team"
CREATED = "2024-11-10"

# Project Structure
PROJECT_STRUCTURE = {
    "backend": {
        "description": "FastAPI REST API with authentication and state management",
        "main": "main.py",
        "features": [
            "JWT Authentication",
            "6+ Router modules",
            "State management with Redis",
            "Comprehensive logging",
            "Error handling middleware"
        ]
    },
    "frontend": {
        "description": "Streamlit real-time monitoring dashboard",
        "main": "app.py",
        "features": [
            "6 dashboard pages",
            "Real-time visualizations",
            "Incident management",
            "AI analysis interface",
            "Interactive charts"
        ]
    },
    "ml_engine": {
        "description": "Machine learning and LLM integration",
        "components": [
            "llm_manager.py - GROQ/Ollama/HuggingFace",
            "anomaly_detector.py - ML models",
            "model_training.ipynb - Training notebook"
        ],
        "features": [
            "Isolation Forest anomaly detection",
            "GROQ fast LLM inference",
            "Ollama local model support",
            "HuggingFace transformers",
            "Intelligent model routing"
        ]
    },
    "data_pipeline": {
        "description": "Data collection and processing",
        "main": "data_pipeline.py",
        "features": [
            "Async data processing",
            "Circular buffer caching",
            "Batch processing",
            "Time-series support"
        ]
    }
}

# Required API Keys
REQUIRED_API_KEYS = {
    "GROQ_API_KEY": {
        "description": "Fast LLM inference",
        "url": "https://console.groq.com/keys",
        "cost": "Free tier available",
        "required": True
    },
    "HUGGINGFACE_API_TOKEN": {
        "description": "Access to pre-trained models",
        "url": "https://huggingface.co/settings/tokens",
        "cost": "Free (community models)",
        "required": True
    },
    "OPENAI_API_KEY": {
        "description": "Fallback LLM provider",
        "url": "https://platform.openai.com/api-keys",
        "cost": "~$0.002/1K tokens",
        "required": False
    }
}

# Optional Services
OPTIONAL_SERVICES = {
    "Ollama": {
        "description": "Local LLM support",
        "download": "https://ollama.ai",
        "cost": "Free",
        "offline": True
    },
    "PagerDuty": {
        "description": "Incident alerting",
        "cost": "Paid",
        "offline": False
    },
    "Slack": {
        "description": "Notifications",
        "cost": "Free/Paid",
        "offline": False
    }
}

# Database Configuration
DATABASES = {
    "PostgreSQL": {
        "description": "Relational database for metadata",
        "default_port": 5432,
        "docker": True,
        "required": True
    },
    "Redis": {
        "description": "Cache and state management",
        "default_port": 6379,
        "docker": True,
        "required": True
    },
    "InfluxDB": {
        "description": "Time-series database",
        "default_port": 8086,
        "docker": True,
        "required": True
    }
}

# Documentation Files
DOCUMENTATION = {
    "README.md": "Complete project documentation",
    "QUICKSTART.md": "5-minute setup guide",
    "PROJECT_DELIVERY_SUMMARY.md": "Delivery details and features",
    "DELIVERABLES.md": "Complete deliverables checklist",
    "docs/API_KEYS_SETUP.md": "API key setup instructions",
    "ml_engine/model_training.ipynb": "ML training and experimentation"
}

# Features Summary
FEATURES = {
    "Real-Time Monitoring": [
        "CPU, Memory, Disk, Network metrics",
        "Multi-host support",
        "Custom metrics",
        "5-second granularity"
    ],
    "Anomaly Detection": [
        "Isolation Forest model",
        "Local Outlier Factor",
        "Configurable thresholds",
        "Severity levels"
    ],
    "Predictive Analytics": [
        "Time-series forecasting",
        "Anomaly risk scoring",
        "Trend analysis",
        "Alert predictions"
    ],
    "AI Integration": [
        "GROQ fast inference",
        "Ollama local models",
        "HuggingFace transformers",
        "Intelligent routing"
    ],
    "State Management": [
        "Redis-backed caching",
        "Session persistence",
        "Automatic cleanup",
        "Performance metrics"
    ]
}

# API Endpoints
API_ENDPOINTS = {
    "Authentication": [
        "POST /api/v1/auth/login",
        "POST /api/v1/auth/register",
        "GET /api/v1/auth/me"
    ],
    "Metrics": [
        "GET /api/v1/metrics/cpu",
        "GET /api/v1/metrics/memory",
        "GET /api/v1/metrics/disk",
        "GET /api/v1/metrics/network",
        "POST /api/v1/metrics/custom"
    ],
    "Anomalies": [
        "GET /api/v1/anomalies/list",
        "GET /api/v1/anomalies/metrics/{name}",
        "POST /api/v1/anomalies/analyze"
    ],
    "Predictions": [
        "GET /api/v1/predictions/forecast/{metric}",
        "GET /api/v1/predictions/anomaly-risk",
        "GET /api/v1/predictions/alerts/predictive"
    ],
    "Incidents": [
        "GET /api/v1/incidents/list",
        "POST /api/v1/incidents/create",
        "PUT /api/v1/incidents/update/{id}"
    ],
    "AI Analysis": [
        "POST /api/v1/analysis/analyze",
        "POST /api/v1/analysis/incident-summary",
        "GET /api/v1/analysis/models"
    ]
}

# Docker Services
DOCKER_SERVICES = {
    "postgres": "PostgreSQL 15",
    "redis": "Redis 7",
    "influxdb": "InfluxDB 2.7",
    "backend": "FastAPI backend",
    "frontend": "Streamlit frontend",
    "prometheus": "Prometheus (optional)"
}

# Quick Commands
QUICK_COMMANDS = {
    "Setup": "cp .env.example .env && nano .env",
    "Start": "docker-compose up -d",
    "Frontend": "http://localhost:8501",
    "API": "http://localhost:8000",
    "API Docs": "http://localhost:8000/docs",
    "Stop": "docker-compose down",
    "Logs": "docker-compose logs -f"
}

# File Statistics
FILE_STATISTICS = {
    "Python Files": 15,
    "Jupyter Notebooks": 1,
    "Docker Files": 3,
    "Configuration Files": 10,
    "Documentation Files": 3,
    "Total Lines of Code": 3000,
    "API Endpoints": 20,
    "Frontend Pages": 6,
    "ML Models": 2
}

# Project Status
PROJECT_STATUS = {
    "Backend": "✅ Complete",
    "Frontend": "✅ Complete",
    "ML Engine": "✅ Complete",
    "Data Pipeline": "✅ Complete",
    "Docker Setup": "✅ Complete",
    "Documentation": "✅ Complete",
    "Testing": "✅ Included",
    "Deployment Ready": "✅ Yes"
}

def print_project_info():
    """Print project information"""
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║         {PROJECT_NAME}        ║
║                      Version {VERSION}                         ║
╚═══════════════════════════════════════════════════════════════════╝

📊 PROJECT STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    
    for module, info in PROJECT_STRUCTURE.items():
        print(f"  📁 {module.upper()}")
        print(f"     Description: {info['description']}")
        if 'features' in info:
            for feature in info['features'][:2]:
                print(f"     ✓ {feature}")
        print()

def print_quick_start():
    """Print quick start guide"""
    print("""
🚀 QUICK START (5 MINUTES)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Copy .env template:
   cp .env.example .env

2. Add your API keys to .env:
   - GROQ_API_KEY (from https://console.groq.com/keys)
   - HUGGINGFACE_API_TOKEN (from https://huggingface.co/settings/tokens)

3. Start with Docker:
   docker-compose up -d

4. Access services:
   - Dashboard: http://localhost:8501
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

📚 DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    
    for doc, description in DOCUMENTATION.items():
        print(f"  📄 {doc}")
        print(f"     {description}\n")

def print_features():
    """Print features"""
    print("""
✨ KEY FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    
    for category, items in FEATURES.items():
        print(f"  • {category}")
        for item in items:
            print(f"    ✓ {item}")
        print()

def print_status():
    """Print project status"""
    print("""
✅ PROJECT STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    
    for component, status in PROJECT_STATUS.items():
        print(f"  {status} {component}")
    
    print(f"""
📊 STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Python Files: {FILE_STATISTICS['Python Files']}
  • Jupyter Notebooks: {FILE_STATISTICS['Jupyter Notebooks']}
  • API Endpoints: {FILE_STATISTICS['API Endpoints']}
  • Total Lines of Code: {FILE_STATISTICS['Total Lines of Code']}+
""")

if __name__ == "__main__":
    print_project_info()
    print_quick_start()
    print_features()
    print_status()
    
    print(f"""
🎯 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Read README.md for complete documentation
  2. Follow QUICKSTART.md for setup
  3. Check docs/API_KEYS_SETUP.md for API keys
  4. Run: docker-compose up -d
  5. Visit: http://localhost:8501

📞 SUPPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Full Documentation: README.md
  • Setup Issues: QUICKSTART.md
  • API Keys: docs/API_KEYS_SETUP.md
  • Troubleshooting: README.md (Troubleshooting section)
  • ML Training: ml_engine/model_training.ipynb

═════════════════════════════════════════════════════════════════════
🎉 Project ready for production deployment!
═════════════════════════════════════════════════════════════════════
""")
