# File: mock_tank.py (TANK SIMULATOR FOR LAPTOP TESTING)
import socket
import sys

# Network configuration (identical to the robot's server settings)
HOST = '127.0.0.1'  # Localhost IP address of your laptop
PORT = 65432        # Safe port designated for communication

print("==================================================")
print("       THEO TANK SIMULATOR (TESTING VERSION)      ")
print("==================================================")

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Allow the system to reuse the port instantly without waiting timeouts
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        s.bind((HOST, PORT))
        s.listen()
        
        print(f"[*] Simulator successfully started on {HOST}:{PORT}")
        print("[*] Awaiting incoming connection from voice_control.py...\n")
        
        conn, addr = s.accept()
        with conn:
            print(f"[+] CONNECTION ESTABLISHED! Voice client connected (Client Address: {addr})")
            print("[*] You can now speak into the microphone to send commands.\n")
            print("-" * 50)
            
            while True:
                data = conn.recv(1024)
                if not data:
                    print("\n[-] Voice control application disconnected or connection lost.")
                    print("[*] Shutting down the simulator.")
                    break
                    
                # Decode the incoming byte command stream from the laptop's mic client
                command_received = data.decode('utf-8')
                
                # Print the raw data payload directly to the console
                print(f"[DATA RECEIVED FROM MIC] ---> {command_received}")
                
                # Visual protocol parsing demonstration for thesis documentation
                if '|' in command_received:
                    cmd, duration = command_received.split('|')
                    print(f"   L--> Decoded System Command: {cmd}")
                    print(f"   L--> Action Duration: {duration} seconds\n")

except KeyboardInterrupt:
    print("\n[-] Simulator forcefully stopped by user (Ctrl+C).")
except Exception as e:
    print(f"\n[Simulator Critical Error]: {e}")
