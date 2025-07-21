"""
Hybrydowy handler bazy danych - MongoDB + lokalne pliki
Autor: Sebastian Ciborowski
"""

from typing import List, Dict, Any, Optional, Union
from .mongodb_handler import MongoDBHandler
from .local_history import LocalHistoryHandler

class HybridDatabaseHandler:
    """Klasa łącząca MongoDB i lokalne pliki"""
    
    def __init__(self, uri: str, database_name: str):
        """
        Inicjalizacja hybrydowego handlera
        
        Args:
            uri (str): URI MongoDB
            database_name (str): Nazwa bazy danych
        """
        self.mongodb_handler = None
        self.local_handler = LocalHistoryHandler()
        self.use_mongodb = False
        
        # Próba połączenia z MongoDB
        try:
            self.mongodb_handler = MongoDBHandler(uri, database_name)
            self.use_mongodb = True
            print("✅ Hybrydowy handler: używa MongoDB")
        except Exception as e:
            print(f"⚠️ MongoDB niedostępny: {e}")
            print("🔄 Hybrydowy handler: używa lokalnych plików")
    
    def save_analysis_result(self, analysis_result) -> str:
        """Zapisanie wyniku analizy - MongoDB lub lokalnie"""
        if self.use_mongodb and self.mongodb_handler:
            try:
                return self.mongodb_handler.save_analysis_result(analysis_result)
            except Exception as e:
                print(f"❌ Błąd MongoDB, przełączanie na lokalny zapis: {e}")
                self.use_mongodb = False
                return self.local_handler.save_analysis_result(analysis_result)
        else:
            return self.local_handler.save_analysis_result(analysis_result)
    
    def get_analysis_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Pobieranie historii - MongoDB lub lokalnie"""
        if self.use_mongodb and self.mongodb_handler:
            try:
                return self.mongodb_handler.get_analysis_history(limit)
            except Exception as e:
                print(f"❌ Błąd MongoDB, przełączanie na lokalny odczyt: {e}")
                return self.local_handler.get_analysis_history(limit)
        else:
            return self.local_handler.get_analysis_history(limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Pobieranie statystyk - MongoDB lub lokalnie"""
        if self.use_mongodb and self.mongodb_handler:
            try:
                return self.mongodb_handler.get_statistics()
            except Exception as e:
                print(f"❌ Błąd MongoDB, przełączanie na lokalne statystyki: {e}")
                return self.local_handler.get_statistics()
        else:
            return self.local_handler.get_statistics()
    
    def create_user_session(self) -> str:
        """Utworzenie sesji użytkownika - MongoDB lub lokalnie"""
        if self.use_mongodb and self.mongodb_handler:
            try:
                return self.mongodb_handler.create_user_session()
            except Exception as e:
                print(f"❌ Błąd MongoDB, przełączanie na lokalną sesję: {e}")
                return self.local_handler.create_user_session()
        else:
            return self.local_handler.create_user_session()
    
    def update_session_activity(self, session_id: str):
        """Aktualizacja aktywności sesji - MongoDB lub lokalnie"""
        if self.use_mongodb and self.mongodb_handler:
            try:
                self.mongodb_handler.update_session_activity(session_id)
            except Exception as e:
                print(f"❌ Błąd MongoDB, aktualizacja lokalnej sesji: {e}")
                self.local_handler.update_session_activity(session_id)
        else:
            self.local_handler.update_session_activity(session_id)
    
    def disconnect(self):
        """Zamknięcie połączeń"""
        if self.use_mongodb and self.mongodb_handler:
            self.mongodb_handler.disconnect()
        self.local_handler.disconnect()
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Informacje o używanym systemie przechowywania"""
        return {
            'uses_mongodb': self.use_mongodb,
            'storage_type': 'MongoDB' if self.use_mongodb else 'Local Files',
            'local_data_dir': str(self.local_handler.app_data_dir)
        }
