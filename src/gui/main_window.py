"""
Główne okno aplikacji AI Code Debugger
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import time
from typing import Dict, Any, Optional
from ..core.code_analyzer import CodeAnalyzer
from ..database.mongodb_handler import MongoDBHandler
from ..database.models import CodeAnalysisResult, AnalysisStatus

class MainWindow:
    """Klasa głównego okna aplikacji"""
    
    def __init__(self, root: ctk.CTk, analyzer: CodeAnalyzer, db_handler: MongoDBHandler):
        """
        Inicjalizacja głównego okna
        
        Args:
            root (ctk.CTk): Główne okno aplikacji
            analyzer (CodeAnalyzer): Instancja analizatora kodu
            db_handler (MongoDBHandler): Handler bazy danych
        """
        self.root = root
        self.analyzer = analyzer
        self.db_handler = db_handler
        self.current_analysis = None
        
        self.setup_window()
        self.create_widgets()
        self.create_menu()
        
        # Utworzenie sesji użytkownika
        try:
            self.session_id = self.db_handler.create_user_session()
        except:
            self.session_id = "local_session"
    
    def setup_window(self):
        """Konfiguracja głównego okna"""
        self.root.title("AI Code Debugger v1.0")
        
        # Proste pobranie wymiarów i ustawienie 90% rozmiaru ekranu
        w = int(self.root.winfo_screenwidth() * 0.9)
        h = int(self.root.winfo_screenheight() * 0.9)
        
        # Pozycjonowanie w lewym górnym rogu
        x = 0
        y = 0
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        # Konfiguracja grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
            
    def create_widgets(self):    
        """Utworzenie widgetów interfejsu"""
        # Główny frame
        main_frame = ctk.CTkFrame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=2)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Pasek narzędzi
        toolbar = ctk.CTkFrame(main_frame)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Przyciski toolbar
        self.btn_open_file = ctk.CTkButton(
            toolbar, 
            text="📁 Otwórz Plik", 
            command=self.open_file,
            width=120,
            font=("Arial", 12, "bold"),
            fg_color="#1f538d",
            hover_color="#143753"
        )
        self.btn_open_file.pack(side="left", padx=5)
        
        self.btn_analyze = ctk.CTkButton(
            toolbar, 
            text="🔍 ANALIZUJ KOD", 
            command=self.analyze_code,
            width=140,
            height=35,
            font=("Arial", 12, "bold"),
            fg_color="#2b8c2b",
            hover_color="#1e6b1e",
            text_color="white"
        )
        self.btn_analyze.pack(side="left", padx=10)
        
        self.btn_clear = ctk.CTkButton(
            toolbar, 
            text="🗑️ Wyczyść", 
            command=self.clear_editor,
            width=100,
            font=("Arial", 12, "bold"),
            fg_color="#d4691d",
            hover_color="#b85516"
        )
        self.btn_clear.pack(side="left", padx=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            toolbar,
            text="Gotowy do analizy kodu",
            font=("Arial", 11)
        )
        self.status_label.pack(side="right", padx=15)
        
        # Panel edytora (lewa strona)
        editor_frame = ctk.CTkFrame(main_frame)
        editor_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        editor_frame.grid_columnconfigure(1, weight=1)
        editor_frame.grid_rowconfigure(1, weight=1)
        
        # Nagłówek edytora
        editor_header = ctk.CTkLabel(editor_frame, text="Edytor Kodu Python", font=("Arial", 16, "bold"))
        editor_header.grid(row=0, column=0, columnspan=2, pady=5)
        
        # Frame dla numeracji i edytora
        editor_content_frame = ctk.CTkFrame(editor_frame)
        editor_content_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        editor_content_frame.grid_columnconfigure(1, weight=1)
        editor_content_frame.grid_rowconfigure(0, weight=1)
    
        # Widget numeracji linii
        self.line_numbers = ctk.CTkTextbox(
            editor_content_frame,
            width=50,  # Szerokość panelu numeracji
            font=("Consolas", 12),
            wrap="none",
            activate_scrollbars=False  # Wyłączenie scrollbarów dla numeracji
        )
        self.line_numbers.grid(row=0, column=0, sticky="nsew", padx=(1, 2))
        
        # Edytor kodu
        self.code_editor = ctk.CTkTextbox(
            editor_content_frame,  
            font=("Consolas", 12),
            wrap="none"
        )
        self.code_editor.grid(row=0, column=1, sticky="nsew", padx=(1, 2))
        
        # Stylowanie numeracji
        self.line_numbers.configure(
            fg_color="#2b2b2b",    # Ciemniejsze tło
            text_color="#666666",  # Szary tekst numerów
            border_width=0,
            corner_radius=0
        )
    
        # Wyłączenie edycji numeracji
        self.line_numbers.configure(state="disabled")
        
        # Zablokowanie scrollowania kółkiem myszy w numeracji
        self.line_numbers.bind('<MouseWheel>', lambda e: "break")

        # Zablokowanie scrollowania klawiszami w numeracji  
        self.line_numbers.bind('<Up>', lambda e: "break")
        self.line_numbers.bind('<Down>', lambda e: "break")
        self.line_numbers.bind('<Prior>', lambda e: "break")  # Page Up
        self.line_numbers.bind('<Next>', lambda e: "break")   # Page Down

        # Zablokowanie scrollowania przez kliknięcie i przeciąganie
        self.line_numbers.bind('<Button-4>', lambda e: "break")  # Linux scroll up
        self.line_numbers.bind('<Button-5>', lambda e: "break")  # Linux scroll down
    
        # Binding dla synchronizacji scrollowania
        self.code_editor.bind('<KeyRelease>', self.update_line_numbers)
        self.code_editor.bind('<Button-1>', self.update_line_numbers)
        self.code_editor.bind('<MouseWheel>', self.sync_scroll)
    
        # Początkowa numeracja
        self.update_line_numbers()
        
        # Panel sugestii (prawa strona)
        suggestions_frame = ctk.CTkFrame(main_frame)
        suggestions_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        suggestions_frame.grid_columnconfigure(0, weight=1)
        suggestions_frame.grid_rowconfigure(1, weight=1)
        
        # Nagłówek sugestii
        suggestions_header = ctk.CTkLabel(suggestions_frame, text="Wyniki Analizy", font=("Arial", 16, "bold"))
        suggestions_header.grid(row=0, column=0, pady=5)
        
        # Zakładki dla wyników
        self.results_tabview = ctk.CTkTabview(suggestions_frame)
        self.results_tabview.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Zakładka błędów
        self.errors_tab = self.results_tabview.add("Błędy")
        self.errors_text = ctk.CTkTextbox(self.errors_tab, font=("Consolas", 10))
        self.errors_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Zakładka sugestii AI
        self.ai_tab = self.results_tabview.add("Sugestie AI")
        self.ai_text = ctk.CTkTextbox(self.ai_tab, font=("Consolas", 10))
        self.ai_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Zakładka metryk
        self.metrics_tab = self.results_tabview.add("Metryki")
        self.metrics_text = ctk.CTkTextbox(self.metrics_tab, font=("Consolas", 10))
        self.metrics_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Zakładka historii
        self.history_tab = self.results_tabview.add("Historia")
        self.history_text = ctk.CTkTextbox(self.history_tab, font=("Consolas", 10))
        self.history_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Frame dla przycisku zamknij (pod panelem sugestii)
        close_button_frame = ctk.CTkFrame(suggestions_frame)
        close_button_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(5, 0))
    
        # PRZYCISK ZAMKNIJ - czerwony, wyróżniony
        self.btn_close = ctk.CTkButton(
            close_button_frame,
            text="❌ ZAMKNIJ APLIKACJĘ",
            command=self.close_application,
            width=200,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#dc3545",
            hover_color="#c82333",
            text_color="white",
            corner_radius=8
        )
        self.btn_close.pack(pady=10)
        
        # Pasek postępu
        self.progress_bar = ctk.CTkProgressBar(main_frame)
        self.progress_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.progress_bar.set(0)
        
        # Przykładowy kod
        self.load_example_code()
    
    def create_menu(self):
        """Utworzenie menu aplikacji"""
        import tkinter as tk
        
        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)
        
        # Menu Plik
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Plik", menu=file_menu)
        file_menu.add_command(label="Otwórz...", command=self.open_file)
        file_menu.add_command(label="Zapisz...", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Wyjście", command=self.root.quit)
        
        # Menu Analiza
        analyze_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analiza", menu=analyze_menu)
        analyze_menu.add_command(label="Analizuj kod", command=self.analyze_code)
        analyze_menu.add_command(label="Wyczyść wyniki", command=self.clear_results)
        
        # Menu Pomoc
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Pomoc", menu=help_menu)
        help_menu.add_command(label="O aplikacji", command=self.show_about)
    
    def update_line_numbers(self, event=None):
        """Aktualizacja numeracji linii na podstawie zawartości edytora"""
        try:
            content = self.code_editor.get("1.0", "end-1c")
            lines = content.split('\n')
            line_count = len(lines)
            
            self.line_numbers.configure(state="normal")
            self.line_numbers.delete("1.0", "end")
            
            line_numbers_text = ""
            for i in range(1, line_count + 1):
                line_numbers_text += f"{i:3d}\n"
            
            self.line_numbers.insert("1.0", line_numbers_text)
            self.line_numbers.configure(state="disabled")
            
            # Synchronizacja pozycji scrollowania
            try:
                editor_top = self.code_editor.yview()[0]
                self.line_numbers.yview_moveto(editor_top)
            except:
                pass
            
        except Exception as e:
            print(f"Błąd aktualizacji numeracji: {e}")

    def sync_scroll(self, event):
        """Synchronizacja scrollowania między edytorem a numeracją"""
        try:
            self.root.after_idle(lambda: self.line_numbers.yview_moveto(self.code_editor.yview()[0]))
        except:
            pass

    def load_example_code(self):
        """Załadowanie przykładowego kodu z aktualizacją numeracji"""
        example_code = '''def bubble_sort(arr):
    """
    Implementacja algorytmu bubble sort
    """
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

# Przykład użycia
numbers = [64, 34, 25, 12, 22, 11, 90]
print("Przed sortowaniem:", numbers)
sorted_numbers = bubble_sort(numbers.copy())
print("Po sortowaniu:", sorted_numbers)'''
        
        self.code_editor.delete("1.0", "end")
        self.code_editor.insert("1.0", example_code)
        self.update_line_numbers()
    
    def open_file(self):
        """Otwarcie pliku Python"""
        file_path = filedialog.askopenfilename(
            title="Otwórz plik Python",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.code_editor.delete("1.0", "end")
                    self.code_editor.insert("1.0", content)
                    self.update_line_numbers()
                    self.status_label.configure(text=f"Załadowano: {file_path}")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można otworzyć pliku: {str(e)}")
    
    def save_file(self):
        """Zapisanie kodu do pliku"""
        file_path = filedialog.asksaveasfilename(
            title="Zapisz plik Python",
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                content = self.code_editor.get("1.0", "end-1c")
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                    self.status_label.configure(text=f"Zapisano: {file_path}")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać pliku: {str(e)}")
    
    def clear_editor(self):
        """Wyczyszczenie edytora"""
        self.code_editor.delete("1.0", "end")
        self.update_line_numbers()
        self.clear_results()
        self.status_label.configure(text="Edytor wyczyszczony")
    
    def clear_results(self):
        """Wyczyszczenie wyników analizy"""
        self.errors_text.delete("1.0", "end")
        self.ai_text.delete("1.0", "end")
        self.metrics_text.delete("1.0", "end")
        self.progress_bar.set(0)
    
    def analyze_code(self):
        """Rozpoczęcie analizy kodu"""
        code = self.code_editor.get("1.0", "end-1c")
        
        if not code.strip():
            messagebox.showwarning("Ostrzeżenie", "Brak kodu do analizy")
            return
        
        # Uruchomienie analizy w osobnym wątku
        self.btn_analyze.configure(state="disabled", text="Analizuję...")
        self.status_label.configure(text="Trwa analiza...")
        self.progress_bar.set(0.1)
        
        # Wątek analizy
        analysis_thread = threading.Thread(target=self._run_analysis, args=(code,))
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def _run_analysis(self, code: str):
        """Uruchomienie analizy w tle"""
        try:
            # Symulacja postępu
            self.progress_bar.set(0.3)
            
            # Uruchomienie analizy
            results = self.analyzer.analyze_code(code)
            
            self.progress_bar.set(0.7)
            
            # Zapisanie wyników do bazy danych
            analysis_result = CodeAnalysisResult(
                file_name="editor_code.py",
                code_content=code,
                analysis_results=results,
                status=AnalysisStatus.COMPLETED,
                error_count=len(results.get('syntax_errors', [])) + len(results.get('static_analysis', [])),
                warning_count=len([e for e in results.get('static_analysis', []) if e.severity.value == 'warning'])
            )
            
            try:
                self.db_handler.save_analysis_result(analysis_result)
                self.db_handler.update_session_activity(self.session_id)
            except Exception as e:
                print(f"Błąd zapisu do bazy: {e}")
            
            self.progress_bar.set(1.0)
            
            # Aktualizacja GUI w głównym wątku
            self.root.after(0, self._update_results, results)
            
        except Exception as e:
            self.root.after(0, self._handle_analysis_error, str(e))
    
    def _update_results(self, results: Dict[str, Any]):
        """Aktualizacja wyników w GUI"""
        # Wyczyść poprzednie wyniki
        self.clear_results()
        
        # Błędy składniowe i statyczne
        errors_text = "=== BŁĘDY SKŁADNIOWE ===\n"
        for error in results.get('syntax_errors', []):
            errors_text += f"Linia {error.line_number}: {error.message}\n"
        
        errors_text += "\n=== ANALIZA STATYCZNA ===\n"
        for error in results.get('static_analysis', []):
            errors_text += f"Linia {error.line_number}: [{error.severity.value}] {error.message}\n"
        
        self.errors_text.insert("1.0", errors_text)
        
        # Sugestie AI
        ai_text = "=== SUGESTIE AI ===\n"
        for suggestion in results.get('ai_suggestions', []):
            if isinstance(suggestion, dict):
                ai_text += f"Linia {suggestion.get('line', 'N/A')}: {suggestion.get('message', 'N/A')}\n"
                if 'suggestion' in suggestion:
                    ai_text += f"  Sugestia: {suggestion['suggestion']}\n"
        
        ai_text += "\n=== REFAKTORYZACJA ===\n"
        for refactor in results.get('refactoring_suggestions', []):
            if isinstance(refactor, dict):
                ai_text += f"Linia {refactor.get('line', 'N/A')}: {refactor.get('message', 'N/A')}\n"
        
        self.ai_text.insert("1.0", ai_text)
        
        # Metryki
        metrics = results.get('code_metrics', {})
        metrics_text = "=== METRYKI KODU ===\n"
        metrics_text += f"Linie kodu: {metrics.get('lines_of_code', 0)}\n"
        metrics_text += f"Linie z kodem: {metrics.get('non_empty_lines', 0)}\n"
        metrics_text += f"Linie komentarzy: {metrics.get('comment_lines', 0)}\n"
        metrics_text += f"Liczba funkcji: {metrics.get('function_count', 0)}\n"
        metrics_text += f"Liczba klas: {metrics.get('class_count', 0)}\n"
        metrics_text += f"Złożoność: {metrics.get('complexity_score', 0)}\n"
        
        self.metrics_text.insert("1.0", metrics_text)
        
        # Historia
        self._update_history()
        
        # Przywróć przycisk
        self.btn_analyze.configure(state="normal", text="🔍 ANALIZUJ KOD")
        self.status_label.configure(text="Analiza zakończona")
        self.progress_bar.set(0)
    
    def _update_history(self):
        """Aktualizacja historii analiz"""
        try:
            if not self.db_handler:
                self.history_text.insert("1.0", "❌ Brak połączenia z systemem przechowywania")
                return
        
            # Pobierz informacje o systemie przechowywania
            storage_info = self.db_handler.get_storage_info()
        
            history_text = "=== INFORMACJE O SYSTEMIE PRZECHOWYWANIA ===\n"
            history_text += f"📊 Typ: {storage_info['storage_type']}\n"
        
            if storage_info['uses_mongodb']:
                history_text += f"🗃️ Baza danych: MongoDB\n"
            else:
                history_text += f"📁 Lokalne pliki: {storage_info['local_data_dir']}\n"
        
            # Pobierz statystyki
            stats = self.db_handler.get_statistics()
            history_text += f"📈 Łączna liczba analiz: {stats.get('total_analyses', 0)}\n"
            history_text += f"🔴 Łączna liczba błędów: {stats.get('total_errors', 0)}\n"
            history_text += f"⚠️ Łączna liczba ostrzeżeń: {stats.get('total_warnings', 0)}\n"
        
            history_text += "\n=== HISTORIA ANALIZ ===\n"
        
            # Pobierz historię
            history = self.db_handler.get_analysis_history(limit=10)
        
            if not history:
                history_text += "⚠️ Brak zapisanych analiz\n"
            else:
                for i, analysis in enumerate(history, 1):
                    timestamp = analysis.get('timestamp', 'N/A')
                    file_name = analysis.get('file_name', 'unknown')
                    error_count = analysis.get('error_count', 0)
                    warning_count = analysis.get('warning_count', 0)
                
                    # Formatowanie daty
                    if isinstance(timestamp, str):
                        display_time = timestamp[:19].replace('T', ' ') if len(timestamp) > 19 else timestamp
                    else:
                        display_time = str(timestamp)

                    history_text += f"{i:2d}. 📄 {file_name}\n"
                    history_text += f"    📅 {display_time}\n"
                    history_text += f"    🔴 Błędy: {error_count} | ⚠️ Ostrzeżenia: {warning_count}\n\n"
        
            # Instrukcje dla użytkownika
            history_text += "\n=== INSTRUKCJE ===\n"
            if storage_info['uses_mongodb']:
                history_text += "💡 Historia jest zapisywana w MongoDB\n"
                history_text += "🔧 Możesz przeglądać szczegóły w MongoDB Compass\n"
            else:
                history_text += "💡 Historia jest zapisywana w lokalnych plikach\n"
                history_text += f"📁 Lokalizacja: {storage_info['local_data_dir']}\n"
                history_text += "🔧 Pliki JSON można otworzyć w dowolnym edytorze tekstu\n"
        
            self.history_text.delete("1.0", "end")
            self.history_text.insert("1.0", history_text)

        except Exception as e:
            error_text = f"❌ Błąd pobierania historii: {str(e)}\n"
            self.history_text.delete("1.0", "end")
            self.history_text.insert("1.0", error_text)
    
    def _handle_analysis_error(self, error_message: str):
        """Obsługa błędu analizy"""
        self.btn_analyze.configure(state="normal", text="🔍 ANALIZUJ KOD")
        self.status_label.configure(text="Błąd analizy")
        self.progress_bar.set(0)
        messagebox.showerror("Błąd analizy", f"Wystąpił błąd podczas analizy: {error_message}")
    
    def show_about(self):
        """Wyświetlenie informacji o aplikacji"""
        about_text = """
AI Code Debugger v1.0

Aplikacja do analizy kodu Python z wykorzystaniem AI.

Funkcje:
- Analiza składniowa kodu
- Statyczna analiza kodu (pylint)
- Sugestie AI dla poprawy kodu
- Historia analiz
- Metryki kodu
- Numeracja linii kodu

Autor: Sebastian Ciborowski github.com/sebastian-c87
Assist: Własny asystent AI stworzony przez autora. - Perplexity/Claude.
Technologie: Python, OpenAI, MongoDB, CustomTkinter
"""
        messagebox.showinfo("O aplikacji", about_text)

    def close_application(self):
        """Bezpieczne zamknięcie aplikacji z potwierdzeniem"""
        result = messagebox.askyesno(
            "Potwierdzenie zamknięcia", 
            "Czy na pewno chcesz zamknąć AI Code Debugger?\n\nWszystkie niezapisane dane zostaną utracone.",
            icon='warning'
        )
    
        if result:
            try:
                self.status_label.configure(text="Zamykanie aplikacji...")
                self.root.update()
            
                # Zamknięcie połączenia z bazą danych
                if hasattr(self, 'db_handler') and self.db_handler:
                    try:
                        self.db_handler.disconnect()
                        print("✓ Połączenie z bazą danych zamknięte")
                    except Exception as e:
                        print(f"⚠️ Błąd podczas zamykania bazy danych: {e}")
            
                # Zakończenie sesji użytkownika
                if hasattr(self, 'session_id') and self.session_id != "local_session":
                    try:
                        print(f"✓ Sesja użytkownika {self.session_id} zakończona")
                    except Exception as e:
                        print(f"⚠️ Błąd podczas zamykania sesji: {e}")
            
                # Czyszczenie tymczasowych plików
                try:
                    import os
                    temp_files = ['temp_analysis.py', 'test_basic_install.py', 'test_openai.py']
                    for temp_file in temp_files:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                            print(f"✓ Usunięto tymczasowy plik: {temp_file}")
                except Exception as e:
                    print(f"⚠️ Błąd podczas czyszczenia plików: {e}")
            
                print("👋 AI Code Debugger zostaje zamknięty...")
                self.root.quit()
                self.root.destroy()
            
            except Exception as e:
                print(f"❌ Błąd podczas zamykania aplikacji: {e}")
                self.root.destroy()
        else:
            self.status_label.configure(text="Gotowy do analizy kodu")
