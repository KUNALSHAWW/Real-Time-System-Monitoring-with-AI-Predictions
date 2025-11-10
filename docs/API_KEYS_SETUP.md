# API Keys Setup Guide

## 🔑 Getting Your API Keys

### 1. GROQ API Key (Required)

**What is GROQ?**
- Fastest LLM inference service available
- Provides access to Llama 2, Mixtral, and other open-source models
- Free tier with generous rate limits

**Steps:**
1. Go to https://console.groq.com/keys
2. Sign up or log in
3. Create a new API key
4. Copy the key and add to `.env`:
   ```env
   GROQ_API_KEY=gsk_your_key_here
   ```

**Test Your Key:**
```bash
curl -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2-70b-4096",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

**Available Models:**
- `llama2-70b-4096` - Most capable, slower
- `mixtral-8x7b-32768` - Balanced
- `llama-3.1-8b-instant` - Fastest

---

### 2. Hugging Face API Token (Required)

**What is Hugging Face?**
- Access to thousands of pre-trained models
- Free community models and commercial options
- Used for text classification, sentiment analysis, embeddings

**Steps:**
1. Go to https://huggingface.co/settings/tokens
2. Create New Token (READ access is enough)
3. Copy and add to `.env`:
   ```env
   HUGGINGFACE_API_TOKEN=hf_your_token_here
   ```

**Recommended Models:**
- `distilbert-base-uncased-finetuned-sst-2-english` - Sentiment analysis
- `gpt2` - Text generation
- `roberta-base` - Classification

**Test Your Token:**
```bash
curl -X GET https://huggingface.co/api/user \
  -H "Authorization: Bearer YOUR_HF_TOKEN"
```

---

### 3. OpenAI API Key (Optional - Recommended as Fallback)

**When to use:**
- Fallback when GROQ/Ollama unavailable
- More reliable but slower and costs money

**Steps:**
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Add to `.env`:
   ```env
   OPENAI_API_KEY=sk_your_key_here
   ```

**Cost:** ~$0.002 per 1,000 tokens

---

### 4. Ollama (Local LLM - Free, No Keys Needed!)

**What is Ollama?**
- Run LLMs locally on your machine
- No API costs, no rate limits
- Works offline

**Steps:**
1. Download from https://ollama.ai
2. Install and run:
   ```bash
   ollama serve
   ```
3. In another terminal, pull models:
   ```bash
   ollama pull llama2
   ollama pull mistral
   ollama pull neural-chat
   ```
4. Update `.env`:
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama2
   ```

**Test:**
```bash
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"llama2","prompt":"Hello"}'
```

---

## 📋 Database Credentials Setup

### PostgreSQL

**If using Docker:**
```bash
docker run --name postgres \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=system_monitoring \
  -p 5432:5432 \
  -d postgres:15
```

**Update .env:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/system_monitoring
```

### Redis

**If using Docker:**
```bash
docker run --name redis \
  -p 6379:6379 \
  -d redis:7
```

**Update .env:**
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Leave empty if no password
```

### InfluxDB

**If using Docker:**
```bash
docker run --name influxdb \
  -e INFLUXDB_DB=system_metrics \
  -e INFLUXDB_ADMIN_USER=admin \
  -e INFLUXDB_ADMIN_PASSWORD=password \
  -p 8086:8086 \
  -d influxdb:2.0
```

**Update .env:**
```env
INFLUXDB_URL=http://localhost:8086
INFLUXDB_ORG=your_org
INFLUXDB_BUCKET=system_metrics
INFLUXDB_TOKEN=your_token  # Generate in UI
```

---

## ✅ Validation Checklist

```
GROQ:
- [ ] Got API key from console.groq.com
- [ ] Added to .env file
- [ ] Test curl command succeeded

HuggingFace:
- [ ] Got token from huggingface.co
- [ ] Added to .env file
- [ ] Token has READ access

Ollama (Optional):
- [ ] Downloaded and installed
- [ ] Running 'ollama serve'
- [ ] Pulled at least one model
- [ ] http://localhost:11434 accessible

Databases:
- [ ] PostgreSQL running/accessible
- [ ] Redis running/accessible
- [ ] InfluxDB running/accessible
- [ ] All credentials in .env

Environment File:
- [ ] .env file created from .env.example
- [ ] All required keys added
- [ ] No extra quotes around values
```

---

## 🚀 Quick Verification

```bash
# 1. Check .env file exists and is readable
ls -la .env

# 2. Verify GROQ key works
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('GROQ:', len(os.getenv('GROQ_API_KEY')))"

# 3. Verify HF token works
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('HF:', len(os.getenv('HUGGINGFACE_API_TOKEN')))"

# 4. Test database connections
psql -U user -h localhost -d system_monitoring -c "SELECT 1"
redis-cli ping
curl http://localhost:8086/api/v1/query
```

---

## 🆘 Troubleshooting

### "Invalid GROQ API Key"
- Check key starts with `gsk_`
- Key should be 50+ characters
- Go to https://console.groq.com/keys to generate new one

### "Hugging Face token not working"
- Token should be READ access minimum
- Check at https://huggingface.co/settings/tokens
- Regenerate if unsure

### "Connection refused" for Ollama
- Make sure `ollama serve` is running
- Default port is 11434
- Check http://localhost:11434/api/tags

### "PostgreSQL authentication failed"
- Verify DATABASE_URL format: `postgresql://user:pass@host:port/db`
- Check password doesn't have special characters (URL encode if needed)
- Test with: `psql $DATABASE_URL`

---

## 📝 Example .env File (After Setup)

```env
# APIs
GROQ_API_KEY=gsk_your_actual_key_from_console_groq_com
HUGGINGFACE_API_TOKEN=hf_your_actual_token_from_huggingface_co
OPENAI_API_KEY=sk_your_openai_key_optional

# Databases
DATABASE_URL=postgresql://user:password@localhost:5432/system_monitoring
REDIS_HOST=localhost
REDIS_PORT=6379
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=your_org
INFLUXDB_BUCKET=system_metrics

# Ollama (for local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# App Config
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=change_this_in_production
```

---

## 🎓 Security Notes

1. **Never commit .env** - Always add to .gitignore
2. **Rotate keys regularly** - Regenerate quarterly
3. **Use environment variables** - Don't hardcode keys
4. **Limit key permissions** - Use READ-only where possible
5. **Monitor usage** - Check API dashboards for suspicious activity

---

**You're all set! Now run:**
```bash
docker-compose up
```

Visit http://localhost:8501 and start monitoring! 🚀
