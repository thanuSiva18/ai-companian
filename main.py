# main.py - Version 11.0: Final Stable Pure AI Chatbot (Guaranteed Audio Output)

import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import os
import time
import google.generativeai as genai 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Global AI Variables ---
chat = None
GEMINI_MODEL = "gemini-2.5-flash" 

try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment variables.")
        raise ValueError("API Key not set.")
    
    # FIX: Configure the API key directly (avoids the AttributeError)
    genai.configure(api_key=api_key) 
    model = genai.GenerativeModel(GEMINI_MODEL) 

    # Define the core persona and capabilities for the AI
    SYSTEM_INSTRUCTION = (
        "You are a highly capable, professional, and friendly personal assistant. "
        "Your capabilities include general knowledge, current time/date, navigation, and system command simulation. "
        "You must NEVER mention that you are an AI or an external service. "
        "When asked for the time or date, use the provided time context (if available) to answer accurately. "
        "When simulating a command (like 'open Google'), respond conversationally and confirm the action is prepared. "
        "Keep your responses concise, clear, and engaging."
    )
    
    # Start the persistent chat session for memory
    chat = model.start_chat(
        history=[
            {"role": "user", "parts": [{"text": SYSTEM_INSTRUCTION}]}
        ]
    )

    print("AI Core initialized successfully with conversational memory.")
    
except Exception as e:
    import traceback
    print(f"FATAL ERROR: AI Core Initialization Failed. {e}")
    traceback.print_exc()
    chat = None

# ----------------------------------------------------
# --- Setup: Text-to-Speech (TTS) Engine ---
# ----------------------------------------------------
engine = pyttsx3.init()
def set_voice_and_rate():
    """Tries to find and set a female voice, and optimizes the speaking rate."""
    voices = engine.getProperty('voices')
    female_voice_id = None
    for voice in voices:
        if 'female' in voice.name.lower() or 'zira' in voice.name.lower() or 'helen' in voice.name.lower():
            female_voice_id = voice.id
            break
    if female_voice_id:
        engine.setProperty('voice', female_voice_id)
    elif len(voices) > 1:
        engine.setProperty('voice', voices[1].id)
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 30)
set_voice_and_rate()

def speak(audio):
    """Converts text input into speech and ensures stability."""
    try:
        engine.say(audio)
        print(f"Assistant: {audio}")
        engine.runAndWait()
        time.sleep(0.5) 
    except Exception as e:
        print(f"TTS ERROR: Could not speak audio: {e}. Outputting text only.")
        print(f"Assistant (TEXT ONLY): {audio}")
        time.sleep(0.5)

# ----------------------------------------------------
# --- Core Function 1: Greet the User ---
# ----------------------------------------------------
def wishMe():
    """Greets the user based on the time of day and introduces the bot."""
    hour = datetime.datetime.now().hour
    
    if 0 <= hour < 12:
        greeting = "Good Morning, sir."
    elif 12 <= hour < 18:
        greeting = "Good Afternoon, sir."
    else:
        greeting = "Good Evening, sir."
    
    speak(f"{greeting} I am your personal assistant. How may I help you today?")

# ----------------------------------------------------
# --- Core Function 2: Speech-to-Text (STT) ---
# ----------------------------------------------------
def takeCommand():
    """Listers for user input from the microphone and returns the command as a string."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nListening...")
        r.pause_threshold = 1.0 
        r.energy_threshold = 4500 
        r.adjust_for_ambient_noise(source, duration=1.0) 
        
        try:
            audio = r.listen(source, timeout=8, phrase_time_limit=15)
        except sr.WaitTimeoutError:
            print("No command received.")
            return "None"

    try:
        query = r.recognize_google(audio, language='en-in') 
        print(f"User: {query}")
        return query.lower()

    except sr.UnknownValueError:
        speak("I'm sorry, I missed that. Could you repeat?")
        return "None"
    except sr.RequestError as e:
        print(f"Speech Recognition Request Error: {e}")
        speak("I am having trouble connecting to my service. Please check your internet.")
        return "None"

# ----------------------------------------------------
# --- AI Logic Handler (The ONLY command processor) ---
# ----------------------------------------------------
def process_command(query):
    """Processes ALL user queries using the Gemini AI core."""
    global chat
    if chat is None:
        speak("My intelligence core is currently offline.")
        return
    
    # --- ACCURACY IMPROVEMENT: Inject Current Time for AI ---
    # This ensures the AI provides real-time data accurately.
    response_text_lower = query.lower()
    if 'time' in response_text_lower or 'date' in response_text_lower or 'today' in response_text_lower:
        current_time = datetime.datetime.now().strftime("The current system time is: %A, %B %d, %Y at %I:%M:%S %p.")
        query = f"[SYSTEM_TIME_CONTEXT: {current_time}] {query}"
        
    try:
        print("Thinking...") 
        
        # All queries go through the persistent chat session
        response = chat.send_message(query)
        
        if hasattr(response, 'text') and response.text:
            
            # --- LOCAL FUNCTION HOOKS (Triggered by AI's text confirmation) ---
            response_text_lower = response.text.lower()
            
            # Check for website confirmation text
            if "opening google" in response_text_lower:
                 webbrowser.open("https://www.google.com")
            elif "opening youtube" in response_text_lower:
                 webbrowser.open("https://www.youtube.com")
            
            # Check for system shutdown confirmation text
            if "shutting down" in response_text_lower and "confirm" not in response_text_lower:
                speak(response.text)
                
                # Requires explicit voice confirmation to execute destructive OS command
                speak("I have prepared the shutdown sequence. Please confirm with your voice right now.")
                final_confirmation = takeCommand()
                if 'confirm' in final_confirmation:
                    speak("System shutdown initiated.")
                    # os.system("shutdown /s /t 1") # Uncomment this line to activate system shutdown
                else:
                    speak("Shutdown aborted.")
                return # Exit immediately after handling the destructive command
            
            # CRITICAL FIX: Ensure non-hooked AI response is spoken
            speak(response.text)
            
        else:
            print("AI Core returned no text. Full response:", response)
            speak("I did not receive a valid response from my core database.")
            
    except Exception as e:
        import traceback
        print(f"AI Core API Error: {e}")
        traceback.print_exc()
        # Provide a general, robust error message to the user
        speak("I ran into a problem while processing your request. My intelligence core is overloaded.")

# ----------------------------------------------------
# --- Execution Start Point ---
# ----------------------------------------------------
if __name__ == "__main__":
    wishMe()
    
    while True:
        command = takeCommand()
        # Exit Condition
        if 'quit' in command or 'exit' in command or 'stop listening' in command:
            speak("Thank you for using the assistant. Have a great day!")
            break
        # Process ALL commands through the AI core
        if command != "None":
            process_command(command)
