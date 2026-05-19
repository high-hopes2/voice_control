# File: voice_control.py (RUN ON LAPTOP)
import speech_recognition as sr
import socket
import re
import time
import os
from gtts import gTTS
import pygame

# Network configuration
PI_IP = 'raspberrypi.local'  
PORT = 65432

# Initialize audio playback and speech recognizer
pygame.mixer.init()
recognizer = sr.Recognizer()

def connect_to_robot():
    """Establishes a safe connection with timeout handling"""
    print(f"Looking for Theo on the network ({PI_IP})...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0) 
    try:
        s.connect((PI_IP, PORT))
        s.settimeout(None) 
        print("Successfully connected to Theo's systems!")
        return s
    except Exception as e:
        print(f"Cannot find the robot. Ensure it is powered on and connected to Wi-Fi. ({e})")
        return None

robot_socket = connect_to_robot()

def speak(text):
    """Safe text-to-speech execution with temporary file cleanup"""
    print(f"[Theo]: {text}")
    filename = "theo_voice.mp3"
    try:
        tts = gTTS(text=text, lang='uk')
        tts.save(filename)
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy(): 
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"Speaker error: {e}")
    finally:
        pygame.mixer.music.unload()
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

def send_command(cmd, duration=1.0):
    """Sends commands and handles connection loss gracefully"""
    global robot_socket
    if not robot_socket:
        print("Command not sent: No connection to the robot.")
        return

    try:
        message = f"{cmd}|{duration}"
        robot_socket.sendall(message.encode('utf-8'))
    except (BrokenPipeError, ConnectionResetError, OSError):
        print("Connection to the robot lost! Attempting to reconnect...")
        robot_socket = connect_to_robot() 
        if robot_socket:
            try:
                robot_socket.sendall(f"{cmd}|{duration}".encode('utf-8'))
            except:
                pass

def listen_voice():
    """Safe microphone listening with timeout and error handling"""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("\n[ Theo is listening... ]")
        try:
            audio = recognizer.listen(source, timeout=4, phrase_time_limit=6)
            text = recognizer.recognize_google(audio, language="uk-UA")
            print(f"[You said]: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            return "" 
        except sr.UnknownValueError:
            return "" 
        except Exception as e:
            print(f"Recognition error: {e}")
            return ""

def parse_duration(text):
    """Safely extracts the first number found in the string"""
    try:
        numbers = re.findall(r'\d+', text)
        return float(numbers[0]) if numbers else 1.0
    except:
        return 1.0

def run_control_mode():
    speak("Режим керування активовано. Починай команду зі слова Тео.")
    while True:
        phrase = listen_voice()
        if not phrase: continue
            
        if "тео" in phrase:
            cmd = phrase.replace("тео", "").strip()
            duration = parse_duration(cmd)
            
            # --- MOVEMENT ---
            if "вперед" in cmd: speak(f"Їду вперед {duration} сек"); send_command('FORWARD', duration)
            elif "назад" in cmd: speak(f"Відступаю назад {duration} сек"); send_command('BACKWARD', duration)
            elif "вліво" in cmd or "ліворуч" in cmd: speak(f"Повертаю ліворуч {duration} сек"); send_command('LEFT', duration)
            elif "вправо" in cmd or "праворуч" in cmd: speak(f"Повертаю праворуч {duration} сек"); send_command('RIGHT', duration)
            elif "коло" in cmd: speak(f"Описую коло {duration} сек"); send_command('CIRCLE', duration)
            elif "стоп" in cmd or "зупинись" in cmd: speak("Зупиняю двигуни"); send_command('STOP')
            
            # --- LIGHTS ---
            elif "ввімкни світло" in cmd: speak("Вмикаю фари"); send_command('LIGHT_ON')
            elif "вимкни світло" in cmd: speak("Вимикаю фари"); send_command('LIGHT_OFF')
            elif "веселка" in cmd: speak("Запускаю веселку"); send_command('RAINBOW')
            
            # --- CLAW CONTROLS ---
            elif "опусти клешню" in cmd: speak("Опускаю клешню"); send_command('CLAW_DOWN')
            elif "підніми клешню" in cmd: speak("Піднімаю клешню"); send_command('CLAW_UP')
            elif "відкрий" in cmd or "розтисни" in cmd: speak("Розтискаю лещата"); send_command('CLAW_OPEN')
            elif "закрий" in cmd or "стисни" in cmd: speak("Стискаю лещата"); send_command('CLAW_CLOSE')
            elif "візьми" in cmd and "м'яч" in cmd: speak("Запускаю протокол захоплення м'яча"); send_command('GRAB_BALL')
            
            # --- EXIT ---
            elif "вихід" in cmd or "назад" in cmd: speak("Повертаюся в головне меню."); break

def run_chat_mode():
    speak("Режим спілкування! Запитуй мене про мої компоненти. Для виходу скажи: Назад.")
    while True:
        phrase = listen_voice()
        if not phrase: continue
            
        if "назад" in phrase or "вихід" in phrase: speak("Завершую розмову."); break
        
        # --- KNOWLEDGE BASE ---
        elif "хто ти" in phrase or "що за робот" in phrase: speak("Я танк Тео — робототехнічна платформа на базі мікрокомп'ютера Raspberry Pi 5!")
        elif "процесор" in phrase or "cpu" in phrase: speak("У мене всередині потужний 64-бітний чотириядерний процесор Broadcom BCM2712 із частотою 2.4 ГГц.")
        elif "графіка" in phrase or "відеокарта" in phrase: speak("За зображення відповідає відеочип VideoCore VII.")
        elif "чип" in phrase and "rp1" in phrase: speak("Чип RP1 — це власний південний міст від Raspberry Pi, який керує моєю периферією та портами.")
        elif "охолодження" in phrase or "вентилятор" in phrase: speak("На мої чіпи встановлено радіатори, а збоку стоїть вентилятор 30 на 30 міліметрів, який видуває гаряче повітря.")
        elif "врізаєшся" in phrase or "ультразвук" in phrase: speak("Мій ультразвуковий датчик працює як ехолокатор. Якщо перешкода тонка або м'яка, звук не повертається, і я можу врізатися.")
        elif "лінії" in phrase or "сонце" in phrase: speak("Мої інфрачервоні датчики лінії чутливі до сонячного світла, тому на вулиці я можу збиватися з чорної лінії.")
        else: speak("Цікаве питання! Запитай мене краще про процесор, охолодження або мої датчики.")

def main():
    while True:
        speak("Привіт! Бажаєш поспілкуватися чи керувати?")
        choice = listen_voice()
        
        if "спілкуватися" in choice or "поговорити" in choice: run_chat_mode()
        elif "керувати" in choice or "команди" in choice: run_control_mode()
        elif "вимкнись" in choice or "завершити" in choice:
            speak("До побачення, відключаю системи!")
            if robot_socket: 
                try: robot_socket.close()
                except: pass
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram forcefully closed by the user.")
        if robot_socket: robot_socket.close()
