# 🚀 Hugging Face Spaces Deployment Guide

This guide will walk you through deploying both the **Backend** and **Frontend** of your Real-Time System Monitoring application on Hugging Face Spaces for **FREE**.

## 📋 Prerequisites

1. A Hugging Face account (sign up at [huggingface.co](https://huggingface.co))
2. Your project code on GitHub (recommended) or ready to upload

## 🎯 Deployment Strategy

You will create **TWO separate Spaces**:
1. **Backend Space** - FastAPI backend (Docker Space)
2. **Frontend Space** - Streamlit frontend (Docker Space)

The frontend will communicate with the backend via its public URL.

---

## 🔧 Step 1: Deploy the Backend

### 1.1 Create Backend Space

1. Go to [huggingface.co](https://huggingface.co) and sign in
2. Click on your profile → **"New Space"**
3. Configure the Space:
   - **Owner**: Your username or organization
   - **Space name**: `system-monitoring-backend` (or your choice)
   - **License**: `mit` (or your preference)
   - **Select the Space SDK**: Choose **Docker**
   - **Space hardware**: `CPU basic` (free tier)
   - **Visibility**: Public or Private (your choice)
4. Click **"Create Space"**

### 1.2 Upload Backend Code

You have two options:

#### Option A: Using Git (Recommended)

```bash
# Clone the Space repository
git clone https://huggingface.co/spaces/YOUR-USERNAME/system-monitoring-backend
cd system-monitoring-backend

# Copy your backend files
cp -r /path/to/your/project/backend/* .

# Commit and push
git add .
git commit -m "Initial backend deployment"
git push
```

#### Option B: Using Web Interface

1. In your Space, click on **"Files and versions"** tab
2. Click **"Add file"** → **"Upload files"**
3. Upload ALL files from your `backend/` folder:
   - `Dockerfile`
   - `main.py`
   - `requirements.txt`
   - All folders: `core/`, `routers/`, `middleware/`, etc.
4. Make sure `Dockerfile` is in the **root** of the Space

### 1.3 Wait for Build

- HF Spaces will automatically detect the `Dockerfile` and start building
- This may take 5-10 minutes
- Once complete, you'll see your backend running at: `https://YOUR-USERNAME-system-monitoring-backend.hf.space`

### 1.4 Test the Backend

Visit: `https://YOUR-USERNAME-system-monitoring-backend.hf.space/docs`

You should see the FastAPI Swagger documentation page.

---

## 🎨 Step 2: Deploy the Frontend

### 2.1 Create Frontend Space

1. Go back to [huggingface.co](https://huggingface.co)
2. Click **"New Space"** again
3. Configure the Space:
   - **Space name**: `system-monitoring-dashboard` (or your choice)
   - **License**: `mit`
   - **Select the Space SDK**: Choose **Docker**
   - **Space hardware**: `CPU basic` (free tier)
   - **Visibility**: Public or Private
4. Click **"Create Space"**

### 2.2 Upload Frontend Code

#### Option A: Using Git

```bash
# Clone the Space repository
git clone https://huggingface.co/spaces/YOUR-USERNAME/system-monitoring-dashboard
cd system-monitoring-dashboard

# Copy your frontend files
cp -r /path/to/your/project/frontend/* .

# Commit and push
git add .
git commit -m "Initial frontend deployment"
git push
```

#### Option B: Using Web Interface

1. Click **"Files and versions"** → **"Add file"** → **"Upload files"**
2. Upload ALL files from your `frontend/` folder:
   - `Dockerfile`
   - `app_final.py` (or `app.py`)
   - `requirements.txt`
   - `metrics_fetcher.py`
   - `websocket_client.py`
   - Any other Python files

### 2.3 Configure Backend URL Secret

🔐 **IMPORTANT**: You must configure the backend URL as a secret!

1. In your **frontend Space**, go to **"Settings"** tab
2. Scroll down to **"Repository secrets"**
3. Click **"New secret"**
4. Add the secret:
   - **Name**: `BACKEND_URL`
   - **Secret value**: `https://YOUR-USERNAME-system-monitoring-backend.hf.space`
   
   ⚠️ **Important**: 
   - Use your actual backend Space URL
   - Do NOT include a trailing slash
   - Example: `https://kunalshaww-system-monitoring-backend.hf.space`

5. Click **"Save"**

### 2.4 Restart the Space

After adding the secret, your Space should automatically restart. If not:
1. Go to **"Settings"** tab
2. Click **"Factory reboot"** under the "Manage space" section

### 2.5 Access Your Dashboard

Visit: `https://YOUR-USERNAME-system-monitoring-dashboard.hf.space`

You should see your Streamlit dashboard fully functional!

---

## ✅ Verification Checklist

### Backend Verification
- [ ] Backend Space is running (green status)
- [ ] Can access `/docs` endpoint
- [ ] Can access `/health` endpoint
- [ ] API returns valid JSON responses

### Frontend Verification
- [ ] Frontend Space is running (green status)
- [ ] Dashboard loads without errors
- [ ] Can see "Backend Connected" status (or connection indicator)
- [ ] Metrics are displayed (real or simulated)
- [ ] Charts and visualizations render correctly

---

## 🔍 Troubleshooting

### Backend Issues

**Problem**: Build fails
- Check `Dockerfile` is in the root directory
- Verify `requirements.txt` has all dependencies
- Check build logs in the Space for specific errors

**Problem**: Space is running but returns errors
- Check the logs tab in your Space
- Verify port 7860 is being used in the Dockerfile
- Make sure `uvicorn` command is correct

### Frontend Issues

**Problem**: Cannot connect to backend
- Verify the `BACKEND_URL` secret is set correctly
- Check there's no trailing slash in the URL
- Ensure backend Space is running and accessible
- Test backend URL manually: visit `YOUR-BACKEND-URL/health`

**Problem**: "Module not found" errors
- Check all Python files are uploaded
- Verify `requirements.txt` includes all dependencies
- Check the import statements in your code

**Problem**: Streamlit won't start
- Verify the correct main file is specified in Dockerfile CMD
- Check if it's `app.py`, `app_final.py`, or another file
- Ensure port 7860 is configured in Streamlit config

---

## 🎓 Tips for Success

1. **Test Locally First**: Before deploying, test with Docker locally:
   ```bash
   # Backend
   cd backend
   docker build -t backend .
   docker run -p 7860:7860 backend
   
   # Frontend
   cd frontend
   docker build -t frontend .
   docker run -p 7860:7860 -e BACKEND_URL=http://localhost:8000 frontend
   ```

2. **Check Dependencies**: Make sure torch and heavy ML libraries are actually needed. They increase build time and space requirements.

3. **Monitor Resources**: Free tier has limitations. If your app uses too much memory, consider:
   - Reducing model sizes
   - Using lighter dependencies
   - Implementing caching

4. **CORS Configuration**: Your backend already has CORS enabled for all origins, which is perfect for this setup.

5. **Logs Are Your Friend**: Always check the "Logs" tab in your Spaces for debugging.

---

## 📊 Expected URLs

After successful deployment:

- **Backend API**: `https://YOUR-USERNAME-system-monitoring-backend.hf.space`
- **API Docs**: `https://YOUR-USERNAME-system-monitoring-backend.hf.space/docs`
- **Frontend Dashboard**: `https://YOUR-USERNAME-system-monitoring-dashboard.hf.space`

---

## 🎉 Success!

If both Spaces are running and the frontend can communicate with the backend, congratulations! Your full-stack monitoring application is now deployed and accessible to anyone on the internet, completely free!

### Share Your Project
- Share the frontend URL with others
- Add it to your GitHub README
- Include it in your portfolio

---

## 💡 Next Steps (Optional)

1. **Custom Domain**: HF Spaces supports custom domains (paid feature)
2. **Persistent Storage**: Add HF Spaces persistent storage if needed
3. **Authentication**: Implement user authentication for production use
4. **Monitoring**: Set up uptime monitoring for your Spaces
5. **CI/CD**: Automate deployments via GitHub Actions

---

## 📝 Notes

- **Free Tier Limitations**:
  - Spaces may sleep after inactivity (restart on first access)
  - Limited CPU/Memory resources
  - No persistent disk storage between restarts
  
- **Upgrading**: You can upgrade to paid hardware tiers if you need better performance

---

## 🆘 Need Help?

- [Hugging Face Spaces Documentation](https://huggingface.co/docs/hub/spaces)
- [Hugging Face Community Forums](https://discuss.huggingface.co/)
- Check your Space's "Community" tab for support

---

**Happy Deploying! 🚀**
