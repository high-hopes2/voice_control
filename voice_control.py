# File: voice_control.py (RUN ON LAPTOP)
import speech_recognition as sr
import socket
import re
import time
import os
from gtts import gTTS
import pygame
import google.generativeai as genai  # Імпорт бібліотеки штучного інтелекту

# Network configuration
PI_IP = '192.168.1.101' 
PORT = 65432

GEMINI_API_KEY = "AIzaSyAYuH0htYYdBinW7ZNKqDQCiaHNfi7v4ck"

# Initialize Gemini ШІ
try:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction="Ти робот-танк Тео на базі Raspberry Pi 5, створений Людкевич Надією. "
                           "Відповідай коротко (1-3 речення), українською мовою, ввічливо та з легким робо-гумором."
    )
    ai_enabled = True
except Exception as e:
    print(f"Попередження: ШІ не налаштовано або помилка ключа ({e}). Працюватиме стандартна база знань.")
    ai_enabled = False

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
            elif "направо" in cmd or "праворуч" in cmd: speak(f"Повертаю праворуч {duration} сек"); send_command('RIGHT', duration)
            elif "коло" in cmd: speak(f"Описую коло {duration} сек"); send_command('CIRCLE', duration)
            elif "стоп" in cmd or "зупинись" in cmd: speak("Зупиняю двигуни"); send_command('STOP')
            
            # --- LIGHTS ---
            if "увімкни світло" in cmd: speak("Вмикаю світло"); send_command('LIGHT_ON')
            elif "вимкни світло" in cmd or "вимкни веселку" in cmd or "виключи веселку" in cmd: 
                speak("Вимикаю підсвітку"); send_command('LIGHT_OFF')
            elif "веселка" in cmd: speak("Запускаю веселку"); send_command('RAINBOW')
            
            # --- CLAW CONTROLS ---
            elif "опусти клешню" in cmd: speak("Опускаю клешню"); send_command('CLAW_DOWN')
            elif "підніми клешню" in cmd: speak("Піднімаю клешню"); send_command('CLAW_UP')
            elif "відкрий" in cmd or "розтисни" in cmd: speak("Розтискаю лещата"); send_command('CLAW_OPEN')
            elif "закрий" in cmd or "стисни" in cmd: speak("Стискаю лещата"); send_command('CLAW_CLOSE')
            elif "візьми" in cmd and "м'яч" in cmd: speak("Запускаю протокол захоплення м'яча"); send_command('GRAB_BALL')
            
            # --- EXIT ---
            elif "вихід" in cmd: speak("Повертаюся в головне меню."); break

def ask_gemini_ai(question):
    """Звернення до безкоштовного ШІ Gemini, якщо відповіді немає в коді"""
    if not ai_enabled or GEMINI_API_KEY == "AIzaSyAYuH0htYYdBinW7ZNKqDQCiaHNfi7v4ck":
        return "Цікаве питання! Запитай мене краще про мої датчики, режими роботи, плату Raspberry Pi або про мою творчиню Надію."
    try:
        print("[Запит до ШІ Gemini...]")
        response = ai_model.generate_content(question)
        return response.text.strip()
    except Exception as e:
        print(f"Помилка ШІ: {e}")
        return "Мої мислячі схеми перевантажені. Запитай мене краще про датчики або про операційну систему!"

def run_chat_mode():
    speak("Режим спілкування! Запитуй мене про мої компоненти, характеристики та проблеми. Для виходу скажи: Назад.")
    while True:
        phrase = listen_voice()
        if not phrase: continue
            
        if "назад" in phrase or "вихід" in phrase: speak("Завершую розмову."); break
        
        # --- БАЗА ЗНАНЬ ТЕО ---
        
        # 1. Створення, розробник та компоненти
        if "хто ти" in phrase or "що за робот" in phrase: 
            speak("Я Тео — робототехнічна платформа Freenove Tank Robot на базі мікрокомп'ютера Raspberry Pi 5!")
            
        elif "хто створив" in phrase or "хто працював" in phrase:
            speak("Над моїм створенням, збіркою та програмуванням працювала Людкевич Надія.")
            
        elif "компонент" in phrase or "із чого складаєшся" in phrase or "матеріали" in phrase:
            speak("Я складаюся з мікрокомп'ютера Raspberry Pi 5, материнської плати розширення Freenove Tank Smart Car Shield, "
                  "гусеничного треку з двома двигунами постійного струму, камери високої роздільної здатності, двох сервоприводів, "
                  "ультразвукового датчика відстані Аш Це СР нуль чотири, інфрачервоних сенсорів лінії та блоку акумуляторів 18650.")

        # Операційна система Raspberry Pi OS vs Windows
        elif "операційну систему" in phrase or "ос" in phrase or "відрізняється від windows" in phrase or "віндовс" in phrase or "windows" in phrase:
            speak("Я працюю на Raspberry Pi OS — це спеціальна полегшена операційна система на базі Linux, створена саме для мікрокомп'ютерів. "
                  "На відміну від важкої та закритої Windows, моя система повністю безкоштовна, відкрита, не витрачає зайву пам'ять на фонові процеси "
                  "і дозволяє програмам на Python напряму і без затримок керувати моїми моторами, датчиками та GPIO-контактами.")

        # 2. Raspberry Pi 5 та обґрунтування (Процесор, Чип RP1, Живлення)
        elif "raspberry" in phrase or "пі 5" in phrase or "плата" in phrase:
            speak("Мій мозок — це Raspberry Pi 5. Він у три рази потужніший за четверту версію! Він забезпечує"
                  "комп'ютерний зір, швидке розпізнавання голосу та миттєву обробку даних без затримок.")
                  
        elif "процесор" in phrase or "cpu" in phrase: 
            speak("У мене всередині 64-бітний чотириядерний процесор Broadcom BCM2712 із частотою 2.4 ГГц. "
                  "Він миттєво обробляє складні ШІ команди завдяки кеш-пам'яті другого та третього рівнів.")
            
        elif "відеокарта" in phrase or "gpu" in phrase: 
            speak("Мій відеочип VideoCore VII працює на частоті 800 мегагерц. Він підтримує стандарти OpenGL та Vulkan, "
                  "що дозволяє транслювати плавну картинку високої якості з моєї камери.")
            
        elif "чип" in phrase and "rp1" in phrase: 
            speak("Чип Ер Пі Один — це власний південний міст від Raspberry Pi. Він апаратно генерує ШІМ сигнали "
                  "для моїх моторів незалежно від операційної системи. Завдяки цьому мої рухи та сервоприводи працюють абсолютно плавно, без мікрозатримок.")

        elif "акумулятор" in phrase or "батаре" or "18650" in phrase:
            speak("Я живлюся від двох літій-іонних високотокових батарей типу 18650 загальною напругою близько 7.4 вольт. "
                  "Вони мають велику енергоємність. Звичайні пальчикові батарейки просто не змогли б увімкнути таку потужну систему!")
            
        elif "на скільки вистачає" in phrase or "час роботи" in phrase:
            speak("Залежно від ємності акумуляторів, моєї батареї вистачає приблизно до двох годин активного руху та трансляції відео.")

        # 3. Режими роботи та характеристики (Що вміє робити)
        elif "що вмієш" in phrase or "що можеш" in phrase or "режим" in phrase or "функції" in phrase:
            speak("Я маю три розумні режими! Перший — вільне керування через голос або веб-інтерфейс, де можна контролювати двигуни, "
                  "вмикати світло, керувати камерою та клешнею для підняття дрібних предметів. Другий — слідування по чорній лінії з прибиранням перешкод. "
                  "Третій — автономне уникнення перешкод. Також я підтримую трансляцію першої особи еф пі ві та колірний трекінг об'єктів.")

        elif "трекінг" in phrase or "колір" in phrase:
            speak("Завдяки комп'ютерному зору OpenCV я вмію розпізнавати об'єкти заданого кольору, наприклад, червоний м'яч, і автоматично рухатися за ним.")

        # 4. Програмування та Команди
        elif "мова" in phrase or "як запрограмований" in phrase:
            speak("Увесь мій код та алгоритми штучного інтелекту написані на мові програмування Python 3.")
            
        elif "команди" in phrase or "як запустити" in phrase or "термінал" in phrase:
            speak("Для мого запуску в терміналі Лінукс переходять у директорію коду сервера командою сі ді, "
                  "а потім запускають головний сервер через команду судо пайтон мейн крапка пай. Також є тести моторів, ультразвуку та сервоприводів.")

        # 5. Проблими та шляхи вирішення (Охолодження, Wi-Fi, Датчики)
        elif "охолодження" in phrase or "перегрів" in phrase or "тротлінг" in phrase:
            speak("Мій процесор дуже потужний і при роботі з комп'ютерним зором нагрівається вище 80 градусів. Через брак місця під платою розширення, "
                  "стандартний кулер не влазить. Проблема вирішується тонокими мідними радіаторами, подовжувачами роз'єму GPIO "
                  "або встановленням вентилятора 30 на 30 міліметрів збоку акрилового корпусу для примусового продування.")

        elif "інтернет" in phrase or "wi-fi" in phrase or "лагає" in phrase or "затримка" in phrase:
            speak("Через перевантажені мережі 2.4 гігагерца або велику відстань відео може лагати. Для вирішення варто використовувати частоту 5 гігагерц, "
                  "налаштувати Raspberry Pi в режим Точки доступу, або роздати Wi-Fi прямо з мобільного телефону.")

        elif "датчик" in phrase or "врізаєшся" in phrase or "ультразвук" in phrase: 
            speak("Мій ультразвуковий датчик HC-SR04 вимірює відстань від 2 до 400 сантиметрів за принципом ехолокатора. "
                  "Я можу врізатися, якщо перешкода тонка, як ніжка стільця, або м'яка і поглинає звук. А інфрачервоні датчики лінії "
                  "можуть сліпнути на вулиці через сонячне світло. Їхню чутливість потрібно підкручувати викруткою.")

        # --- ЗВЕРНЕННЯ ДО ШТУЧНОГО ІНТЕЛЕКТУ, ЯКЩО НІЧОГО НЕ ПІДІЙШЛО ---
        else: 
            ai_response = ask_gemini_ai(phrase)
            speak(ai_response)

def main():
    first_run = True  # Прапорець для відстеження першого запуску
    while True:
        if first_run:
            speak("Привіт! Бажаєш поспілкуватися чи керувати?")
            first_run = False  # Більше це вітання не повториться
        else:
            speak("Я повернувся в головне меню. Що вибереш: спілкуватися чи керувати?")
            
        choice = listen_voice()
        
        if "спілкуватися" in choice or "поговорити" in choice: run_chat_mode()
        elif "керувати" in choice or "команди" in choice: run_control_mode()
        elif "вимкнись" in choice or "завершити" in choice:
            speak("До побачення, відключаюсь!")
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
