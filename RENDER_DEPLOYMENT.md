# Deploying Gen AI Platform on Render

This guide provides step-by-step instructions for deploying the **Gen AI Platform for Automated Content Transformation** to [Render](https://render.com) as a production-grade Web Service.

---

## 📋 Render Deployment Summary

| Parameter | Configuration Value |
| :--- | :--- |
| **Service Type** | **Web Service** |
| **Runtime** | **Python 3** |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |
| **Health Check Path** | `/api/health` |

---

## 🗄️ Step 1: Set Up MongoDB Atlas (For Persistent Storage)

Cloud hosting platforms like Render feature **ephemeral file systems**—any local files (such as local JSON files) are erased whenever the service restarts, redeploys, or scales. To ensure user accounts and transformation history persist permanently, configure a free MongoDB Atlas cloud database.

1. **Create an Account:**
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) and sign up for a free account.
2. **Create a Free Cluster:**
   - Choose the **M0 Shared** (Free forever) cluster tier.
   - Select a cloud provider and region closest to your Render service (e.g. AWS / us-east-1).
   - Click **Create Deployment**.
3. **Set Up Database User Credentials:**
   - In **Security > Database Access**, click **Add New Database User**.
   - Choose **Password Authentication**.
   - Enter a username (e.g. `appuser`) and secure password (avoid special characters like `@` or `:` in the password, or URL-encode them).
   - Assign the **Read and write to any database** privilege.
4. **Configure Network Access (Crucial for Render):**
   - In **Security > Network Access**, click **Add IP Address**.
   - Select **Allow Access from Anywhere** (`0.0.0.0/0`).
   - *Note: Render instances use dynamic IPs, so whitelisting 0.0.0.0/0 is required.*
5. **Get Connection String:**
   - Click **Connect** on your cluster overview.
   - Choose **Drivers** (Python).
   - Copy the connection string format:
     ```
     mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
     ```
   - Replace `<username>` and `<password>` with your database user credentials.

---

## 🚀 Step 2: Push Your Project to GitHub / GitLab

1. Initialize git in your local project folder (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Prepare Gen AI Platform for Render deployment"
   ```
2. Create a repository on [GitHub](https://github.com/new).
3. Push your repository:
   ```bash
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git branch -M main
   git push -u origin main
   ```
*(Notice: `.env` and `venv/` are excluded by `.gitignore` and will never be committed).*

---

## 🌐 Step 3: Create Web Service on Render

1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** in the top navigation and select **Web Service**.
3. Select **Build and deploy from a Git repository** and connect your GitHub/GitLab repository.
4. Configure the service settings:
   - **Name:** `genai-content-transformation` (or your preferred name)
   - **Region:** Closest to your users / database
   - **Branch:** `main`
   - **Root Directory:** *(leave blank if repository root contains app.py)*
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     gunicorn app:app
     ```
   - **Instance Type:** `Free` (or Starter / Standard)

---

## 🔑 Step 4: Configure Environment Variables on Render

In the **Environment** tab of your Render Web Service, add the following variables:

| Environment Variable | Value / Description | Example |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | Python runtime version | `3.11.9` |
| `SECRET_KEY` | Long random key for session security | *(e.g. 64-char random string)* |
| `MONGO_URI` | Persistent MongoDB Atlas connection string | `mongodb+srv://appuser:SecretPass123@cluster0.abc.mongodb.net/?retryWrites=true&w=majority` |
| `MONGO_DB` | Database name | `genai_content_transformation` |
| `GEMINI_API_KEY` | Google Gemini API Key | `AIzaSy...` (from Google AI Studio) |
| `GEMINI_MODEL` | *(Optional)* Default Gemini model | `gemini-2.5-flash` |
| `OPENAI_API_KEY` | *(Optional)* OpenAI API Key | `sk-proj-...` (from OpenAI) |
| `OPENAI_MODEL` | *(Optional)* Default OpenAI model | `gpt-4o-mini` |
| `FLASK_DEBUG` | Production debug flag | `false` |

*(Note: Render automatically sets the `PORT` variable. Gunicorn will automatically bind to the port assigned by Render).*

---

## 🔍 Step 5: Verify Deployment

1. Click **Create Web Service** (or **Manual Deploy > Deploy Latest Commit**).
2. Monitor the Render deployment logs. You should see:
   ```
   ==> Installing dependencies with pip...
   ==> Successfully installed Flask gunicorn pymongo dnspython certifi ...
   ==> Running 'gunicorn app:app'
   [INFO] Starting gunicorn 21.2.0
   [INFO] Listening at: http://0.0.0.0:10000
   ==> Your service is live 🎉
   ```
3. Click your Render service URL (e.g. `https://genai-content-transformation.onrender.com`).
4. Test:
   - Create a user account (`/register`).
   - Log in (`/login`).
   - View Dashboard (`/dashboard`).
   - Run a test transformation in Studio (`/studio`).
   - Verify that your transformation is saved to History (`/history`).
   - Test PDF / Word / PPTX download.
   - Check health endpoint: `https://your-service.onrender.com/api/health`

---

## 🛠️ Troubleshooting Common Render Issues

### 1. MongoDB Atlas Connection Timeout
- **Symptom:** App falls back to local storage or shows `ServerSelectionTimeoutError`.
- **Fix:** In MongoDB Atlas, go to **Network Access** and ensure `0.0.0.0/0` (Allow access from anywhere) is added and active. Ensure your database user password has no unencoded special characters.

### 2. Port Binding / Web Service Did Not Become Healthy
- **Symptom:** Render displays `Timed out waiting for port to become open`.
- **Fix:** Render requires Gunicorn to bind to `0.0.0.0:$PORT`.
  The command `gunicorn app:app` automatically reads `$PORT` on Render. Alternatively, specify:
  ```bash
  gunicorn --bind 0.0.0.0:$PORT app:app
  ```

### 3. Missing Dependencies During Build
- **Symptom:** `ModuleNotFoundError` in runtime logs.
- **Fix:** Ensure `pip install -r requirements.txt` runs in the Build Command and that `requirements.txt` includes `gunicorn>=21.2.0`, `dnspython`, and `certifi`.
