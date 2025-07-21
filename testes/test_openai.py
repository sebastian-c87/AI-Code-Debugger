"""
Test połączenia z OpenAI API
"""
import openai
from dotenv import load_dotenv
import os

# Załaduj konfigurację
load_dotenv('config.env')

try:
    # Pobierz klucz API
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ Brak klucza OPENAI_API_KEY w config.env")
        exit(1)
    
    if not api_key.startswith('sk-'):
        print("❌ Nieprawidłowy format klucza OpenAI (powinien zaczynać się od 'sk-')")
        exit(1)
    
    print("🔄 Testowanie połączenia z OpenAI...")
    
    # Inicjalizacja klienta - nowa wersja
    client = openai.OpenAI(api_key=api_key)
    
    # Test połączenia
    response = client.chat.completions.create(
        model="gpt-4.1-nano-2025-04-14",
        messages=[{"role": "user", "content": "Hello, test"}],
        max_tokens=5
    )
    
    print("✅ OpenAI API działa poprawnie!")
    print(f"🎯 Odpowiedź: {response.choices[0].message.content}")
    
except openai.AuthenticationError:
    print("❌ Błąd autoryzacji - sprawdź klucz API OpenAI")
except openai.RateLimitError:
    print("❌ Przekroczony limit API - sprawdź plan OpenAI")
except Exception as e:
    print(f"❌ Błąd OpenAI: {e}")
