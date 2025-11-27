# Telegram Bot Setup

Your Telegram bot is already configured! ✅

## Your Configuration (from .env)
- **Bot Token**: `8492926684:AAGKa_ra9YWZCBrA0axnVMzybGC2Ze2K96A`
- **Chat ID**: `6803602128`

## Features
- 🚨 Automatic notification when room reaches maximum capacity
- ✅ Notification when capacity returns to normal (< 90%)
- ⏰ 5-minute cooldown between repeated alerts
- 🧪 Test button in dashboard sidebar

## Notifications You'll Receive

### Capacity Alert
```
🚨 ROOM AT MAXIMUM CAPACITY!

👥 Currently Inside: 5/5
🚪 Total Entries: 15
🚶 Total Exits: 10
📊 Capacity: 100%

⏰ Time: 2025-11-26 15:30:45
```

### Back to Normal
```
✅ Room Capacity Back to Normal

👥 Currently Inside: 4/5
📊 Capacity: 80%

⏰ Time: 2025-11-26 15:35:20
```

## Testing
1. Open the Streamlit dashboard
2. Go to the sidebar under "📱 Telegram Notifications"
3. Click "🧪 Test Notification" button
4. Check your Telegram for the test message

## How It Works
- Notifications are sent automatically when the "Currently Inside" count reaches the "Max Capacity"
- A second notification is sent (silently) when the room drops below 90% capacity
- 5-minute cooldown prevents spam if people keep entering at capacity

## Troubleshooting
- If notifications don't work, check that your `.env` file has the correct values
- Make sure you've started a chat with your bot on Telegram
- Click the test button to verify the connection
