# Deploying to Streamlit Cloud

## Step-by-Step Deployment Guide

### 1. Go to Streamlit Cloud
Visit: https://share.streamlit.io/

### 2. Sign in with GitHub
- Click "Sign in with GitHub"
- Authorize Streamlit to access your repositories

### 3. Deploy Your App
- Click "New app"
- Select your repository: `ummamah/person_counter`
- Main file path: `streamlit_dashboard.py`
- Branch: `main`

### 4. Configure Secrets (Important!)
Before clicking "Deploy", add your Telegram credentials:

1. Click on "Advanced settings"
2. In the "Secrets" section, paste this:

```toml
TELEGRAM_BOT_TOKEN = "8492926684:AAGKa_ra9YWZCBrA0axnVMzybGC2Ze2K96A"
TELEGRAM_CHAT_ID = "6803602128"
```

3. Click "Save"

### 5. Click "Deploy"!

Your app will be live at: `https://<your-app-name>.streamlit.app`

---

## What Gets Deployed

✅ **Files that will be deployed:**
- `streamlit_dashboard.py` - Main dashboard
- `main.py` - ESP32 code (for reference)
- `main_with_json.py` - ESP32 code with JSON
- `requirements.txt` - Python dependencies
- `README.md` - Documentation
- `diagram.json` - Circuit diagram

❌ **Files that won't be deployed:**
- `.env` - Protected by .gitignore
- `__pycache__/` - Temporary files
- `.streamlit/secrets.toml` - Local only

---

## Important Notes

### Simulation Mode Only
Since you won't have the ESP32 connected to Streamlit Cloud, the dashboard will run in **Simulation Mode** only:
- Use the "Simulate Entry" and "Simulate Exit" buttons
- Telegram notifications will still work!
- Perfect for testing and demonstrations

### ESP32 Connection
To use the real device:
- Run the dashboard locally: `streamlit run streamlit_dashboard.py`
- Connect your ESP32 via USB
- Select "Real Device (Serial)" mode

---

## After Deployment

### Testing Telegram Notifications
1. Open your deployed app
2. Set Max Capacity to 5
3. Click "Simulate Entry" 5 times
4. Check your Telegram - you should get an alert! 🎉

### Sharing Your App
Your app URL will be: `https://person-counter-<random>.streamlit.app`
- Share this with anyone
- No authentication required
- Free hosting!

---

## Troubleshooting

**Telegram not working?**
- Check secrets are entered correctly in Streamlit Cloud settings
- No quotes needed around the values in secrets
- Format: `KEY = "value"` not `KEY=value`

**App won't start?**
- Check the logs in Streamlit Cloud dashboard
- Make sure `requirements.txt` has all dependencies

**Need to update secrets?**
- Go to your app settings in Streamlit Cloud
- Click "Secrets" 
- Edit and save
- App will automatically restart
