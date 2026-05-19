# File: voice_server.py (RUN ON RASPBERRY PI)
import socket
import time
import threading

# Import hardware control modules
from motor import tankMotor
from servo import Servo
from led import Led

# Initialize hardware safely
try:
    PWM = tankMotor()
    servo = Servo()
    led = Led()
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize robot hardware. {e}")
    exit(1)

# Base angles for claw/manipulator (as requested: both starting at 150 degrees)
# Servo 0 = Lift mechanism (Top), Servo 1 = Grip/Claw mechanism (Bottom)
claw_lift_angle = 150
claw_grip_angle = 150

# Network settings
HOST = 'raspberrypi.local'  # Local hostname
PORT = 65432      

# --- SAFETY FUNCTIONS ---
def safe_servo(port, angle):
    """Safe servo control with strict limits (30-150 degrees) to prevent mechanical damage."""
    safe_angle = max(30, min(150, int(angle))) # Clamp value between 30 and 150
    servo.setServoPwm(str(port), safe_angle)

def safe_motor_run(left_speed, right_speed, duration):
    """Safe motor execution. Guarantees motors will stop even if an error occurs."""
    safe_duration = min(float(duration), 10.0) # Safety limit: max 10 seconds of movement
    try:
        PWM.setMotorModel(left_speed, right_speed)
        time.sleep(safe_duration)
    finally:
        # This block ALWAYS executes, stopping the motors
        PWM.setMotorModel(0, 0)

# --- MAIN LOGIC ---
def execute_command(command_str):
    global claw_lift_angle, claw_grip_angle
    
    # Input validation (protection against corrupted network data)
    if not command_str or '|' not in command_str:
        return
        
    parts = command_str.split('|')
    cmd = parts[0].strip()
    
    try:
        duration = float(parts[1]) if len(parts) > 1 else 1.0
    except ValueError:
        duration = 1.0 # Default to 1 second if an invalid number is received

    print(f"Received command: {cmd}, duration: {duration} sec")

    # --- Movement ---
    if cmd == 'FORWARD': safe_motor_run(2000, 2000, duration)
    elif cmd == 'BACKWARD': safe_motor_run(-2000, -2000, duration)
    elif cmd == 'LEFT': safe_motor_run(-2000, 2000, duration)
    elif cmd == 'RIGHT': safe_motor_run(2000, -2000, duration)
    elif cmd == 'CIRCLE': safe_motor_run(2500, 800, duration)
    elif cmd == 'STOP': PWM.setMotorModel(0, 0)
    
    # --- LEDs ---
    elif cmd == 'LIGHT_ON': led.colorWipe((255, 255, 255))
    elif cmd == 'LIGHT_OFF': led.colorWipe((0, 0, 0))
    elif cmd == 'RAINBOW': 
        for _ in range(3): led.rainbow()
        
    # --- Claw Movement (Port 0 = Lift/Top, Port 1 = Grip/Bottom) ---
    elif cmd == 'CLAW_DOWN':
        claw_lift_angle = 50  # Lowering the arm down
        safe_servo('0', claw_lift_angle)
    elif cmd == 'CLAW_UP':
        claw_lift_angle = 150 # Returning to base top position
        safe_servo('0', claw_lift_angle)
    elif cmd == 'CLAW_OPEN':
        claw_grip_angle = 60  # Opening the pincers
        safe_servo('1', claw_grip_angle)
    elif cmd == 'CLAW_CLOSE':
        claw_grip_angle = 150 # Closing the pincers (base state)
        safe_servo('1', claw_grip_angle)
        
    # --- New & Adjusted Protocol: Grab Ball ---
    elif cmd == 'GRAB_BALL':
        # Step 1: Prepare the claw (Open pincers and lower the arm)
        safe_servo('1', 60); time.sleep(0.4)   # Open grip to 60 degrees
        safe_servo('0', 50); time.sleep(0.5)   # Lower arm to 50 degrees
        
        # Step 2: Drive forward slowly to get the ball inside the claw
        safe_motor_run(1200, 1200, 0.8)       # Move forward for 0.8 seconds
        time.sleep(0.2)                        # Short stabilization pause
        
        # Step 3: Secure the ball and lift it up to safety
        safe_servo('1', 150); time.sleep(0.6)  # Close grip back to 150 degrees (secure ball)
        safe_servo('0', 150)                   # Lift arm back to 150 degrees (base position)
        
        # Update global state tracking variables
        claw_lift_angle, claw_grip_angle = 150, 150

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow quick port reuse
        
        try:
            s.bind((HOST, PORT))
        except socket.gaierror:
            print(f"Could not bind to '{HOST}'. Falling back to '0.0.0.0'")
            s.bind(('0.0.0.0', PORT))
            
        s.listen()
        print(f"Safe Theo server started! Waiting for connection...")
        
        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    print(f"Client connected: {addr}")
                    while True:
                        data = conn.recv(1024)
                        if not data: break
                        command = data.decode('utf-8')
                        threading.Thread(target=execute_command, args=(command,), daemon=True).start()
            except Exception as e:
                print(f"Connection error: {e}")

if __name__ == "__main__":
    try:
        # Set both servos to their safe base positions (150 degrees) on startup
        safe_servo('0', 150)
        safe_servo('1', 150)
        start_server()
    except KeyboardInterrupt:
        print("\nShutdown signal detected. Stopping systems...")
    finally:
        print("Turning off motors and lights...")
        try:
            PWM.setMotorModel(0, 0)
            led.colorWipe((0, 0, 0))
        except:
            pass
        print("Server safely stopped.")
