"""
Test podstawowych bibliotek wymaganych do działania aplikacji
"""

required_libraries = [
    ("customtkinter", "GUI framework"),
    ("pymongo", "MongoDB connection"),
    ("openai", "OpenAI API"),
    ("dotenv", "Environment variables"),
    ("requests", "HTTP requests"),
    ("chardet", "Character encoding detection"),
    ("pylint", "Code analysis"),
]

optional_libraries = [
    ("transformers", "HuggingFace models"),
    ("torch", "PyTorch backend"),
]

print("🔍 Testowanie instalacji bibliotek...\n")

print("📚 WYMAGANE BIBLIOTEKI:")
all_required_ok = True
for lib_name, description in required_libraries:
    try:
        if lib_name == "dotenv":
            from dotenv import load_dotenv
        else:
            __import__(lib_name)
        print(f"  ✅ {lib_name} - {description}")
    except ImportError as e:
        print(f"  ❌ {lib_name} - {description} - BŁĄD: {e}")
        all_required_ok = False

print(f"\n📦 OPCJONALNE BIBLIOTEKI:")
for lib_name, description in optional_libraries:
    try:
        __import__(lib_name)
        print(f"  ✅ {lib_name} - {description}")
    except ImportError:
        print(f"  ⚠️ {lib_name} - {description} - Niedostępne (aplikacja będzie działać)")

print(f"\n🎯 WYNIK:")
if all_required_ok:
    print("✅ Wszystkie wymagane biblioteki są zainstalowane!")
    print("🚀 Aplikacja powinna działać poprawnie!")
else:
    print("❌ Brakuje wymaganych bibliotek - aplikacja może nie działać")

print(f"\n💡 Aby uruchomić aplikację: python main.py")
