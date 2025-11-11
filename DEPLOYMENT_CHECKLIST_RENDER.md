# 🚀 Quick Deployment Checklist

## Before Deployment

### 1. Prepare Your Repository
- [ ] Commit all changes to Git
- [ ] Push to GitHub
- [ ] Ensure `render.yaml` is in root directory
- [ ] Verify Dockerfiles are correct

### 2. Get API Keys (if using AI features)
- [ ] GROQ API Key from [console.groq.com](https://console.groq.com)
- [ ] Hugging Face API Key from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

### 3. Create Render Account
- [ ] Sign up at [render.com](https://render.com)
- [ ] Connect your GitHub account
- [ ] Verify email address

---

## Deployment Steps

### Using Blueprint (Recommended - 5 minutes)

1. **Push Code**
   ```bash
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   ```

2. **Deploy on Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Blueprint"
   - Select your repository
   - Click "Apply"

3. **Add Secret Variables**
   
   Navigate to **Backend Service** → Environment:
   ```
   GROQ_API_KEY=your_actual_key_here
   HUGGINGFACE_API_KEY=your_actual_key_here
   ```

4. **Wait for Build** (5-10 minutes)
   - Monitor logs in real-time
   - Both services will build automatically

5. **Test Your App**
   - Backend: `https://system-monitoring-backend.onrender.com/health`
   - Frontend: `https://system-monitoring-frontend.onrender.com`

---

## Post-Deployment

### Testing Checklist
- [ ] Backend health endpoint returns `{"status": "healthy"}`
- [ ] Frontend loads without errors
- [ ] Real-time metrics display
- [ ] WebSocket connection works
- [ ] Charts and graphs render
- [ ] No console errors

### Optional Enhancements
- [ ] Set up custom domain
- [ ] Enable auto-deploy on Git push
- [ ] Upgrade to paid tier for 24/7 availability
- [ ] Add monitoring/alerting
- [ ] Configure backup strategy

---

## Quick URLs After Deployment

Replace with your actual Render URLs:

- **Frontend**: `https://system-monitoring-frontend.onrender.com`
- **Backend API**: `https://system-monitoring-backend.onrender.com`
- **API Docs**: `https://system-monitoring-backend.onrender.com/docs`
- **Health Check**: `https://system-monitoring-backend.onrender.com/health`

---

## Common Issues & Quick Fixes

### ❌ Build Failed
```bash
# Test locally first
cd backend
docker build -t test-backend .
```

### ❌ Frontend Can't Connect
- Check `BACKEND_URL` in frontend environment variables
- Ensure it's `https://` not `http://`

### ❌ WebSocket Error
- Use `wss://` for secure WebSocket connections
- Check CORS settings in backend

### ❌ Service Keeps Sleeping
- Free tier sleeps after 15 min inactivity
- Upgrade to Starter plan ($7/month) for always-on

---

## Need Help?

1. Check `RENDER_DEPLOYMENT_GUIDE.md` for detailed instructions
2. View logs in Render Dashboard
3. Test locally with Docker first
4. Check [Render Documentation](https://render.com/docs)

---

**Estimated Deployment Time**: 10-15 minutes
**Difficulty**: Easy ⭐⭐☆☆☆

Good luck! 🚀
