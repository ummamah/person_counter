# 👥 Occupancy Sense - Real-Time People Counter

A real-time people counting system using ESP32 with ultrasonic sensors, featuring a beautiful Streamlit web dashboard with live monitoring and virtual buzzer alerts.

## 🎯 Features

### Hardware (ESP32)
- ✅ Dual ultrasonic sensors (Entry & Exit detection)
- ✅ LED indicators for visual feedback
- ✅ Real-time people counting
- ✅ Maximum capacity enforcement (blocks entries when full)
- ✅ Mass event detection (3+ people in 3 seconds)
- ✅ Cooldown period to prevent false counts
- ✅ JSON output for easy integration

### Web Dashboard (Streamlit)
- 📊 **Real-time monitoring** - Live updates of entries, exits, and current occupancy
- 🎯 **Visual occupancy gauge** - Color-coded capacity indicator
- 📈 **Time series chart** - Track occupancy trends over time
- 🔔 **Virtual buzzer** - Visual and text alerts on the web interface
- 📜 **Event log** - Complete history of all entry/exit events
- 📊 **Statistics** - Average occupancy, peak usage, and more
- 🎨 **Beautiful UI** - Modern, responsive design with animations
- 🔄 **Auto-refresh** - Configurable refresh rate

## 🔧 Hardware Setup

### Components Required
- ESP32 Dev Board
- 2x HC-SR04 Ultrasonic Sensors
- 2x LEDs (Red for Exit, Green for Entry)
- 2x 220Ω Resistors
- Breadboard and jumper wires

### Pin Connections

#### 📋 **Quick Connection Table (Based on 30-Pin ESP32 DevKit)**

| Component | Pin/Terminal | → | ESP32 Pin Label | Physical Location | Notes |
|-----------|-------------|---|-----------------|-------------------|-------|
| **Entry Sensor (HC-SR04 #1)** | | | | | |
| | VCC | → | **3V3** | Top right area | Power (3.3V) |
| | TRIG | → | **D5** (GPIO 5) | Left side, middle | Trigger signal |
| | ECHO | → | **D18** (GPIO 18) | Right side, middle | Echo signal |
| | GND | → | **GND** | Left bottom or right bottom | Ground |
| **Exit Sensor (HC-SR04 #2)** | | | | | |
| | VCC | → | **3V3** | Top right area | Power (3.3V) |
| | TRIG | → | **D23** (GPIO 23) | Right side, top | Trigger signal |
| | ECHO | → | **D19** (GPIO 19) | Right side, upper-middle | Echo signal |
| | GND | → | **GND** | Left bottom or right bottom | Ground |
| **Green LED (Entry Indicator)** | | | | | |
| | Anode (+) | → | **D2** (GPIO 2) | Right side, bottom | Signal pin |
| | Cathode (-) | → | **220Ω Resistor** → **GND** | Any GND pin | Through resistor |
| **Red LED (Exit Indicator)** | | | | | |
| | Anode (+) | → | **D4** (GPIO 4) | Right side, near D2 | Signal pin |
| | Cathode (-) | → | **220Ω Resistor** → **GND** | Any GND pin | Through resistor |

#### 📍 **ESP32 30-Pin Layout Reference**

**LEFT SIDE (Top to Bottom):**
- EN
- VP (GPIO 36)
- VN (GPIO 39)
- D34 (GPIO 34)
- D35 (GPIO 35)
- D32 (GPIO 32)
- D33 (GPIO 33)
- D25 (GPIO 25)
- D26 (GPIO 26)
- D27 (GPIO 27)
- D14 (GPIO 14)
- D12 (GPIO 12)
- D13 (GPIO 13)
- **GND**
- VIN

**RIGHT SIDE (Top to Bottom):**
- D23 (GPIO 23) ← **Exit TRIG**
- D22 (GPIO 22)
- TX0 (GPIO 1)
- RX0 (GPIO 3)
- D21 (GPIO 21)
- **GND**
- D19 (GPIO 19) ← **Exit ECHO**
- D18 (GPIO 18) ← **Entry ECHO**
- D5 (GPIO 5) ← **Entry TRIG**
- TX2 (GPIO 17)
- RX2 (GPIO 16)
- D4 (GPIO 4) ← **Red LED**
- D2 (GPIO 2) ← **Green LED**
- D15 (GPIO 15)
- **3V3** ← **Both Sensors VCC**

#### 🎯 **Wokwi Simulation Note**
For Wokwi simulator (diagram.json), use:
- Exit Sensor TRIG → **D8** instead of D23
- Exit Sensor ECHO → **D9** instead of D19

⚠️ **Pin Mismatch:** Update either diagram.json or main.py to match.

## 💻 Software Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. ESP32 Setup

**For Real Hardware:**
1. Install MicroPython on your ESP32
2. Upload `main.py` or `main_with_json.py` to your ESP32
3. Connect ESP32 via USB to your computer

**For Wokwi Simulator:**
1. Go to https://wokwi.com
2. Upload `main.py` and `diagram.json`
3. Click "Start Simulation"

### 3. Run the Dashboard

**Option 1: Simulation Mode (No Hardware Required)**
```bash
streamlit run streamlit_dashboard.py
```
- Select "Simulation" mode in the sidebar
- Use the buttons to simulate entry/exit events

**Option 2: Real Device Mode**
```bash
streamlit run streamlit_dashboard.py
```
- Select "Real Device (Serial)" mode in the sidebar
- Enter your COM port (e.g., COM3, /dev/ttyUSB0)
- Click "Connect"

### 4. Test Serial Bridge (Optional)

To test the serial connection separately:
```bash
python serial_bridge.py COM3
```
Replace `COM3` with your actual serial port.

## 📱 Using the Dashboard

### Main Features

1. **Live Metrics**
   - Total Entries: Count of people who entered
   - Total Exits: Count of people who left
   - Currently Inside: Real-time occupancy
   - Capacity Usage: Percentage of max capacity

2. **Occupancy Gauge**
   - Green: Normal (0-50% capacity)
   - Yellow: Near capacity (50-80%)
   - Red: At/exceeding capacity (80-100%)

3. **Status Indicators**
   - 🟢 NORMAL: Space available
   - 🟡 NEAR CAPACITY: Approaching limit
   - 🔴 ROOM OCCUPIED: Maximum capacity reached

4. **Virtual Buzzer Alerts**
   - Capacity Alert: Flashing red buzzer when room is full
   - Mass Event Alert: Yellow buzzer for mass entry/exit
   - Visual animation and sound indicators

5. **Event Log**
   - Real-time feed of all entry/exit events
   - Color-coded entries (green) and exits (red)
   - Timestamps for each event

6. **Time Series Chart**
   - Live graph of occupancy over time
   - Red dashed line showing max capacity
   - Hover for detailed information

7. **Statistics Summary**
   - Net Movement: Total entries minus exits
   - Average Occupancy: Mean number of people over time
   - Peak Occupancy: Highest recorded count
   - Events Logged: Total number of tracked events

### Settings (Sidebar)

- **Max Capacity**: Set room capacity limit (1-500)
- **Mode**: Choose between Simulation or Real Device
- **Auto Refresh**: Enable/disable automatic updates
- **Refresh Rate**: Set update frequency (1-10 seconds)

## 🎮 Simulation Mode

Perfect for testing without hardware:

1. Launch dashboard: `streamlit run streamlit_dashboard.py`
2. Select "Simulation" mode in sidebar
3. Click "🎲 Simulate Entry" to add a person
4. Click "🚶 Simulate Exit" to remove a person
5. Click "🔄 Reset Counter" to clear all data

Watch the dashboard update in real-time with animations and alerts!

## 🔌 Real Device Integration

### Using main_with_json.py (Recommended)

This version outputs structured JSON for easier parsing:

```json
{
  "type": "entry",
  "timestamp": 1234567890,
  "entries": 5,
  "exits": 2,
  "inside": 3,
  "max_capacity": 50,
  "capacity_percent": 6.0,
  "distance": 45.2
}
```

### Connecting to Streamlit

The dashboard can automatically parse these JSON messages and update the display.

## 📊 Alert System

### Capacity Alert (🔴 Red Buzzer)
- Triggers when occupancy reaches max capacity
- Blocks further entries for safety
- Continuous flashing red indicator
- "BEEP BEEP BEEP!" sound indicator

### Mass Event Alert (🟡 Yellow Buzzer)
- Triggers when 3+ people enter/exit within 3 seconds
- Useful for detecting rush hours or emergencies
- Pulsing yellow indicator
- "BEEP BEEP!" sound indicator

### Normal Operation (🟢 Green)
- Quiet "ding" sound for individual entries/exits
- LED blinks for visual confirmation

## 🎨 Customization

### Modify Thresholds
Edit in ESP32 code (`main.py`):
```python
self.threshold = 100  # Detection distance (cm)
self.cooldown = 2.0   # Seconds between detections
self.max_capacity = 50  # Maximum people
self.mass_event_threshold = 3  # People for mass event
self.mass_event_window = 3.0  # Time window (seconds)
```

### Customize Dashboard
Edit `streamlit_dashboard.py`:
- Change colors in CSS section
- Modify refresh rates
- Add custom metrics
- Adjust chart styles

## 🐛 Troubleshooting

### Dashboard Issues

**"No module named 'streamlit'"**
```bash
pip install -r requirements.txt
```

**Dashboard not updating**
- Check Auto Refresh is enabled
- Increase refresh rate
- Check serial connection

### ESP32 Issues

**Sensors not detecting**
- Check wiring connections
- Verify 3.3V power supply
- Ensure sensors face the entrance/exit
- Adjust threshold value

**Serial connection failed**
- Check COM port number
- Verify baud rate (115200)
- Install CH340 drivers if needed
- Close other serial monitors

**LEDs not working**
- Check resistor values (220Ω)
- Verify GPIO pins
- Check LED polarity

### Finding Serial Port

**Windows:**
```powershell
Get-WmiObject Win32_SerialPort | Select-Object Name,DeviceID
```

**Linux/Mac:**
```bash
ls /dev/tty*
# or
python -m serial.tools.list_ports
```

## 📈 Future Enhancements

- [ ] Cloud data storage (Firebase/AWS)
- [ ] Mobile app notifications
- [ ] Multiple room support
- [ ] Machine learning for predictions
- [ ] Thermal camera integration
- [ ] Door lock automation
- [ ] QR code check-in system

---
