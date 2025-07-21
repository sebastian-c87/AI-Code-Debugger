# src/utils/config.py - ZMODYFIKOWANA WERSJA
"""
Konfiguracja aplikacji z wbudowanymi kluczami API
Autor: Sebastian Ciborowski
Data: 2025-07-18
"""

import os
from src.security.key_manager import key_manager

class Config:
    """Klasa konfiguracji z wbudowanymi zaszyfrowanymi kluczami"""
    
    def __init__(self):
        """Inicjalizacja konfiguracji"""
        # Ładuj klucze z wbudowanego menedżera
        self.secrets = key_manager.get_all_secrets()
        print("✅ Konfiguracja z wbudowanymi kluczami załadowana")
    
    def get(self, key, default=None):
        """
        Pobiera wartość konfiguracji.
        
        Args:
            key (str): Nazwa klucza
            default: Wartość domyślna
            
        Returns:
            str: Wartość konfiguracji
        """
        # Najpierw sprawdź wbudowane sekrety
        value = self.secrets.get(key)
        
        # Jeśli nie ma w sekretach, sprawdź zmienne środowiskowe
        if not value:
            value = os.getenv(key, default)
        
        return value
    
    def is_configured(self):
        """Sprawdza czy wszystkie wymagane klucze są dostępne"""
        required_keys = ['OPENAI_API_KEY']
        
        for key in required_keys:
            if not self.get(key):
                return False
        
        return True
    
    def get_openai_key(self):
        """Pobiera klucz OpenAI API"""
        return self.get('OPENAI_API_KEY')
    
    def get_mongodb_uri(self):
        """Pobiera URI MongoDB"""
        return self.get('MONGODB_URI', 'mongodb://localhost:27017')
    
    def get_database_name(self):
        """Pobiera nazwę bazy danych"""
        return self.get('DATABASE_NAME', 'ai_code_debugger')
