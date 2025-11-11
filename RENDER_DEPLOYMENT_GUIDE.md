# 🚀 Render Deployment Guide
## Real-Time System Monitoring with AI Predictions

This guide will help you deploy both the backend and frontend to Render.com.

---

## 📋 Prerequisites

1. **GitHub Account** - Your code should be in a GitHub repository
2. **Render Account** - Sign up at [render.com](https://render.com)
3. **API Keys** (if using AI features):
   - GROQ API Key
   - Hugging Face API Key

---

## 🎯 Deployment Options

### Option 1: Blueprint Deployment (Recommended - Deploys Everything)

This deploys both backend and frontend with one click.

#### Steps:

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Deploy via Render Blueprint**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click **"New +"** → **"Blueprint"**
   - Connect your GitHub repository
   - Select the repository with your project
   - Render will detect `render.yaml` automatically
   - Click **"Apply"**

3. **Configure Environment Variables**
   
   After blueprint is applied, go to each service and add secret variables:
   
   **Backend Service:**
   - `GROQ_API_KEY`: Your GROQ API key
   - `HUGGINGFACE_API_KEY`: Your Hugging Face API key
   
   **Frontend Service:**
   - Environment variables are automatically set from backend URL

4. **Wait for Deployment**
   - Backend: ~5-10 minutes
   - Frontend: ~5-10 minutes
   - Check logs for any errors

5. **Access Your Application**
   - Backend: `https://system-monitoring-backend.onrender.com`
   - Frontend: `https://system-monitoring-frontend.onrender.com`

---

### Option 2: Manual Deployment (More Control)

Deploy each service separately.

#### Deploy Backend First:

1. **Create New Web Service**
   - Go to Render Dashboard
   - Click **"New +"** → **"Web Service"**
   - Connect your repository
   - Configure:
     - **Name**: `system-monitoring-backend`
     - **Region**: Choose closest to your users
     - **Branch**: `main`
     - **Root Directory**: `backend`
     - **Environment**: `Docker`
     - **Dockerfile Path**: `backend/Dockerfile`
     - **Plan**: Free (or upgrade for better performance)

2. **Add Environment Variables**
   ```
   PORT=10000
   GROQ_API_KEY=your_groq_api_key_here
   HUGGINGFACE_API_KEY=your_hf_api_key_here
   LOG_LEVEL=INFO
   DEBUG=false
   CORS_ORIGINS=*
   ```

3. **Deploy**
   - Click **"Create Web Service"**
   - Wait for deployment to complete
   - Note the URL: `https://system-monitoring-backend.onrender.com`

#### Deploy Frontend:

1. **Create New Web Service**
   - Click **"New +"** → **"Web Service"**
   - Connect same repository
   - Configure:
     - **Name**: `system-monitoring-frontend`
     - **Region**: Same as backend
     - **Branch**: `main`
     - **Root Directory**: `frontend`
     - **Environment**: `Docker`
     - **Dockerfile Path**: `frontend/Dockerfile`
     - **Plan**: Free (or upgrade)

2. **Add Environment Variables**
   ```
   PORT=10000
   BACKEND_URL=https://system-monitoring-backend.onrender.com
   STREAMLIT_SERVER_PORT=10000
   STREAMLIT_SERVER_ADDRESS=0.0.0.0
   STREAMLIT_SERVER_HEADLESS=true
   ```

3. **Deploy**
   - Click **"Create Web Service"**
   - Wait for deployment
   - Access at: `https://system-monitoring-frontend.onrender.com`

---

## 🔧 Configuration Details

### Backend Configuration

The backend requires these environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `PORT` | Port to run on (Render sets to 10000) | Auto-set |
| `GROQ_API_KEY` | GROQ API key for LLM | Optional* |
| `HUGGINGFACE_API_KEY` | Hugging Face API key | Optional* |
| `CORS_ORIGINS` | Allowed CORS origins | Yes |
| `LOG_LEVEL` | Logging level (INFO/DEBUG) | No |
| `DEBUG` | Debug mode (true/false) | No |

*Required only if using AI analysis features

### Frontend Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `PORT` | Port to run on | Auto-set |
| `BACKEND_URL` | Backend API URL | Yes |
| `STREAMLIT_SERVER_PORT` | Streamlit port | Auto-set |

---

## 🌐 WebSocket Support

Render fully supports WebSocket connections! Your real-time features will work:

- ✅ Real-time metrics streaming
- ✅ Live alerts and notifications
- ✅ Bidirectional communication

WebSocket endpoints:
- `wss://system-monitoring-backend.onrender.com/api/ws/ws`
- `wss://system-monitoring-backend.onrender.com/api/ws/alerts`

---

## 📊 Free Tier Limitations

**Render Free Tier includes:**
- ✅ 750 hours/month (enough for 1 service running 24/7)
- ✅ Automatic SSL certificates
- ✅ Automatic deployments from GitHub
- ⚠️ Services spin down after 15 minutes of inactivity
- ⚠️ Cold start time: ~30-60 seconds when spinning up

**Recommendation:** 
- For 24/7 availability, upgrade to **Starter Plan** ($7/month per service)
- For production use with better performance, use **Standard Plan**

---

## 🔍 Troubleshooting

### Issue: "Build Failed"

**Check:**
1. Dockerfile syntax
2. All required files are present
3. Requirements.txt dependencies are compatible
4. Logs in Render dashboard

**Solution:**
```bash
# Test locally first
cd backend
docker build -t backend-test .
docker run -p 10000:10000 backend-test

cd ../frontend
docker build -t frontend-test .
docker run -p 10000:10000 -e BACKEND_URL=http://localhost:8000 frontend-test
```

### Issue: "Frontend can't connect to backend"

**Check:**
1. Backend URL is correct in frontend environment variables
2. Backend service is running and healthy
3. CORS is properly configured

**Solution:**
- Ensure `BACKEND_URL` in frontend uses `https://` (not `http://`)
- Update CORS_ORIGINS in backend if needed

### Issue: "WebSocket connection failed"

**Check:**
1. Use `wss://` (not `ws://`) for secure connections
2. Backend WebSocket endpoint is accessible

**Solution:**
Update WebSocket URL in frontend to use secure protocol:
```python
ws_url = API_BASE_URL.replace('https://', 'wss://').replace('http://', 'ws://')
```

### Issue: "Service keeps spinning down"

**Cause:** Free tier spins down after 15 minutes of inactivity

**Solution:**
- Upgrade to Starter plan ($7/month) for always-on service
- Or implement a health check pinger (though not recommended for free tier)

---

## 🚀 Post-Deployment Steps

1. **Test all features:**
   - [ ] Dashboard loads correctly
   - [ ] Real-time metrics update
   - [ ] WebSocket connections work
   - [ ] AI predictions (if enabled)
   - [ ] Alerts and notifications

2. **Monitor performance:**
   - Check Render metrics dashboard
   - Monitor response times
   - Check error logs

3. **Set up custom domain (optional):**
   - Go to service settings
   - Add custom domain
   - Configure DNS records

4. **Enable auto-deploy:**
   - Already enabled in blueprint
   - Every push to `main` branch auto-deploys

---

## 💰 Pricing Recommendations

### For Development/Testing:
- **Backend**: Free tier
- **Frontend**: Free tier
- **Total**: $0/month

### For Small Production Use:
- **Backend**: Starter ($7/month)
- **Frontend**: Free tier
- **Total**: $7/month

### For Production with High Traffic:
- **Backend**: Standard ($25/month)
- **Frontend**: Starter ($7/month)
- **Database**: Starter ($7/month) if needed
- **Total**: ~$39/month

---

## 📝 Quick Commands

### View Logs:
```bash
# In Render Dashboard
Services → [Your Service] → Logs
```

### Redeploy:
```bash
# Option 1: Via GitHub
git push origin main

# Option 2: Via Render Dashboard
Services → [Your Service] → Manual Deploy → Deploy latest commit
```

### Check Health:
```bash
# Backend
curl https://system-monitoring-backend.onrender.com/health

# Frontend
curl https://system-monitoring-frontend.onrender.com
```

---

## 🎉 Success Checklist

- [ ] Both services deployed successfully
- [ ] Environment variables configured
- [ ] Backend health check returns 200
- [ ] Frontend loads in browser
- [ ] Real-time data updates work
- [ ] WebSocket connections established
- [ ] No errors in logs
- [ ] Custom domain configured (optional)

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Render Discord Community](https://discord.gg/render)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Streamlit Deployment Guide](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app)

---

## 🆘 Need Help?

1. **Check Render Logs**: Most issues show up here
2. **Render Community**: [community.render.com](https://community.render.com)
3. **GitHub Issues**: Create an issue in your repository
4. **Documentation**: Check project docs in `/docs` folder

---

## 🔒 Security Notes

1. **Never commit API keys** - Use Render's environment variables
2. **Use HTTPS** - Render provides free SSL
3. **Enable CORS properly** - Restrict origins in production
4. **Monitor logs** - Watch for suspicious activity
5. **Update dependencies** - Keep packages up to date

---

**Happy Deploying! 🚀**

If you encounter any issues, check the troubleshooting section or reach out to the Render community.
