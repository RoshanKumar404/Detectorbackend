# 🚀 Detector Backend Production Deployment Guide (Render)

This guide shows you step-by-step how to host your Flask backend and PostgreSQL database for free on **Render**.

---

## 📦 Prerequisites

Your repository is fully pre-configured for production:
* `Procfile`: Configured to run the Gunicorn WSGI production server (`web: gunicorn run:app`).
* `requirements.txt`: Includes all dependencies and `gunicorn`.

---

## 🛠️ Step 1: Create a PostgreSQL Database on Render

1. Go to [Render Dashboard](https://dashboard.render.com/) and log in (or sign up with your GitHub account).
2. Click **New +** (top right) and select **PostgreSQL**.
3. Fill in the details:
   * **Name**: `detector-db`
   * **Database Name**: `detector`
   * **User**: `roshan`
   * **Region**: Choose the closest region (e.g., `Singapore` or `Oregon`).
4. Scroll down and choose the **Free** instance type.
5. Click **Create Database**.
6. Once the database status is **Active**, copy the **Internal Database URL** (for Render services) or **External Database URL** (for local testing). It will look like:
   `postgresql://roshan:password@host.render.com/detector`

---

## 🌐 Step 2: Create a Web Service on Render

1. On the Render Dashboard, click **New +** and select **Web Service**.
2. Connect your GitHub account and select your repository: `Detectorbackend`.
3. Configure the service:
   * **Name**: `detector-backend`
   * **Region**: Same region as your database.
   * **Branch**: `master`
   * **Root Directory**: Leave blank.
   * **Language**: `Python 3`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `gunicorn run:app`
4. Choose the **Free** instance type.
5. Click **Advanced** to add environment variables.

---

## ⚙️ Step 3: Add Environment Variables

In the **Environment Variables** section on Render, add the following keys:

| Key | Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | *Paste your PostgreSQL Internal Database URL here* | Render database connection string |
| `JWT_SECRET_KEY` | `your-secret-key-here` | Random string for token encryption |
| `CLOUDINARY_URL` | *Paste your Cloudinary environment URL here* | For citizen report image storage |
| `PYTHON_VERSION` | `3.11.0` (or similar) | Sets the python runtime version |

Click **Create Web Service**. Render will now automatically pull your code, install dependencies, and spin up your live server!

---

## 🗃️ Step 4: Run Migrations and Seed Data

Once your Web Service is successfully built and deployed, you need to initialize the PostgreSQL database schema and seed the Jharkhand municipalities.

1. On your Render Web Service page, click the **Shell** tab (left sidebar).
2. Run the database migration upgrade:
   ```bash
   flask db upgrade
   ```
3. Run the Jharkhand municipalities seeding script:
   ```bash
   python seed.py
   ```

**🎉 Congratulations! Your backend is now hosted and live!** You can use the provided Render URL (e.g., `https://detector-backend.onrender.com`) in your React Native app and Admin Dashboard!
