"""
Simple script to upload code to ESP32 via serial
"""
import serial
import time

def upload_file(port, filename, target_name="/main.py"):
    """Upload a file to ESP32"""
    print(f"Connecting to {port}...")
    
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        time.sleep(2)
        
        print("Connected! Reading file...")
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()
        
        print(f"Uploading {filename} to ESP32 as {target_name}...")
        print("This may take a moment...\n")
        
        # Enter raw REPL mode
        ser.write(b'\r\x03\x03')  # Ctrl-C twice
        time.sleep(0.1)
        ser.write(b'\r\x01')  # Ctrl-A for raw REPL
        time.sleep(0.5)
        
        # Clear any output
        ser.read(ser.in_waiting)
        
        # Create file writing command
        file_cmd = f"""
f = open('{target_name}', 'w')
f.write({repr(code)})
f.close()
print('File uploaded successfully!')
"""
        
        # Send command
        ser.write(file_cmd.encode('utf-8'))
        ser.write(b'\r\x04')  # Ctrl-D to execute
        time.sleep(1)
        
        # Read response
        response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        
        if 'File uploaded successfully!' in response:
            print("✓ Upload successful!")
            print(f"✓ {filename} uploaded to ESP32 as {target_name}")
            print("\nResetting ESP32...")
            
            # Soft reset
            ser.write(b'\r\x03\x03')  # Ctrl-C
            time.sleep(0.1)
            ser.write(b'\r\x04')  # Ctrl-D (soft reset)
            time.sleep(1)
            
            print("✓ ESP32 reset complete!")
            print("\nYour code should now be running on the ESP32.")
            print("Check the serial monitor or dashboard for output.")
        else:
            print("⚠ Upload may have issues. Response:")
            print(response)
        
        ser.close()
        return True
        
    except serial.SerialException as e:
        print(f"✗ Error: {e}")
        print(f"\nMake sure:")
        print(f"  1. ESP32 is connected to {port}")
        print(f"  2. No other program is using the serial port")
        print(f"  3. ESP32 has MicroPython firmware installed")
        return False
    except FileNotFoundError:
        print(f"✗ Error: File '{filename}' not found!")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    # Default values
    port = "COM3"
    filename = "main_with_json.py"
    
    # Check command line arguments
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    if len(sys.argv) > 2:
        port = sys.argv[2]
    
    print("="*50)
    print("ESP32 Code Uploader")
    print("="*50)
    print(f"File to upload: {filename}")
    print(f"Target port: {port}")
    print(f"Baud rate: 115200")
    print("="*50 + "\n")
    
    success = upload_file(port, filename)
    
    if success:
        print("\n" + "="*50)
        print("✓ UPLOAD COMPLETE!")
        print("="*50)
        print("\nNext steps:")
        print("1. Open your Streamlit dashboard (should already be running)")
        print("2. Select 'Real Device (Serial)' mode in sidebar")
        print("3. Enter COM3 and click Connect")
        print("4. Test your sensors by passing your hand in front of them")
        print("\nHappy counting! 🎉")
    else:
        print("\n" + "="*50)
        print("✗ UPLOAD FAILED")
        print("="*50)
        print("\nTroubleshooting:")
        print("1. Check if MicroPython is installed on ESP32")
        print("2. Try uploading firmware first:")
        print("   - Download: https://micropython.org/download/ESP32_GENERIC/")
        print("   - Flash with: esptool --port COM3 erase_flash")
        print("   - Flash with: esptool --port COM3 write_flash -z 0x1000 firmware.bin")
