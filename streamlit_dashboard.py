import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json
import random
import threading
import serial
import serial.tools.list_ports
import re
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Telegram Bot Configuration - works locally and on Streamlit Cloud
try:
    # Try Streamlit secrets first (for cloud deployment)
    TELEGRAM_BOT_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID")
except:
    # Fall back to .env file (for local development)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

# Page configuration
st.set_page_config(
    page_title="Occupancy Sense - People Counter",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .big-font {
        font-size: 50px !important;
        font-weight: bold;
        text-align: center;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .alert-box {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        font-weight: bold;
        text-align: center;
        font-size: 20px;
    }
    .alert-danger {
        background-color: #ff4444;
        color: white;
        animation: blink 1s infinite;
    }
    .alert-warning {
        background-color: #ffaa00;
        color: white;
    }
    .alert-success {
        background-color: #00C851;
        color: white;
    }
    @keyframes blink {
        0%, 50%, 100% { opacity: 1; }
        25%, 75% { opacity: 0.5; }
    }
    .buzzer {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        margin: 20px auto;
        animation: buzz 0.5s infinite;
    }
    @keyframes buzz {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    /* Custom scrollbar styling */
    div::-webkit-scrollbar {
        width: 8px;
    }
    div::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    div::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
    }
    div::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'counter_data' not in st.session_state:
    st.session_state.counter_data = {
        'entries': 0,
        'exits': 0,
        'inside': 0,
        'max_capacity': 50,
        'last_event': None,
        'last_event_time': None,
        'history': [],
        'alert_active': False,
        'alert_type': None,
        'alert_message': None
    }

if 'event_log' not in st.session_state:
    st.session_state.event_log = []

if 'time_series' not in st.session_state:
    st.session_state.time_series = pd.DataFrame(columns=['timestamp', 'occupancy'])

if 'serial_connection' not in st.session_state:
    st.session_state.serial_connection = None

if 'serial_connected' not in st.session_state:
    st.session_state.serial_connected = False

if 'last_serial_data' not in st.session_state:
    st.session_state.last_serial_data = None

if 'telegram_notified' not in st.session_state:
    st.session_state.telegram_notified = False

if 'last_telegram_notification' not in st.session_state:
    st.session_state.last_telegram_notification = None


def send_telegram_notification(message, silent=False):
    """Send notification via Telegram bot"""
    if not TELEGRAM_ENABLED:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_notification': silent
        }
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram notification failed: {e}")
        return False


def check_and_notify_capacity(inside, max_capacity, entries, exits):
    """Check capacity and send Telegram notification if needed"""
    current_time = time.time()
    
    # Room is full
    if inside >= max_capacity:
        # Only send notification once per capacity event (with 5 minute cooldown)
        if not st.session_state.telegram_notified or \
           (st.session_state.last_telegram_notification and 
            current_time - st.session_state.last_telegram_notification > 300):
            
            message = (
                f"🚨 <b>ROOM AT MAXIMUM CAPACITY!</b>\n\n"
                f"👥 Currently Inside: <b>{inside}/{max_capacity}</b>\n"
                f"🚪 Total Entries: {entries}\n"
                f"🚶 Total Exits: {exits}\n"
                f"📊 Capacity: <b>{(inside/max_capacity)*100:.0f}%</b>\n\n"
                f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            if send_telegram_notification(message):
                st.session_state.telegram_notified = True
                st.session_state.last_telegram_notification = current_time
                add_event_log("TELEGRAM", "Capacity alert sent via Telegram")
    
    # Room is back to normal
    elif inside < max_capacity * 0.9:  # 90% threshold for "back to normal"
        if st.session_state.telegram_notified:
            message = (
                f"✅ <b>Room Capacity Back to Normal</b>\n\n"
                f"👥 Currently Inside: <b>{inside}/{max_capacity}</b>\n"
                f"📊 Capacity: <b>{(inside/max_capacity)*100:.0f}%</b>\n\n"
                f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            send_telegram_notification(message, silent=True)
            st.session_state.telegram_notified = False
            add_event_log("TELEGRAM", "Normal capacity notification sent")


def parse_serial_line(line):
    """Parse ESP32 serial output for counter data"""
    try:
        # Check for JSON format (main_with_json.py)
        if line.startswith('JSON:'):
            data = json.loads(line[5:])
            return data
        
        # Parse text format (main.py)
        if 'PERSON ENTERED' in line:
            return {'type': 'entry'}
        elif 'PERSON EXITED' in line:
            return {'type': 'exit'}
        elif 'Total Inside:' in line:
            match = re.search(r'Total Inside:\s*(\d+)', line)
            if match:
                return {'type': 'update', 'inside': int(match.group(1))}
        elif 'ROOM AT MAXIMUM CAPACITY' in line or 'ROOM OCCUPIED' in line:
            return {'type': 'alert', 'alert_type': 'capacity', 'alert_message': 'Room at maximum capacity!'}
        elif 'MASS ENTRY DETECTED' in line:
            return {'type': 'alert', 'alert_type': 'mass_entry', 'alert_message': 'Mass entry detected!'}
        elif 'MASS EXIT DETECTED' in line:
            return {'type': 'alert', 'alert_type': 'mass_exit', 'alert_message': 'Mass exit detected!'}
    except Exception as e:
        pass
    return None


def read_serial_data():
    """Read all available data from serial port"""
    events = []
    if st.session_state.serial_connection and st.session_state.serial_connected:
        try:
            # Read all available lines in buffer
            while st.session_state.serial_connection.in_waiting > 0:
                line = st.session_state.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    event = parse_serial_line(line)
                    if event:
                        events.append(event)
                        st.session_state.last_serial_data = event
        except Exception as e:
            st.session_state.serial_connected = False
            return None
    return events if events else None


def play_buzzer_sound(alert_type):
    """Generate buzzer sound based on alert type"""
    if alert_type == "capacity":
        return "🔴🔊 BEEP BEEP BEEP!"
    elif alert_type == "mass_event":
        return "🟡🔊 BEEP BEEP!"
    else:
        return "🟢 ding"


def update_counter_data(entries, exits, inside, alert_type=None, alert_message=None):
    """Update counter data in session state"""
    st.session_state.counter_data['entries'] = entries
    st.session_state.counter_data['exits'] = exits
    st.session_state.counter_data['inside'] = inside
    st.session_state.counter_data['alert_active'] = alert_type is not None
    st.session_state.counter_data['alert_type'] = alert_type
    st.session_state.counter_data['alert_message'] = alert_message
    
    # Check and send Telegram notification if capacity reached
    check_and_notify_capacity(inside, st.session_state.counter_data['max_capacity'], entries, exits)
    
    # Add to time series
    new_row = pd.DataFrame({
        'timestamp': [datetime.now()],
        'occupancy': [inside]
    })
    st.session_state.time_series = pd.concat([st.session_state.time_series, new_row], ignore_index=True)
    
    # Keep only last 100 records
    if len(st.session_state.time_series) > 100:
        st.session_state.time_series = st.session_state.time_series.tail(100)


def add_event_log(event_type, details):
    """Add event to log"""
    event = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'type': event_type,
        'details': details
    }
    st.session_state.event_log.insert(0, event)
    
    # Keep only last 50 events
    if len(st.session_state.event_log) > 50:
        st.session_state.event_log = st.session_state.event_log[:50]


# Main dashboard
st.title("👥 Occupancy Sense - Real-Time People Counter")
st.markdown("---")

# Sidebar for settings and controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    max_capacity = st.number_input(
        "Max Capacity",
        min_value=1,
        max_value=500,
        value=st.session_state.counter_data['max_capacity'],
        step=1
    )
    st.session_state.counter_data['max_capacity'] = max_capacity
    
    st.markdown("---")
    st.header(" Connection Status")
    
    # Simulation mode or real device
    mode = st.radio("Mode", ["Simulation", "Real Device (Serial)"])
    
    if mode == "Simulation":
        st.info("Running in simulation mode")
        if st.button("🎲 Simulate Entry"):
            if st.session_state.counter_data['inside'] < max_capacity:
                st.session_state.counter_data['entries'] += 1
                st.session_state.counter_data['inside'] += 1
                add_event_log("ENTRY", f"Person entered. Inside: {st.session_state.counter_data['inside']}")
                
                # Update time series
                update_counter_data(
                    st.session_state.counter_data['entries'],
                    st.session_state.counter_data['exits'],
                    st.session_state.counter_data['inside']
                )
                
                # Check for alerts
                if st.session_state.counter_data['inside'] >= max_capacity:
                    update_counter_data(
                        st.session_state.counter_data['entries'],
                        st.session_state.counter_data['exits'],
                        st.session_state.counter_data['inside'],
                        "capacity",
                        "🚨 ROOM AT MAXIMUM CAPACITY!"
                    )
                st.rerun()
        
        if st.button("🚶 Simulate Exit"):
            if st.session_state.counter_data['inside'] > 0:
                st.session_state.counter_data['exits'] += 1
                st.session_state.counter_data['inside'] -= 1
                add_event_log("EXIT", f"Person exited. Inside: {st.session_state.counter_data['inside']}")
                
                update_counter_data(
                    st.session_state.counter_data['entries'],
                    st.session_state.counter_data['exits'],
                    st.session_state.counter_data['inside']
                )
                st.rerun()
            else:
                st.warning("Room is already empty!")
                add_event_log("WARNING", "Exit attempted but room is empty")
        
        if st.button("🔄 Reset Counter"):
            st.session_state.counter_data['entries'] = 0
            st.session_state.counter_data['exits'] = 0
            st.session_state.counter_data['inside'] = 0
            st.session_state.counter_data['alert_active'] = False
            st.session_state.event_log = []
            st.session_state.time_series = pd.DataFrame(columns=['timestamp', 'occupancy'])
            add_event_log("SYSTEM", "Counter reset")
            st.rerun()
    else:
        st.info("Connect your ESP32 device")
        
        # List available ports
        try:
            ports = serial.tools.list_ports.comports()
            port_list = [p.device for p in ports]
            if not port_list:
                port_list = ["COM3"]
        except:
            port_list = ["COM3", "COM4", "COM5"]
        
        serial_port = st.selectbox("Serial Port", port_list)
        baud_rate = st.selectbox("Baud Rate", [9600, 115200], index=1)
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🔌 Connect"):
                try:
                    if st.session_state.serial_connection:
                        st.session_state.serial_connection.close()
                    st.session_state.serial_connection = serial.Serial(serial_port, baud_rate, timeout=0.1)
                    st.session_state.serial_connected = True
                    time.sleep(1)  # Wait for connection to stabilize
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to connect: {e}")
        
        with col_btn2:
            if st.button("🔌 Disconnect"):
                if st.session_state.serial_connection:
                    st.session_state.serial_connection.close()
                    st.session_state.serial_connection = None
                st.session_state.serial_connected = False
                st.rerun()
        
        st.markdown("---")
        
        # Show connection status
        if st.session_state.serial_connected:
            st.markdown(f"""
                <div style="background-color: #00C851; color: white; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; margin-top: 10px;">
                    ✓ Connected to {serial_port}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background-color: #666; color: white; padding: 15px; border-radius: 8px; text-align: center; margin-top: 10px;">
                    ✗ Not connected
                </div>
            """, unsafe_allow_html=True)
        
        # Read serial data if connected
        if st.session_state.serial_connected:
            events = read_serial_data()
            if events:
                # Process all events in buffer
                for event in events:
                    event_type = event.get('type')
                    
                    # Handle JSON format data
                    if 'entries' in event and 'exits' in event and 'inside' in event:
                        # ALWAYS calculate inside count from entries - exits (don't trust ESP32's value)
                        entries_val = int(event['entries'])
                        exits_val = int(event['exits'])
                        esp32_inside = int(event['inside'])
                        
                        # Force correct calculation
                        inside_val = max(0, entries_val - exits_val)
                        
                        # Log if ESP32 sent wrong value
                        if esp32_inside != inside_val:
                            add_event_log("WARNING", f"ESP32 sent wrong count! Entries={entries_val}, Exits={exits_val}, ESP32 said Inside={esp32_inside}, Corrected to {inside_val}")
                        
                        st.session_state.counter_data['entries'] = entries_val
                        st.session_state.counter_data['exits'] = exits_val
                        st.session_state.counter_data['inside'] = inside_val
                        
                        # Update time series
                        update_counter_data(
                            entries_val,
                            exits_val,
                            inside_val,
                            event.get('alert_type'),
                            event.get('alert_message')
                        )
                        
                        # Add to event log
                        if event_type == 'entry':
                            add_event_log("ENTRY", f"Person entered. Inside: {inside_val}")
                        elif event_type == 'exit':
                            add_event_log("EXIT", f"Person exited. Inside: {inside_val}")
                        elif event_type in ['capacity_alert', 'mass_event']:
                            add_event_log("ALERT", event.get('alert_message', 'Alert triggered'))
                    
                    # Handle text format data
                    else:
                        if event_type == 'entry':
                            st.session_state.counter_data['entries'] += 1
                            st.session_state.counter_data['inside'] += 1
                            add_event_log("ENTRY", f"Person entered. Inside: {st.session_state.counter_data['inside']}")
                            
                            # Update time series after entry
                            update_counter_data(
                                st.session_state.counter_data['entries'],
                                st.session_state.counter_data['exits'],
                                st.session_state.counter_data['inside']
                            )
                        elif event_type == 'exit':
                            # Only decrement if there are people inside
                            if st.session_state.counter_data['inside'] > 0:
                                st.session_state.counter_data['exits'] += 1
                                st.session_state.counter_data['inside'] -= 1
                                add_event_log("EXIT", f"Person exited. Inside: {st.session_state.counter_data['inside']}")
                                
                                # Update time series after exit
                                update_counter_data(
                                    st.session_state.counter_data['entries'],
                                    st.session_state.counter_data['exits'],
                                    st.session_state.counter_data['inside']
                                )
                            else:
                                # Log false exit detection
                                add_event_log("WARNING", "Exit detected but room is empty - ignored")
                        elif event_type == 'update' and 'inside' in event:
                            # Recalculate inside from counters instead of trusting update
                            calculated_inside = max(0, st.session_state.counter_data['entries'] - st.session_state.counter_data['exits'])
                            st.session_state.counter_data['inside'] = calculated_inside
                            
                            # Log if update value was different
                            update_val = int(event.get('inside', 0))
                            if update_val != calculated_inside:
                                add_event_log("WARNING", f"Update mismatch: Expected {calculated_inside}, got {update_val}")
                            
                            # Update time series
                            update_counter_data(
                                st.session_state.counter_data['entries'],
                                st.session_state.counter_data['exits'],
                                st.session_state.counter_data['inside']
                            )
                        elif event_type == 'alert':
                            update_counter_data(
                                st.session_state.counter_data['entries'],
                                st.session_state.counter_data['exits'],
                                st.session_state.counter_data['inside'],
                                event.get('alert_type'),
                                event.get('alert_message')
                            )
                            add_event_log("ALERT", event.get('alert_message', 'Alert'))                # Trigger immediate refresh after processing events
                st.rerun()
    
    st.markdown("---")
    
    # Universal reset button
    if st.button("🔄 Reset All Counters", key="reset_all"):
        st.session_state.counter_data['entries'] = 0
        st.session_state.counter_data['exits'] = 0
        st.session_state.counter_data['inside'] = 0
        st.session_state.counter_data['alert_active'] = False
        st.session_state.event_log = []
        st.session_state.time_series = pd.DataFrame(columns=['timestamp', 'occupancy'])
        add_event_log("SYSTEM", "All counters reset to zero")
        st.success("✓ Counters reset!")
        st.rerun()
    
    st.markdown("---")
    st.header("📡 Data Source")
    st.info("ESP32 via Serial/HTTP")
    
    st.markdown("---")
    st.header("📱 Telegram Notifications")
    if TELEGRAM_ENABLED:
        st.success("✓ Telegram Bot Connected")
        if TELEGRAM_CHAT_ID:
            st.caption(f"Chat ID: {TELEGRAM_CHAT_ID[:8]}...")
        if st.button("🧪 Test Notification"):
            test_msg = (
                f"🧪 <b>Test Notification</b>\\n\\n"
                f"Your Occupancy Sense bot is working!\\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            if send_telegram_notification(test_msg):
                st.success("Test message sent!")
            else:
                st.error("Failed to send test message")
    else:
        st.warning("⚠️ Telegram Not Configured")
        st.caption("Check your .env file")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto Refresh", value=True)
    if auto_refresh:
        refresh_rate = st.slider("Refresh Rate (seconds)", 0.05, 2.0, 0.1, 0.05)


# Alert Section
if st.session_state.counter_data['alert_active']:
    alert_type = st.session_state.counter_data['alert_type']
    alert_message = st.session_state.counter_data['alert_message']
    
    if alert_type == "capacity":
        st.markdown(f"""
            <div class="alert-box alert-danger">
                🚨 {alert_message}
                <div class="buzzer" style="background-color: #ff4444;"></div>
                <p style="font-size: 30px;">{play_buzzer_sound("capacity")}</p>
            </div>
        """, unsafe_allow_html=True)
    elif alert_type == "mass_event":
        st.markdown(f"""
            <div class="alert-box alert-warning">
                ⚠️ {alert_message}
                <div class="buzzer" style="background-color: #ffaa00;"></div>
                <p style="font-size: 30px;">{play_buzzer_sound("mass_event")}</p>
            </div>
        """, unsafe_allow_html=True)

# Main metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🚪 Total Entries",
        value=st.session_state.counter_data['entries'],
        delta=None
    )

with col2:
    st.metric(
        label="🚶 Total Exits",
        value=st.session_state.counter_data['exits'],
        delta=None
    )

with col3:
    inside = st.session_state.counter_data['inside']
    max_cap = st.session_state.counter_data['max_capacity']
    delta_color = "normal"
    if inside >= max_cap:
        delta_color = "inverse"
    
    st.metric(
        label="👥 Currently Inside",
        value=f"{inside}",
        delta=None
    )

with col4:
    capacity_percent = (inside / max_cap) * 100
    st.metric(
        label="📊 Capacity Usage",
        value=f"{capacity_percent:.1f}%",
        delta=None
    )

st.markdown("---")

# Occupancy gauge
col_gauge, col_status = st.columns([2, 1])

with col_gauge:
    st.subheader("🎯 Occupancy Level")
    
    # Create gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=inside,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "People Inside", 'font': {'size': 24}},
        delta={'reference': max_cap},
        gauge={
            'axis': {'range': [None, max_cap], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, max_cap * 0.5], 'color': '#00C851'},
                {'range': [max_cap * 0.5, max_cap * 0.8], 'color': '#ffaa00'},
                {'range': [max_cap * 0.8, max_cap], 'color': '#ff4444'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_cap
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, width='stretch')

with col_status:
    st.subheader("📋 Status")
    
    if inside >= max_cap:
        st.markdown("""
            <div style="background-color: #ff4444; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                <h2>🔴 ROOM OCCUPIED</h2>
                <p>Maximum capacity reached</p>
            </div>
        """, unsafe_allow_html=True)
    elif inside >= max_cap * 0.8:
        st.markdown("""
            <div style="background-color: #ffaa00; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                <h2>🟡 NEAR CAPACITY</h2>
                <p>Approaching limit</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="background-color: #00C851; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                <h2>🟢 NORMAL</h2>
                <p>Space available</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.metric("Available Space", max_cap - inside)

st.markdown("---")

# Time series chart
col_chart, col_log = st.columns([2, 1])

with col_chart:
    st.subheader("📈 Occupancy Over Time")
    
    if len(st.session_state.time_series) > 0:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=st.session_state.time_series['timestamp'],
            y=st.session_state.time_series['occupancy'],
            mode='lines+markers',
            name='Occupancy',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ))
        
        # Add capacity line
        fig.add_hline(
            y=max_cap,
            line_dash="dash",
            line_color="red",
            annotation_text="Max Capacity",
            annotation_position="right"
        )
        
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Number of People",
            height=300,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No data available yet. Waiting for events...")

with col_log:
    st.subheader("📜 Event Log")
    
    if st.session_state.event_log:
        # Build the complete HTML in one string
        events_container = '<div style="height: 400px; overflow-y: scroll; border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: #1e1e1e;">'
        
        for event in st.session_state.event_log[:20]:
            event_type = event['type']
            icon = "🚪" if event_type == "ENTRY" else "🚶" if event_type == "EXIT" else "⚙️"
            
            if event_type == "ENTRY":
                bg_color = "#00C851"
            elif event_type == "EXIT":
                bg_color = "#ff4444"
            else:
                bg_color = "#666"
            
            events_container += f'<div style="background-color: {bg_color}; color: white; padding: 12px; border-radius: 5px; margin-bottom: 8px; font-family: sans-serif;">'
            events_container += f'<strong>{icon} {event["type"]}</strong><br>'
            events_container += f'<small style="opacity: 0.9;">{event["timestamp"]}</small><br>'
            events_container += f'<span>{event["details"]}</span>'
            events_container += '</div>'
        
        events_container += '</div>'
        
        # Render once
        st.markdown(events_container, unsafe_allow_html=True)
    else:
        st.info("No events logged yet")

st.markdown("---")

# Statistics
st.subheader("📊 Statistics Summary")

col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

with col_stat1:
    # Net movement should always equal current inside count
    net_movement = st.session_state.counter_data['inside']
    st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #333; margin-bottom: 10px;">Net Movement</h3>
            <p style="font-size: 40px; color: #1f77b4; font-weight: bold; margin: 0;">
                {net_movement}
            </p>
        </div>
    """, unsafe_allow_html=True)

with col_stat2:
    if len(st.session_state.time_series) > 0:
        avg_occupancy = st.session_state.time_series['occupancy'].mean()
    else:
        avg_occupancy = 0
    
    st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #333; margin-bottom: 10px;">Avg Occupancy</h3>
            <p style="font-size: 40px; color: #ff7f0e; font-weight: bold; margin: 0;">
                {avg_occupancy:.1f}
            </p>
        </div>
    """, unsafe_allow_html=True)

with col_stat3:
    if len(st.session_state.time_series) > 0:
        peak_occupancy = st.session_state.time_series['occupancy'].max()
    else:
        peak_occupancy = 0
    
    st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #333; margin-bottom: 10px;">Peak Occupancy</h3>
            <p style="font-size: 40px; color: #d62728; font-weight: bold; margin: 0;">
                {int(peak_occupancy)}
            </p>
        </div>
    """, unsafe_allow_html=True)

with col_stat4:
    st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #333; margin-bottom: 10px;">Events Logged</h3>
            <p style="font-size: 40px; color: #2ca02c; font-weight: bold; margin: 0;">
                {len(st.session_state.event_log)}
            </p>
        </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>🔧 Occupancy Sense Dashboard | Powered by Streamlit</p>
        <p>Last updated: {}</p>
    </div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

# Auto-refresh for real-time updates
if auto_refresh and st.session_state.serial_connected:
    # Small delay only when in serial mode to keep checking for data
    time.sleep(refresh_rate)
    st.rerun()
elif auto_refresh:
    # Longer delay in simulation mode
    time.sleep(0.5)
    st.rerun()
