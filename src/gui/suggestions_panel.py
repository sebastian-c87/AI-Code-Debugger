"""
Panel sugestii i wyników analizy dla AI Code Debugger
"""

import customtkinter as ctk
from tkinter import ttk
from typing import Dict, List, Any, Optional
from ..core.error_classifier import ClassifiedError, ErrorCategory, ErrorPriority
from ..database.models import CodeAnalysisResult

class SuggestionsPanel(ctk.CTkFrame):
    """Panel wyświetlający sugestie i wyniki analizy kodu"""
    
    def __init__(self, parent, **kwargs):
        """
        Inicjalizacja panelu sugestii
        
        Args:
            parent: Widget nadrzędny
            **kwargs: Dodatkowe argumenty dla CTkFrame
        """
        super().__init__(parent, **kwargs)
        
        self.current_results: Optional[Dict[str, Any]] = None
        self.classified_errors: List[ClassifiedError] = []
        
        self.create_widgets()
        self.setup_layout()
    
    def create_widgets(self):
        """Utworzenie widgetów panelu"""
        # Nagłówek
        self.header_label = ctk.CTkLabel(
            self, 
            text="Wyniki Analizy Kodu", 
            font=("Arial", 16, "bold")
        )
        
        # Zakładki dla różnych typów wyników
        self.tab_view = ctk.CTkTabview(self)
        
        # Zakładka błędów
        self.errors_tab = self.tab_view.add("Błędy")
        self.create_errors_tab()
        
        # Zakładka sugestii AI
        self.ai_tab = self.tab_view.add("Sugestie AI")
        self.create_ai_tab()
        
        # Zakładka metryk
        self.metrics_tab = self.tab_view.add("Metryki")
        self.create_metrics_tab()
        
        # Zakładka historii
        self.history_tab = self.tab_view.add("Historia")
        self.create_history_tab()
        
        # Pasek narzędzi
        self.toolbar = ctk.CTkFrame(self)
        self.create_toolbar()
        
        # Pasek statusu
        self.status_bar = ctk.CTkFrame(self)
        self.create_status_bar()
    
    def create_errors_tab(self):
        """Utworzenie zakładki błędów"""
        # Frame dla filtrów
        self.errors_filter_frame = ctk.CTkFrame(self.errors_tab)
        
        # Filtry
        self.severity_filter = ctk.CTkComboBox(
            self.errors_filter_frame,
            values=["Wszystkie", "Krytyczne", "Błędy", "Ostrzeżenia", "Info"],
            command=self.filter_errors
        )
        
        self.category_filter = ctk.CTkComboBox(
            self.errors_filter_frame,
            values=["Wszystkie", "Składnia", "Logika", "Styl", "Wydajność", "Bezpieczeństwo"],
            command=self.filter_errors
        )
        
        # Lista błędów
        self.errors_tree = ttk.Treeview(
            self.errors_tab,
            columns=("line", "severity", "category", "message"),
            show="headings",
            height=15
        )
        
        # Nagłówki kolumn
        self.errors_tree.heading("line", text="Linia")
        self.errors_tree.heading("severity", text="Poziom")
        self.errors_tree.heading("category", text="Kategoria")
        self.errors_tree.heading("message", text="Opis")
        
        # Szerokość kolumn
        self.errors_tree.column("line", width=60)
        self.errors_tree.column("severity", width=80)
        self.errors_tree.column("category", width=100)
        self.errors_tree.column("message", width=300)
        
        # Scrollbar dla listy błędów
        self.errors_scrollbar = ctk.CTkScrollbar(
            self.errors_tab,
            command=self.errors_tree.yview
        )
        self.errors_tree.configure(yscrollcommand=self.errors_scrollbar.set)
        
        # Panel szczegółów błędu
        self.error_details_frame = ctk.CTkFrame(self.errors_tab)
        self.error_details_text = ctk.CTkTextbox(
            self.error_details_frame,
            height=100,
            font=("Consolas", 10)
        )
        
        # Binding dla selekcji błędu
        self.errors_tree.bind("<<TreeviewSelect>>", self.on_error_select)
    
    def create_ai_tab(self):
        """Utworzenie zakładki sugestii AI"""
        # Panel sugestii
        self.ai_suggestions_frame = ctk.CTkFrame(self.ai_tab)
        
        # Nagłówek sugestii
        self.ai_header = ctk.CTkLabel(
            self.ai_suggestions_frame,
            text="Sugestie Poprawy Kodu",
            font=("Arial", 14, "bold")
        )
        
        # Text widget dla sugestii
        self.ai_suggestions_text = ctk.CTkTextbox(
            self.ai_suggestions_frame,
            font=("Consolas", 10),
            height=200
        )
        
        # Panel refaktoryzacji
        self.refactor_frame = ctk.CTkFrame(self.ai_tab)
        
        # Nagłówek refaktoryzacji
        self.refactor_header = ctk.CTkLabel(
            self.refactor_frame,
            text="Sugestie Refaktoryzacji",
            font=("Arial", 14, "bold")
        )
        
        # Text widget dla refaktoryzacji
        self.refactor_text = ctk.CTkTextbox(
            self.refactor_frame,
            font=("Consolas", 10),
            height=200
        )
        
        # Przyciski akcji
        self.ai_actions_frame = ctk.CTkFrame(self.ai_tab)
        
        self.regenerate_btn = ctk.CTkButton(
            self.ai_actions_frame,
            text="Regeneruj Sugestie",
            command=self.regenerate_suggestions
        )
        
        self.apply_suggestion_btn = ctk.CTkButton(
            self.ai_actions_frame,
            text="Zastosuj Sugestię",
            command=self.apply_suggestion
        )
    
    def create_metrics_tab(self):
        """Utworzenie zakładki metryk"""
        # Frame dla metryk podstawowych
        self.basic_metrics_frame = ctk.CTkFrame(self.metrics_tab)
        
        # Metryki podstawowe
        self.lines_count_label = ctk.CTkLabel(
            self.basic_metrics_frame,
            text="Linie kodu: -",
            font=("Arial", 12)
        )
        
        self.functions_count_label = ctk.CTkLabel(
            self.basic_metrics_frame,
            text="Funkcje: -",
            font=("Arial", 12)
        )
        
        self.classes_count_label = ctk.CTkLabel(
            self.basic_metrics_frame,
            text="Klasy: -",
            font=("Arial", 12)
        )
        
        self.complexity_label = ctk.CTkLabel(
            self.basic_metrics_frame,
            text="Złożoność: -",
            font=("Arial", 12)
        )
        
        # Frame dla metryk jakości
        self.quality_metrics_frame = ctk.CTkFrame(self.metrics_tab)
        
        # Metryki jakości
        self.errors_count_label = ctk.CTkLabel(
            self.quality_metrics_frame,
            text="Błędy: -",
            font=("Arial", 12)
        )
        
        self.warnings_count_label = ctk.CTkLabel(
            self.quality_metrics_frame,
            text="Ostrzeżenia: -",
            font=("Arial", 12)
        )
        
        self.code_quality_label = ctk.CTkLabel(
            self.quality_metrics_frame,
            text="Jakość kodu: -",
            font=("Arial", 12)
        )
        
        # Progress bar dla jakości
        self.quality_progress = ctk.CTkProgressBar(self.quality_metrics_frame)
        
        # Wykres metryk (placeholder)
        self.metrics_chart_frame = ctk.CTkFrame(self.metrics_tab)
        self.metrics_chart_label = ctk.CTkLabel(
            self.metrics_chart_frame,
            text="Wykres metryk będzie tutaj",
            font=("Arial", 10)
        )
    
    def create_history_tab(self):
        """Utworzenie zakładki historii"""
        # Lista historii
        self.history_tree = ttk.Treeview(
            self.history_tab,
            columns=("date", "filename", "errors", "warnings", "status"),
            show="headings",
            height=15
        )
        
        # Nagłówki kolumn
        self.history_tree.heading("date", text="Data")
        self.history_tree.heading("filename", text="Plik")
        self.history_tree.heading("errors", text="Błędy")
        self.history_tree.heading("warnings", text="Ostrzeżenia")
        self.history_tree.heading("status", text="Status")
        
        # Szerokość kolumn
        self.history_tree.column("date", width=120)
        self.history_tree.column("filename", width=150)
        self.history_tree.column("errors", width=60)
        self.history_tree.column("warnings", width=80)
        self.history_tree.column("status", width=80)
        
        # Scrollbar dla historii
        self.history_scrollbar = ctk.CTkScrollbar(
            self.history_tab,
            command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=self.history_scrollbar.set)
        
        # Przyciski akcji historii
        self.history_actions_frame = ctk.CTkFrame(self.history_tab)
        
        self.refresh_history_btn = ctk.CTkButton(
            self.history_actions_frame,
            text="Odśwież",
            command=self.refresh_history
        )
        
        self.clear_history_btn = ctk.CTkButton(
            self.history_actions_frame,
            text="Wyczyść Historię",
            command=self.clear_history
        )
        
        self.export_history_btn = ctk.CTkButton(
            self.history_actions_frame,
            text="Eksportuj",
            command=self.export_history
        )
        
        # Binding dla selekcji historii
        self.history_tree.bind("<<TreeviewSelect>>", self.on_history_select)
    
    def create_toolbar(self):
        """Utworzenie paska narzędzi"""
        # Przycisk eksportu wyników
        self.export_btn = ctk.CTkButton(
            self.toolbar,
            text="Eksportuj Wyniki",
            command=self.export_results,
            width=120
        )
        
        # Przycisk filtrowania
        self.filter_btn = ctk.CTkButton(
            self.toolbar,
            text="Filtry",
            command=self.toggle_filters,
            width=80
        )
        
        # Przycisk ustawień
        self.settings_btn = ctk.CTkButton(
            self.toolbar,
            text="Ustawienia",
            command=self.open_settings,
            width=100
        )
    
    def create_status_bar(self):
        """Utworzenie paska statusu"""
        # Licznik wyników
        self.results_count_label = ctk.CTkLabel(
            self.status_bar,
            text="Wyniki: 0",
            font=("Arial", 10)
        )
        
        # Status analizy
        self.analysis_status_label = ctk.CTkLabel(
            self.status_bar,
            text="Gotowy",
            font=("Arial", 10)
        )
        
        # Czas wykonania
        self.execution_time_label = ctk.CTkLabel(
            self.status_bar,
            text="Czas: 0.0s",
            font=("Arial", 10)
        )
    
    def setup_layout(self):
        """Konfiguracja layoutu"""
        # Konfiguracja grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Pozycjonowanie głównych elementów
        self.header_label.grid(row=0, column=0, pady=5, sticky="ew")
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.toolbar.grid(row=2, column=0, sticky="ew", padx=5, pady=2)
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=5, pady=2)
        
        # Layout zakładki błędów
        self.errors_filter_frame.pack(fill="x", padx=5, pady=5)
        self.severity_filter.pack(side="left", padx=5)
        self.category_filter.pack(side="left", padx=5)
        
        self.errors_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.errors_scrollbar.pack(side="right", fill="y")
        
        self.error_details_frame.pack(fill="x", padx=5, pady=5)
        self.error_details_text.pack(fill="both", expand=True)
        
        # Layout zakładki AI
        self.ai_suggestions_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.ai_header.pack(pady=5)
        self.ai_suggestions_text.pack(fill="both", expand=True)
        
        self.refactor_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.refactor_header.pack(pady=5)
        self.refactor_text.pack(fill="both", expand=True)
        
        self.ai_actions_frame.pack(fill="x", padx=5, pady=5)
        self.regenerate_btn.pack(side="left", padx=5)
        self.apply_suggestion_btn.pack(side="left", padx=5)
        
        # Layout zakładki metryk
        self.basic_metrics_frame.pack(fill="x", padx=5, pady=5)
        self.lines_count_label.pack(anchor="w", padx=10, pady=2)
        self.functions_count_label.pack(anchor="w", padx=10, pady=2)
        self.classes_count_label.pack(anchor="w", padx=10, pady=2)
        self.complexity_label.pack(anchor="w", padx=10, pady=2)
        
        self.quality_metrics_frame.pack(fill="x", padx=5, pady=5)
        self.errors_count_label.pack(anchor="w", padx=10, pady=2)
        self.warnings_count_label.pack(anchor="w", padx=10, pady=2)
        self.code_quality_label.pack(anchor="w", padx=10, pady=2)
        self.quality_progress.pack(fill="x", padx=10, pady=5)
        
        self.metrics_chart_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.metrics_chart_label.pack(expand=True)
        
        # Layout zakładki historii
        self.history_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.history_scrollbar.pack(side="right", fill="y")
        
        self.history_actions_frame.pack(fill="x", padx=5, pady=5)
        self.refresh_history_btn.pack(side="left", padx=5)
        self.clear_history_btn.pack(side="left", padx=5)
        self.export_history_btn.pack(side="left", padx=5)
        
        # Layout toolbar
        self.export_btn.pack(side="left", padx=5)
        self.filter_btn.pack(side="left", padx=5)
        self.settings_btn.pack(side="right", padx=5)
        
        # Layout status bar
        self.results_count_label.pack(side="left", padx=5)
        self.analysis_status_label.pack(side="right", padx=5)
        self.execution_time_label.pack(side="right", padx=5)
    
    def update_results(self, results: Dict[str, Any]):
        """
        Aktualizacja wyników analizy
        
        Args:
            results (Dict[str, Any]): Wyniki analizy kodu
        """
        self.current_results = results
        
        # Aktualizacja zakładki błędów
        self.update_errors_tab(results)
        
        # Aktualizacja zakładki AI
        self.update_ai_tab(results)
        
        # Aktualizacja zakładki metryk
        self.update_metrics_tab(results)
        
        # Aktualizacja paska statusu
        self.update_status_bar(results)
    
    def update_errors_tab(self, results: Dict[str, Any]):
        """Aktualizacja zakładki błędów"""
        # Wyczyszczenie poprzednich wyników
        for item in self.errors_tree.get_children():
            self.errors_tree.delete(item)
        
        # Dodanie błędów składniowych
        for error in results.get('syntax_errors', []):
            self.errors_tree.insert("", "end", values=(
                error.line_number,
                error.severity.value,
                "Składnia",
                error.message
            ))
        
        # Dodanie błędów statycznych
        for error in results.get('static_analysis', []):
            self.errors_tree.insert("", "end", values=(
                error.line_number,
                error.severity.value,
                "Statyczna",
                error.message
            ))
        
        # Aktualizacja licznika błędów
        total_errors = len(results.get('syntax_errors', [])) + len(results.get('static_analysis', []))
        self.results_count_label.configure(text=f"Błędy: {total_errors}")
    
    def update_ai_tab(self, results: Dict[str, Any]):
        """Aktualizacja zakładki AI"""
        # Wyczyszczenie poprzednich sugestii
        self.ai_suggestions_text.delete("0.0", "end")
        self.refactor_text.delete("0.0", "end")
        
        # Dodanie sugestii AI
        suggestions_text = "=== SUGESTIE AI ===\n\n"
        for suggestion in results.get('ai_suggestions', []):
            if isinstance(suggestion, dict):
                suggestions_text += f"Linia {suggestion.get('line', 'N/A')}: {suggestion.get('message', 'N/A')}\n"
                if 'suggestion' in suggestion:
                    suggestions_text += f"  💡 Sugestia: {suggestion['suggestion']}\n\n"
        
        self.ai_suggestions_text.insert("0.0", suggestions_text)
        
        # Dodanie sugestii refaktoryzacji
        refactor_text = "=== REFAKTORYZACJA ===\n\n"
        for refactor in results.get('refactoring_suggestions', []):
            if isinstance(refactor, dict):
                refactor_text += f"Linia {refactor.get('line', 'N/A')}: {refactor.get('message', 'N/A')}\n"
                if 'suggestion' in refactor:
                    refactor_text += f"  🔄 Refaktor: {refactor['suggestion']}\n\n"
        
        self.refactor_text.insert("0.0", refactor_text)
    
    def update_metrics_tab(self, results: Dict[str, Any]):
        """Aktualizacja zakładki metryk"""
        metrics = results.get('code_metrics', {})
        
        # Metryki podstawowe
        self.lines_count_label.configure(text=f"Linie kodu: {metrics.get('lines_of_code', 0)}")
        self.functions_count_label.configure(text=f"Funkcje: {metrics.get('function_count', 0)}")
        self.classes_count_label.configure(text=f"Klasy: {metrics.get('class_count', 0)}")
        self.complexity_label.configure(text=f"Złożoność: {metrics.get('complexity_score', 0)}")
        
        # Metryki jakości
        error_count = len(results.get('syntax_errors', [])) + len(results.get('static_analysis', []))
        warning_count = len([e for e in results.get('static_analysis', []) if hasattr(e, 'severity') and e.severity.value == 'warning'])
        
        self.errors_count_label.configure(text=f"Błędy: {error_count}")
        self.warnings_count_label.configure(text=f"Ostrzeżenia: {warning_count}")
        
        # Obliczanie jakości kodu (0-100%)
        total_lines = metrics.get('lines_of_code', 1)
        quality_score = max(0, min(100, 100 - (error_count * 10) - (warning_count * 5)))
        
        self.code_quality_label.configure(text=f"Jakość kodu: {quality_score}%")
        self.quality_progress.set(quality_score / 100)
    
    def update_status_bar(self, results: Dict[str, Any]):
        """Aktualizacja paska statusu"""
        # Licznik wyników
        total_issues = len(results.get('syntax_errors', [])) + len(results.get('static_analysis', []))
        self.results_count_label.configure(text=f"Wyniki: {total_issues}")
        
        # Status analizy
        status = results.get('status', 'unknown')
        self.analysis_status_label.configure(text=f"Status: {status}")
        
        # Czas wykonania (jeśli dostępny)
        if 'execution_time' in results:
            self.execution_time_label.configure(text=f"Czas: {results['execution_time']:.2f}s")
    
    def on_error_select(self, event):
        """Obsługa selekcji błędu"""
        selection = self.errors_tree.selection()
        if selection:
            item = self.errors_tree.item(selection[0])
            values = item['values']
            
            # Wyświetlenie szczegółów błędu
            details = f"Linia: {values[0]}\n"
            details += f"Poziom: {values[1]}\n"
            details += f"Kategoria: {values[2]}\n"
            details += f"Opis: {values[3]}\n"
            
            self.error_details_text.delete("0.0", "end")
            self.error_details_text.insert("0.0", details)
    
    def on_history_select(self, event):
        """Obsługa selekcji historii"""
        selection = self.history_tree.selection()
        if selection:
            item = self.history_tree.item(selection[0])
            # Tutaj można załadować szczegóły analizy z historii
            pass
    
    def filter_errors(self, event=None):
        """Filtrowanie błędów"""
        # Implementacja filtrowania błędów
        pass
    
    def regenerate_suggestions(self):
        """Regenerowanie sugestii AI"""
        # Implementacja regeneracji sugestii
        pass
    
    def apply_suggestion(self):
        """Zastosowanie sugestii"""
        # Implementacja zastosowania sugestii
        pass
    
    def refresh_history(self):
        """Odświeżenie historii"""
        # Implementacja odświeżenia historii
        pass
    
    def clear_history(self):
        """Wyczyszczenie historii"""
        # Implementacja wyczyszczenia historii
        pass
    
    def export_history(self):
        """Eksport historii"""
        # Implementacja eksportu historii
        pass
    
    def export_results(self):
        """Eksport wyników"""
        # Implementacja eksportu wyników
        pass
    
    def toggle_filters(self):
        """Przełączenie filtrów"""
        # Implementacja przełączenia filtrów
        pass
    
    def open_settings(self):
        """Otwarcie ustawień"""
        # Implementacja otwarcia ustawień
        pass
    
    def clear_results(self):
        """Wyczyszczenie wszystkich wyników"""
        # Wyczyszczenie błędów
        for item in self.errors_tree.get_children():
            self.errors_tree.delete(item)
        
        # Wyczyszczenie sugestii AI
        self.ai_suggestions_text.delete("0.0", "end")
        self.refactor_text.delete("0.0", "end")
        
        # Wyczyszczenie metryk
        self.lines_count_label.configure(text="Linie kodu: -")
        self.functions_count_label.configure(text="Funkcje: -")
        self.classes_count_label.configure(text="Klasy: -")
        self.complexity_label.configure(text="Złożoność: -")
        self.errors_count_label.configure(text="Błędy: -")
        self.warnings_count_label.configure(text="Ostrzeżenia: -")
        self.code_quality_label.configure(text="Jakość kodu: -")
        self.quality_progress.set(0)
        
        # Wyczyszczenie szczegółów błędu
        self.error_details_text.delete("0.0", "end")
        
        # Reset paska statusu
        self.results_count_label.configure(text="Wyniki: 0")
        self.analysis_status_label.configure(text="Gotowy")
        self.execution_time_label.configure(text="Czas: 0.0s")
