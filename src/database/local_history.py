"""
Lokalny system przechowywania historii analiz (bez MongoDB)
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

class LocalHistoryHandler:
    """Klasa obsługująca lokalną historię analiz w plikach JSON"""
    
    def __init__(self, app_data_dir: str = None):
        """
        Inicjalizacja lokalnego handlera historii
        
        Args:
            app_data_dir (str): Katalog do przechowywania danych aplikacji
        """
        # Określenie katalogu dla danych aplikacji
        if app_data_dir:
            self.app_data_dir = Path(app_data_dir)
        else:
            # Domyślny katalog w folderze użytkownika
            user_home = Path.home()
            self.app_data_dir = user_home / "AI_Code_Debugger" / "data"
        
        # Utworzenie katalogu jeśli nie istnieje
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Ścieżki do plików
        self.history_file = self.app_data_dir / "analysis_history.json"
        self.sessions_file = self.app_data_dir / "user_sessions.json"
        
        print(f"📁 Lokalna historia będzie zapisywana w: {self.app_data_dir}")
    
    def save_analysis_result(self, analysis_result) -> str:
        """
        Zapisanie wyniku analizy do lokalnego pliku JSON
        
        Args:
            analysis_result: Wynik analizy
            
        Returns:
            str: ID zapisanego dokumentu
        """
        try:
            # Wczytanie istniejącej historii
            history_data = self._load_history_file()
            
            # Generowanie ID dla nowego rekordu
            record_id = f"local_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(history_data)}"
            
            # Przygotowanie danych do zapisu
            from ..utils.serialization import serialize_for_mongodb
            
            record = {
                'id': record_id,
                'timestamp': analysis_result.timestamp.isoformat(),
                'file_name': analysis_result.file_name,
                'code_content': analysis_result.code_content[:500] + "..." if len(analysis_result.code_content) > 500 else analysis_result.code_content,
                'analysis_results': serialize_for_mongodb(analysis_result.analysis_results),
                'status': analysis_result.status.value if hasattr(analysis_result.status, 'value') else str(analysis_result.status),
                'execution_time': analysis_result.execution_time,
                'error_count': analysis_result.error_count,
                'warning_count': analysis_result.warning_count,
                'saved_at': datetime.now().isoformat()
            }
            
            # Dodanie nowego rekordu na początek listy
            history_data.insert(0, record)
            
            # Ograniczenie historii do 100 ostatnich analiz
            if len(history_data) > 100:
                history_data = history_data[:100]
            
            # Zapisanie do pliku
            self._save_history_file(history_data)
            
            print(f"✅ Lokalnie zapisano analizę: {record_id}")
            return record_id
            
        except Exception as e:
            print(f"❌ Błąd lokalnego zapisu: {e}")
            return f"error_{datetime.now().timestamp()}"
    
    def get_analysis_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Pobieranie historii analiz z lokalnego pliku
        
        Args:
            limit (int): Maksymalna liczba rekordów
            
        Returns:
            List[Dict[str, Any]]: Lista historii analiz
        """
        try:
            history_data = self._load_history_file()
            
            # Ograniczenie do żądanej liczby rekordów
            limited_data = history_data[:limit]
            
            print(f"📊 Zwrócono {len(limited_data)} analiz z {len(history_data)} dostępnych (lokalnie)")
            return limited_data
            
        except Exception as e:
            print(f"❌ Błąd pobierania lokalnej historii: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Pobieranie statystyk z lokalnej historii
        
        Returns:
            Dict[str, Any]: Statystyki analiz
        """
        try:
            history_data = self._load_history_file()
            
            total_analyses = len(history_data)
            total_errors = sum(record.get('error_count', 0) for record in history_data)
            total_warnings = sum(record.get('warning_count', 0) for record in history_data)
            
            # Średni czas wykonania
            execution_times = [record.get('execution_time', 0) for record in history_data if record.get('execution_time')]
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            return {
                'total_analyses': total_analyses,
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'avg_execution_time': round(avg_execution_time, 2),
                'storage_type': 'local_files'
            }
            
        except Exception as e:
            print(f"❌ Błąd pobierania statystyk: {e}")
            return {'total_analyses': 0, 'total_errors': 0, 'total_warnings': 0, 'avg_execution_time': 0}
    
    def create_user_session(self) -> str:
        """
        Utworzenie sesji użytkownika w lokalnym pliku
        
        Returns:
            str: ID sesji
        """
        try:
            import uuid
            session_id = str(uuid.uuid4())
            
            # Wczytanie istniejących sesji
            sessions_data = self._load_sessions_file()
            
            # Dodanie nowej sesji
            session_record = {
                'session_id': session_id,
                'start_time': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'analyses_count': 0
            }
            
            sessions_data.append(session_record)
            
            # Zapisanie sesji
            self._save_sessions_file(sessions_data)
            
            print(f"✅ Lokalna sesja utworzona: {session_id}")
            return session_id
            
        except Exception as e:
            print(f"❌ Błąd tworzenia lokalnej sesji: {e}")
            return "local_session_error"
    
    def update_session_activity(self, session_id: str):
        """
        Aktualizacja aktywności sesji w lokalnym pliku
        
        Args:
            session_id (str): ID sesji
        """
        try:
            sessions_data = self._load_sessions_file()
            
            # Znajdź i zaktualizuj sesję
            for session in sessions_data:
                if session['session_id'] == session_id:
                    session['last_activity'] = datetime.now().isoformat()
                    session['analyses_count'] = session.get('analyses_count', 0) + 1
                    break
            
            # Zapisanie zaktualizowanych sesji
            self._save_sessions_file(sessions_data)
            
        except Exception as e:
            print(f"❌ Błąd aktualizacji lokalnej sesji: {e}")
    
    def _load_history_file(self) -> List[Dict[str, Any]]:
        """Wczytanie historii z pliku JSON"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            print(f"❌ Błąd wczytywania historii: {e}")
            return []
    
    def _save_history_file(self, data: List[Dict[str, Any]]):
        """Zapisanie historii do pliku JSON"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Błąd zapisywania historii: {e}")
    
    def _load_sessions_file(self) -> List[Dict[str, Any]]:
        """Wczytanie sesji z pliku JSON"""
        try:
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            print(f"❌ Błąd wczytywania sesji: {e}")
            return []
    
    def _save_sessions_file(self, data: List[Dict[str, Any]]):
        """Zapisanie sesji do pliku JSON"""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Błąd zapisywania sesji: {e}")
    
    def disconnect(self):
        """Symulacja disconnection (dla kompatybilności)"""
        print("✓ Lokalna historia zamknięta")
