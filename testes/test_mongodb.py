"""
Test połączenia z MongoDB
"""
try:
    from pymongo import MongoClient
    
    print("🔄 Testowanie połączenia z MongoDB...")
    
    # Próba połączenia
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    
    # Test ping
    client.admin.command('ping')
    
    print("✅ MongoDB działa poprawnie!")
    print(f"📊 Wersja serwera: {client.server_info()['version']}")
    
    # Lista baz danych
    databases = client.list_database_names()
    print(f"📁 Dostępne bazy danych: {databases}")
    
    client.close()
    
except Exception as e:
    print(f"❌ Błąd połączenia z MongoDB: {e}")
    print("💡 Sprawdź czy usługa MongoDB jest uruchomiona")
