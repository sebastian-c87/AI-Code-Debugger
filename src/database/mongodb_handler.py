"""
Handler dla bazy danych MongoDB
Zarządza połączeniem i operacjami na bazie danych
"""

import pymongo
import os
from pymongo import MongoClient
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import pytz 
import uuid
from .models import CodeAnalysisResult, UserSession, AnalysisStatus
from ..utils.serialization import serialize_for_mongodb, deserialize_from_mongodb


class MongoDBHandler:
    """Klasa obsługująca operacje na bazie danych MongoDB"""
    
    def __init__(self, uri: str, database_name: str):
        """
        Inicjalizacja połączenia z MongoDB
        
        Args:
            uri (str): URI połączenia z MongoDB
            database_name (str): Nazwa bazy danych
        """
        self.uri = uri
        self.database_name = database_name
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Nawiązanie połączenia z bazą danych"""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Test połączenia
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            print(f"✓ Połączono z MongoDB: {self.database_name}")
        except Exception as e:
            print(f"❌ Błąd połączenia z MongoDB: {e}")
            raise
    
    def disconnect(self):
        """Zamknięcie połączenia z bazą danych"""
        if self.client:
            self.client.close()
            print("✓ Połączenie z MongoDB zamknięte")
    
    def save_analysis_result(self, analysis_result: CodeAnalysisResult) -> str:
        """
        Zapisanie wyniku analizy do bazy danych
        
        Args:
            analysis_result (CodeAnalysisResult): Wynik analizy
            
        Returns:
            str: ID zapisanego dokumentu
        """
        try:
            collection = self.db.analyses
            
            print(f"💾 Zapisywanie analizy: {analysis_result.file_name}")
            
            try:
            # Konwersja obiektu na słownik
                document_raw = {
                    'timestamp': analysis_result.timestamp,
                    'file_name': analysis_result.file_name,
                    'code_content': analysis_result.code_content[:500] + "..." if len(analysis_result.code_content) > 500 else analysis_result.code_content,
                    'analysis_results': analysis_result.analysis_results,
                    'status': analysis_result.status.value if hasattr(analysis_result.status, 'value') else str(analysis_result.status),
                    'execution_time': analysis_result.execution_time,
                    'error_count': analysis_result.error_count,
                    'warning_count': analysis_result.warning_count,
                    'saved_at': datetime.now(),
                    'session_info': {
                        'user': os.getenv('USERNAME', 'unknown'),
                        'machine': os.getenv('COMPUTERNAME', 'unknown')
                    }
            }
            
                document = serialize_for_mongodb(document_raw)
            
                """print(f"🔍 DEBUG: Dokument po serializacji - typ: {type(document)}")
                print(f"🔍 DEBUG: Klucze dokumentu: {list(document.keys())}")
            
                if 'analysis_results' in document:
                    analysis_data = document['analysis_results']
                    print(f"🔍 DEBUG: Analysis results typ: {type(analysis_data)}")
                    if isinstance(analysis_data, dict):
                        for key, value in analysis_data.items():
                            print(f"🔍 DEBUG: {key}: {type(value)} (pierwsze 3 elementy: {value[:3] if isinstance(value, list) else 'non list'})")
                        """
            except Exception as e:
                print(f"❌ BŁĄD SERIALIZACJI: {e}")
                
                document = {
                    'timestamp': analysis_result.timestamp,
                    'file_name': analysis_result.file_name,
                    'code_content': "ERROR: Could not serialize code content",
                    'analysis_results': self._serialize_analysis_results(analysis_result.analysis_results),
                    'status': str(analysis_result.status),
                    'execution_time': float(analysis_result.execution_time),
                    'error_count': int(analysis_result.error_count),
                    'warning_count': int(analysis_result.warning_count),
                    'saved_at': datetime.now(),
                    'serialization_error': str(e)
                }
            # Zapis do MongoDB
            result = collection.insert_one(document)
            analysis_result.id = str(result.inserted_id)
            
            """saved_doc = collection.find_one({'_id': result.inserted_id})
            if saved_doc:
            
                print(f"✅ SUKCES Zapisano analizę: {analysis_result.id}")
                print(f"📊 Całkowita liczba analiz w bazie: {collection.count_documents({})}")
            else:
                print(f"❌ BŁĄD: Nie można zweryfikować zapisu")
                
            return analysis_result.id
            
        except Exception as e:
            print(f"❌ Błąd zapisu analizy: {e}")
            print(f"🔍 DEBUG: Szczegóły błędu: {type(e).__name__}")"""
            
            # Weryfikacja z prostym komunikatem
            if collection.find_one({'_id': result.inserted_id}):
                print(f"✅ Analiza zapisana: {analysis_result.error_count} błędów, {analysis_result.warning_count} ostrzeżeń")
            else:
                print(f"❌ Błąd zapisu analizy")
            
            return analysis_result.id
        
        except Exception as e:
            print(f"❌ Błąd zapisu: {e}")
            # dont raise
            return f"error_{datetime.now().timestamp()}"
        
    def _serialize_analysis_results(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Serializacja bez szczegółowego debugowania"""
        try:
            serialized = {}
        
            for key, value in analysis_results.items():
                if isinstance(value, list):
                    serialized_list = []
                    for item in value:
                        if hasattr(item, 'to_dict'):
                            serialized_list.append(item.to_dict())
                        elif hasattr(item, '__dict__'):
                            item_dict = item.__dict__.copy()
                            for attr_key, attr_value in item_dict.items():
                                if hasattr(attr_value, 'value'):
                                    item_dict[attr_key] = attr_value.value
                            serialized_list.append(item_dict)
                        else:
                            serialized_list.append(item)
                    serialized[key] = serialized_list
                else:
                    serialized[key] = serialize_for_mongodb(value)
        
            return serialized
        
        except Exception as e:
            print(f"❌ Błąd serializacji: {e}")
            return {
                'serialization_error': str(e),
                'original_keys': list(analysis_results.keys()) if isinstance(analysis_results, dict) else str(type(analysis_results))
            }
    
    def get_analysis_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Pobieranie historii z uproszczonym logowaniem"""
        try:
            collection = self.db.analyses
            total_docs = collection.count_documents({})
        
            print(f"📊 Pobieranie {min(limit, total_docs)} analiz z {total_docs} dostępnych")
        
            if total_docs == 0:
                return []
        
            cursor = collection.find().sort("timestamp", -1).limit(limit)
            results = []
        
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                results.append(doc)
        
            return results
        
        except Exception as e:
            print(f"❌ Błąd pobierania historii: {e}")
            return []
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Pobieranie konkretnej analizy po ID
        
        Args:
            analysis_id (str): ID analizy
            
        Returns:
            Optional[Dict[str, Any]]: Dane analizy lub None
        """
        try:
            from bson import ObjectId
            collection = self.db.analyses
            
            doc = collection.find_one({'_id': ObjectId(analysis_id)})
            if doc:
                doc['_id'] = str(doc['_id'])
                return doc
            return None
            
        except Exception as e:
            print(f"❌ Błąd pobierania analizy: {e}")
            return None
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """
        Usunięcie analizy z bazy danych
        
        Args:
            analysis_id (str): ID analizy
            
        Returns:
            bool: True jeśli usunięto, False w przeciwnym wypadku
        """
        try:
            from bson import ObjectId
            collection = self.db.analyses
            
            result = collection.delete_one({'_id': ObjectId(analysis_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"❌ Błąd usuwania analizy: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Pobieranie statystyk analiz
        
        Returns:
            Dict[str, Any]: Statystyki
        """
        try:
            collection = self.db.analyses
            
            total_analyses = collection.count_documents({})
            
            # Statystyki błędów
            pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'total_errors': {'$sum': '$error_count'},
                        'total_warnings': {'$sum': '$warning_count'},
                        'avg_execution_time': {'$avg': '$execution_time'}
                    }
                }
            ]
            
            stats_result = list(collection.aggregate(pipeline))
            
            if stats_result:
                stats = stats_result[0]
                return {
                    'total_analyses': total_analyses,
                    'total_errors': stats.get('total_errors', 0),
                    'total_warnings': stats.get('total_warnings', 0),
                    'avg_execution_time': round(stats.get('avg_execution_time', 0), 2)
                }
            else:
                return {
                    'total_analyses': total_analyses,
                    'total_errors': 0,
                    'total_warnings': 0,
                    'avg_execution_time': 0
                }
                
        except Exception as e:
            print(f"❌ Błąd pobierania statystyk: {e}")
            return {}
    
    def create_user_session(self) -> str:
        """
        Utworzenie nowej sesji użytkownika
        
        Returns:
            str: ID sesji
        """
        try:
            collection = self.db.sessions
            
            session = UserSession(
                session_id=str(uuid.uuid4()),
                start_time=datetime.now(),
                last_activity=datetime.now()
            )
            
            document = {
                'session_id': session.session_id,
                'start_time': session.start_time,
                'last_activity': session.last_activity,
                'analyses_count': session.analyses_count
            }
            
            collection.insert_one(document)
            return session.session_id
            
        except Exception as e:
            print(f"❌ Błąd tworzenia sesji: {e}")
            raise
    
    def update_session_activity(self, session_id: str):
        """
        Aktualizacja aktywności sesji
        
        Args:
            session_id (str): ID sesji
        """
        try:
            collection = self.db.sessions
            
            collection.update_one(
                {'session_id': session_id},
                {
                    '$set': {'last_activity': datetime.now()},
                    '$inc': {'analyses_count': 1}
                }
            )
            
        except Exception as e:
            print(f"❌ Błąd aktualizacji sesji: {e}")
