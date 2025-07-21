"""
AI Code Debugger - Główny plik aplikacji
Autor: Sebastian Ciborowski
Data: 2025-07-09
"""
import sys
import os

# Obsługa ścieżek dla aplikacji .exe
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
    sys.path.insert(0, application_path)
    src_path = os.path.join(application_path, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    os.chdir(os.path.dirname(sys.executable))
else:
    # Aplikacja uruchomiona jako skrypt Python
    application_path = os.path.dirname(os.path.abspath(__file__))

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from src.gui.main_window import MainWindow
from src.core.code_analyzer import CodeAnalyzer
from src.database.mongodb_handler import MongoDBHandler
from src.database.hybrid_handler import HybridDatabaseHandler
from src.utils.config import Config

# Konfiguracja CustomTkinter
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class AICodeDebugger:
    """Główna klasa aplikacji AI Code Debugger"""
    
    def __init__(self):
        """Inicjalizacja aplikacji"""
        self.config = Config()
        self.setup_database()
        self.setup_analyzer()
        self.setup_gui()
    
    def show_configuration_error(self):
        """Wyświetla błąd konfiguracji"""
        error_msg = """
        ❌ Błąd konfiguracji aplikacji

        Aplikacja nie może znaleźć wymaganych kluczy API.
        To jest błąd wewnętrzny aplikacji.

        Skontaktuj się z autorem aplikacji.
        """
        
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Błąd Konfiguracji", error_msg)
            root.destroy()
        except:
            print(error_msg)
    
    def setup_database(self):
        """Konfiguracja połączenia z bazą danych"""
        try:
            self.db_handler = HybridDatabaseHandler(
            uri=self.config.get('MONGODB_URI'),
            database_name=self.config.get('DATABASE_NAME')
            )
        
            # Wyświetl informacje o używanym systemie
            storage_info = self.db_handler.get_storage_info()
            print(f"📊 System przechowywania: {storage_info['storage_type']}")
            if not storage_info['uses_mongodb']:
                print(f"📁 Dane lokalne: {storage_info['local_data_dir']}")
        
            print("✓ Hybrydowy handler bazy danych zainicjalizowany")
        
        except Exception as e:
                print(f"❌ Krytyczny błąd bazy danych: {str(e)}")
                sys.exit(1)
    
    def setup_analyzer(self):
        """Konfiguracja analizatora kodu"""
        try:
            self.analyzer = CodeAnalyzer(
                openai_api_key=self.config.get('OPENAI_API_KEY'),
                hf_api_key=self.config.get('HUGGINGFACE_API_KEY')
            )
            print("✓ Analizator kodu zainicjalizowany")
        except Exception as e:
            messagebox.showerror("Błąd analizatora", f"Nie można zainicjalizować analizatora: {str(e)}")
            sys.exit(1)
    
    def setup_gui(self):
        """Konfiguracja interfejsu graficznego"""
        try:
            self.root = ctk.CTk()
            self.main_window = MainWindow(
                root=self.root,
                analyzer=self.analyzer,
                db_handler=self.db_handler
            )
            print("✓ Interfejs graficzny zainicjalizowany")
        except Exception as e:
            messagebox.showerror("Błąd GUI", f"Nie można zainicjalizować interfejsu: {str(e)}")
            sys.exit(1)
    
    def run(self):
        """Uruchomienie aplikacji"""
        print("🚀 Uruchamianie AI Code Debugger...")
        self.root.mainloop()

def main():
    """Funkcja główna aplikacji"""
    try:
        app = AICodeDebugger()
        app.run()
    except KeyboardInterrupt:
        print("\n❌ Aplikacja została przerwana przez użytkownika")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Krytyczny błąd aplikacji: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    