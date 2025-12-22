import speech_recognition as sr
import webbrowser
import pyttsx3
import os
import musicLibrary
import requests
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()  # loads .env file

WEATHERSTACK_API_KEY = os.getenv("WEATHERSTACK_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
news_api_key=os.getenv("news_api")

recognizier=sr.Recognizer()
news=news_api_key

def speak(text):
    engine=pyttsx3.init()
    engine.setProperty('rate', 150)   
    engine.say(text)
    engine.runAndWait()
    engine.stop()

#Gemini Processs
def aiProcess(command):
    client = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/" 
    )

    completion = client.chat.completions.create(
        model="gemini-2.5-flash", # 3. Change the model name to a compatible Gemini model
        messages=[
            {"role": "system", "content": "You are a virtual assistant named jarvis skilled in general like Alexa and Google Cloud"},
            {"role": "user", "content": command}
        ]
    )

    return completion.choices[0].message.content

#Weather related command
def getWeather(city):
    url = f"http://api.weatherstack.com/current?access_key={WEATHERSTACK_API_KEY}&query={city}"
    r = requests.get(url)

    if r.status_code != 200:
        speak("Sorry, I could not get the weather.")
        return

    data = r.json()

    if "error" in data:
        speak("City not found.")
        return

    temperature = data["current"]["temperature"]
    description = data["current"]["weather_descriptions"][0]
    humidity = data["current"]["humidity"]

    speak(
        f"The temperature in {city} is {temperature} degree celsius. "
        f"Weather is {description} with humidity {humidity} percent."
    )

#Current Weather info
def getCurrentCity():
    try:
        r = requests.get("http://ip-api.com/json/")
        data = r.json()
        return data["city"]
    except:
        return None


#Processs the command given by user
def processCommand(c):
    c = c.lower().strip()
    print("Final command received:", c)

    # -------------------------------------------------
    # 1.Hii - BYE CONDITION (MUST BE FIRST)
    # -------------------------------------------------
    if "bye" in c or "jarvis bye" in c:
        speak("Bye, have a great day!")
        return "exit"   # for breaking main loop safely
    
    elif "hii" in c or "hello jarvis" in c:
        speak("Hey, How can i help you today!")
         

    # -------------------------------------------------
    # 2. OPEN WHATSAPP APP ON WINDOWS
    # -------------------------------------------------
    # elif "open whatsapp" in c or "open whatsapp chat" in c:
    #     speak("Opening WhatsApp")
    #     print("Opening WhatsApp Desktop")

    #     # open WhatsApp Desktop safely
    #     os.system("start whatsapp:")

    elif "open whatsapp" in c or "open whatsapp chat" in c:
        speak("Tell me the phone number, digit by digit")

        try:
            with sr.Microphone() as source:
                recognizier.adjust_for_ambient_noise(source, duration=0.5)
                # Give longer phrase time limit for complete number
                audio = recognizier.listen(source, timeout=10, phrase_time_limit=10)

            phone = recognizier.recognize_google(audio)
            print(f"Raw detected text: {phone}")

            # Keep only digits
            phone = ''.join(filter(str.isdigit, phone))

            # Ensure 10 digits
            if len(phone) < 10:
                speak("Could not detect full number. Please type it manually.")
                phone = input("Enter full phone number: ")
                phone = ''.join(filter(str.isdigit, phone))

            if not phone.startswith("+"):
                phone = "+91" + phone  # Adjust country code as needed

            # Confirm detected number
            print(f"Detected number: {phone}")
            speak(f"Detected number is {phone}. Opening WhatsApp chat.")

            # Open WhatsApp chat
            os.system(f'start whatsapp://send?phone={phone}')

        except Exception as e:
            print(e)
            speak("Could not open WhatsApp chat")


    # -------------------------------------------------
    # 3. YOUR NORMAL COMMANDS
    # -------------------------------------------------
    elif "open google" in c.lower():
        webbrowser.open("https://google.com")
    elif "open facebook" in c.lower():
        webbrowser.open("https://facebook.com")
    elif "open youtube" in c.lower():
        webbrowser.open("https://youtube.com")
    elif "open linkedin" in c.lower():
        webbrowser.open("https://linkedin.com")
    elif c.lower().startswith("play"):
        songs=c.lower().split(" ")[1] #command= play bulley songs=["play","bulley"] so song bulley[1] will play
        link=musicLibrary.music[songs]
        webbrowser.open(link)


    # -------------------------------------------------
    # 4. Weather Information
    # -------------------------------------------------
    elif "tell me weather" in c.lower() or "weather" in c.lower() or "tell me a weather" in c.lower():
        speak("Tell me a city name")
        print("Jarvis: Tell me a city name")

        try:
            with sr.Microphone() as source:
                recognizier.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizier.listen(source, timeout=4, phrase_time_limit=3)

            city = recognizier.recognize_google(audio)
            print("Detected city:", city)

        except sr.WaitTimeoutError:
            print("No city spoken. Using current location.")
            speak("You did not say anything. Showing current weather.")
            city = getCurrentCity()

        except Exception:
            print("Speech not recognized. Using current location.")
            speak("I could not hear you clearly. Showing current weather.")
            city = getCurrentCity()

        if city:
            getWeather(city)
        else:
            speak("Sorry, I could not detect your location.")


    # -------------------------------------------------
    # 5. NEWS READING WITH STOP
    # -------------------------------------------------
    elif "news" in c.lower():
        r = requests.get(f"https://newsapi.org/v2/top-headlines?category=general&apiKey={news}")

        if r.status_code == 200:
            data = r.json()
            articles = data.get('articles', [])

            if not articles:
                speak("No news found.")
                return

            speak("Reading latest news. Say stop anytime to stop me.")

            for art in articles:
                title = art.get("title", "")
                
                # Skip empty titles
                if not title.strip():
                    continue
                print("Speaking:", art['title'])
                speak(title)

                #LISTEN FOR STOP AFTER EACH HEADLINE
                with sr.Microphone() as source:
                    recognizier.adjust_for_ambient_noise(source, duration=0.5)
                    try:
                        print("Listening for stop command...")   # DEBUG
                        audio = recognizier.listen(source, timeout=2, phrase_time_limit=2)
                        c = recognizier.recognize_google(audio).lower()
                        print("Heard:", c,"\n")   # DEBUG

                        if "stop" in c or "enough" in c or "pause" in c:
                            speak("Okay, stopping the news.")
                            break

                    except:
                        # Nothing said → just move to next headline
                        continue

    # -------------------------------------------------
    # 6. SET ALARM
    # -------------------------------------------------
    elif "open clock" in c or "open alarm" in c:
        speak("Opening clock application")
        print("Opening Windows Clock app")
        os.system("start ms-clock:")


    # -------------------------------------------------
    # 7. DEFAULT: GEMINI AI WITH STOP LISTENING
    # -------------------------------------------------
    else:
    # Get Gemini output
        output = aiProcess(c)

        # Split Gemini response into sentences
        sentences = output.split(".")

        speak("Okay.")

        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue

            # Speak one sentence at a time
            speak(s)

            # --- LISTEN FOR STOP AFTER EACH SENTENCE ---
            with sr.Microphone() as source:
                recognizier.adjust_for_ambient_noise(source, duration=0.5)

                try:
                    print("Listening for stop command...")
                    audio = recognizier.listen(source, timeout=2, phrase_time_limit=2)
                    c = recognizier.recognize_google(audio).lower()
                    print("Heard:", c)

                    if "stop" in c or "pause" in c or "enough" in c:
                        speak("Okay, stopping now.")
                        break

                except:
                    # If user says nothing → continue to next sentence
                    continue


# -------------------------------------------------
# Main Programs Starts From here
# -------------------------------------------------
if __name__== "__main__" :
    speak("Initializing Jarvis......")
    r = sr.Recognizer()
    while True:
        #Listen for the wake word "Jarvis"
        # obtain audio from the microphone
        # r = sr.Recognizer()
           
        try:
            with sr.Microphone() as source:
                print("Listening.....")
                r.adjust_for_ambient_noise(source, duration=0.2)
                audio = r.listen(source,timeout=2,phrase_time_limit=1)
            word=r.recognize_google(audio)
            print("Detected word:",word)
            print("Recognizing....")
            if(word.lower().strip() == "jarvis" ):
                speak("Yaa")
                #Listen for command
                with sr.Microphone() as source:
                    print("Jarvis Active.....")
                    # audio = r.listen(source)
                    audio = r.listen(source)
                    command=r.recognize_google(audio)

                    result = processCommand(command)

                    #If processCommand returned "exit", break the loop
                    if result == "exit":
                        break


        except sr.WaitTimeoutError:
            print("Timed out")
        except Exception as e:
            print("Error; {0}".format(e)+"Speak Jarvis..")

