from machine import Pin
import time

# Simple distance simulation for Wokwi
class UltrasonicSensor:
    """Simplified ultrasonic sensor for Wokwi"""
    
    def __init__(self, trigger_pin, echo_pin, name="Sensor"):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
        self.name = name
        self.trigger.value(0)
        print(f"+ {name} initialized (Trigger: GPIO{trigger_pin}, Echo: GPIO{echo_pin})")
    
    def measure(self):
        """
        Measure distance using ultrasonic sensor
        Returns distance in cm
        """
        # Send trigger pulse
        self.trigger.value(0)
        time.sleep_us(2)
        self.trigger.value(1)
        time.sleep_us(10)
        self.trigger.value(0)
        
        # Wait for echo to start
        timeout = 30000  # 30ms timeout
        start = time.ticks_us()
        
        while self.echo.value() == 0:
            if time.ticks_diff(time.ticks_us(), start) > timeout:
                return 400  # Return max distance on timeout
        
        # Measure echo pulse
        pulse_start = time.ticks_us()
        
        while self.echo.value() == 1:
            if time.ticks_diff(time.ticks_us(), pulse_start) > timeout:
                return 400
        
        pulse_end = time.ticks_us()
        pulse_duration = time.ticks_diff(pulse_end, pulse_start)
        
        # Calculate distance: duration * speed of sound / 2
        # Speed of sound = 343 m/s = 0.0343 cm/μs
        distance = (pulse_duration * 0.0343) / 2
        
        return distance


class PeopleCounter:
    """People counting system for Wokwi"""
    
    def __init__(self):
        print("\n" + "="*45)
        print("   ULTRASONIC PEOPLE COUNTER")
        print("   Wokwi Simulator Version")
        print("="*45)
        print("\nInitializing system...")
        
        # Create sensors
        self.entry_sensor = UltrasonicSensor(5, 18, "Entry")
        self.exit_sensor = UltrasonicSensor(23, 19, "Exit")
        
        # Create LEDs
        try:
            self.led_entry = Pin(2, Pin.OUT)
            self.led_exit = Pin(4, Pin.OUT)
            self.led_entry.value(0)
            self.led_exit.value(0)
            print("+ LEDs initialized (Entry: GPIO2, Exit: GPIO4)")
        except:
            print("! LED initialization skipped")
            self.led_entry = None
            self.led_exit = None
        
        # Settings
        self.threshold = 100  # Detection distance in cm
        self.cooldown = 2.0   # Seconds between detections
        self.max_capacity = 50  # Maximum room capacity
        self.mass_event_window = 3.0  # Time window for mass event detection (seconds)
        self.mass_event_threshold = 3  # Minimum people for mass event
        
        # Counters
        self.entries = 0
        self.exits = 0
        self.inside = 0
        
        # Timing
        self.last_entry_time = 0
        self.last_exit_time = 0
        
        # Mass event tracking
        self.recent_entries = []  # List of entry timestamps
        self.recent_exits = []  # List of exit timestamps
        
        # Alert state
        self.room_occupied_alert_active = False
        
        print(f"+ Threshold: {self.threshold}cm")
        print(f"+ Cooldown: {self.cooldown}s")
        print(f"+ Max Capacity: {self.max_capacity} people")
        print(f"+ Mass Event Threshold: {self.mass_event_threshold} people in {self.mass_event_window}s")
        print("\n" + "="*45)
        print("System Ready! Monitoring started...")
        print("="*45 + "\n")
    
    def blink_led(self, led):
        """Blink an LED"""
        if led:
            led.value(1)
            time.sleep(0.2)
            led.value(0)
    
    def alert_led_pattern(self, led):
        """Alert LED pattern for warnings"""
        if led:
            for _ in range(3):
                led.value(1)
                time.sleep(0.1)
                led.value(0)
                time.sleep(0.1)
    
    def get_time_str(self):
        """Get formatted time string"""
        secs = time.time()
        mins = int(secs / 60)
        hrs = int(mins / 60)
        secs = int(secs % 60)
        mins = mins % 60
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    
    def clean_old_events(self, event_list):
        """Remove events outside the time window"""
        current_time = time.time()
        cutoff_time = current_time - self.mass_event_window
        # Keep only events within the time window
        return [t for t in event_list if t > cutoff_time]
    
    def check_mass_event(self, event_list, event_type):
        """Check if a mass event is occurring"""
        if len(event_list) >= self.mass_event_threshold:
            print("\n" + "!"*45)
            print(f"   ALERT: MASS {event_type.upper()} DETECTED!")
            print(f"   {len(event_list)} people {event_type} in {self.mass_event_window}s")
            print("   Current occupancy: {} people".format(self.inside))
            print("!"*45 + "\n")
            return True
        return False
    
    def check_capacity(self):
        """Check if room capacity is exceeded"""
        if self.inside >= self.max_capacity:
            if not self.room_occupied_alert_active:
                print("\n" + "!"*45)
                print("   ALERT: ROOM AT MAXIMUM CAPACITY!")
                print(f"   Current: {self.inside}/{self.max_capacity} people")
                print("   No more entries allowed - Room Occupied")
                print("!"*45 + "\n")
                self.room_occupied_alert_active = True
                # Flash both LEDs as warning
                self.alert_led_pattern(self.led_entry)
                self.alert_led_pattern(self.led_exit)
            return True
        else:
            if self.room_occupied_alert_active:
                print("\n" + "="*45)
                print("   Room capacity back to normal")
                print(f"   Current: {self.inside}/{self.max_capacity} people")
                print("="*45 + "\n")
                self.room_occupied_alert_active = False
            return False
    
    def check_entry(self):
        """Check entry sensor"""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_entry_time < self.cooldown:
            return False
        
        # Measure distance
        distance = self.entry_sensor.measure()
        
        # Check if person detected (close distance)
        if distance < self.threshold and distance > 2:
            # Check if room is at capacity
            if self.inside >= self.max_capacity:
                print(f"[{self.get_time_str()}] >> ENTRY BLOCKED - ROOM AT CAPACITY")
                print(f"    Current: {self.inside}/{self.max_capacity} people")
                print(f"    Entry denied for safety\n")
                self.alert_led_pattern(self.led_entry)
                self.last_entry_time = current_time
                return False
            
            self.entries += 1
            self.inside += 1
            self.last_entry_time = current_time
            
            # Track for mass event detection
            self.recent_entries.append(current_time)
            self.recent_entries = self.clean_old_events(self.recent_entries)
            
            # Visual feedback
            self.blink_led(self.led_entry)
            
            # Print detection
            print(f"[{self.get_time_str()}] >> PERSON ENTERED")
            print(f"    Distance: {distance:.1f} cm")
            print(f"    Total Inside: {self.inside}/{self.max_capacity}")
            
            # Check for mass entry event
            if self.check_mass_event(self.recent_entries, "entry"):
                pass  # Alert already printed in check_mass_event
            
            # Check capacity
            self.check_capacity()
            
            print()
            
            return True
        
        return False
    
    def check_exit(self):
        """Check exit sensor"""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_exit_time < self.cooldown:
            return False
        
        # Measure distance
        distance = self.exit_sensor.measure()
        
        # Check if person detected
        if distance < self.threshold and distance > 2:
            # Only process exit if there are people inside
            if self.inside <= 0:
                print(f"[{self.get_time_str()}] << EXIT IGNORED - Room is empty")
                self.last_exit_time = current_time
                return False
            
            self.exits += 1
            self.inside -= 1
            self.last_exit_time = current_time
            
            # Track for mass event detection
            self.recent_exits.append(current_time)
            self.recent_exits = self.clean_old_events(self.recent_exits)
            
            # Visual feedback
            self.blink_led(self.led_exit)
            
            # Print detection
            print(f"[{self.get_time_str()}] << PERSON EXITED")
            print(f"    Distance: {distance:.1f} cm")
            print(f"    Total Inside: {self.inside}/{self.max_capacity}")
            
            # Check for mass exit event
            if self.check_mass_event(self.recent_exits, "exit"):
                pass  # Alert already printed in check_mass_event
            
            # Check if capacity normalized
            self.check_capacity()
            
            print()
            
            return True
        
        return False
    
    def show_stats(self):
        """Display statistics"""
        print("\n" + "="*45)
        print("         STATISTICS")
        print("="*45)
        print(f"  Total Entries:     {self.entries:4d}")
        print(f"  Total Exits:       {self.exits:4d}")
        print(f"  Currently Inside:  {self.inside:4d} / {self.max_capacity}")
        capacity_percent = (self.inside / self.max_capacity) * 100
        print(f"  Capacity Usage:    {capacity_percent:5.1f}%")
        if self.inside >= self.max_capacity:
            print("  Status:            ROOM OCCUPIED")
        elif self.inside >= self.max_capacity * 0.8:
            print("  Status:            NEAR CAPACITY")
        else:
            print("  Status:            NORMAL")
        print("="*45 + "\n")
    
    def run(self):
        """Main loop"""
        print("Monitoring for people...")
        print("   (In Wokwi: Click sensors to change distance)")
        print("   (Press Stop button to end)\n")
        
        last_stats = time.time()
        stats_interval = 15  # Show stats every 15 seconds
        
        loop_count = 0
        
        try:
            while True:
                # Clean old events periodically
                if loop_count % 100 == 0:
                    self.recent_entries = self.clean_old_events(self.recent_entries)
                    self.recent_exits = self.clean_old_events(self.recent_exits)
                
                # Check both sensors
                self.check_entry()
                self.check_exit()
                
                # Periodic stats
                current = time.time()
                if current - last_stats >= stats_interval:
                    self.show_stats()
                    last_stats = current
                
                # Small delay
                time.sleep(0.1)
                
                # Progress indicator every 50 loops
                loop_count += 1
                if loop_count % 50 == 0:
                    print(".", end="")
                if loop_count % 500 == 0:
                    print(" [Running]")
        
        except KeyboardInterrupt:
            print("\n\n" + "="*45)
            print("   SYSTEM STOPPED")
            print("="*45)
            self.show_stats()
            print("Thank you for using People Counter!")
        
        except Exception as e:
            print(f"\n! Error: {e}")
            self.show_stats()


# Auto-start when uploaded to Wokwi
print("\nStarting People Counter System...")
print("="*45)

counter = PeopleCounter()
counter.run()
