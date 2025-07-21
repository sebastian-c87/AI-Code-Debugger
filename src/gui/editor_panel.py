"""
Panel edytora kodu dla AI Code Debugger
Zarządza edycją kodu, podświetlaniem składni i numerowaniem linii
"""

import customtkinter as ctk
from tkinter import scrolledtext, font, messagebox
import re
from typing import Dict, List, Optional, Tuple, Callable
import threading
import time

class CodeEditor(ctk.CTkFrame):
    """Klasa panelu edytora kodu z zaawansowanymi funkcjami"""
    
    def __init__(self, parent, **kwargs):
        """
        Inicjalizacja edytora kodu
        
        Args:
            parent: Widget nadrzędny
            **kwargs: Dodatkowe argumenty dla CTkFrame
        """
        super().__init__(parent, **kwargs)
        
        # Konfiguracja edytora
        self.line_highlight_enabled = True
        self.syntax_highlighting_enabled = True
        self.auto_indent_enabled = True
        self.line_numbers_enabled = True
        
        # Kolory składni
        self.syntax_colors = {
            'keyword': '#569cd6',      # Niebieskie słowa kluczowe
            'string': '#ce9178',       # Pomarańczowe stringi
            'comment': '#6a9955',      # Zielone komentarze
            'number': '#b5cea8',       # Jasno zielone liczby
            'function': '#dcdcaa',     # Żółte funkcje
            'class': '#4ec9b0',        # Turkusowe klasy
            'error': '#f44747'         # Czerwone błędy
        }
        
        # Słowa kluczowe Python
        self.python_keywords = {
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'exec', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
            'not', 'or', 'pass', 'print', 'raise', 'return', 'try',
            'while', 'with', 'yield', 'True', 'False', 'None'
        }
        
        # Builtins Python
        self.python_builtins = {
            'abs', 'all', 'any', 'bin', 'bool', 'chr', 'dict', 'dir',
            'enumerate', 'filter', 'float', 'format', 'frozenset',
            'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex',
            'id', 'input', 'int', 'isinstance', 'issubclass', 'iter',
            'len', 'list', 'locals', 'map', 'max', 'min', 'next',
            'object', 'oct', 'open', 'ord', 'pow', 'range', 'repr',
            'reversed', 'round', 'set', 'setattr', 'slice', 'sorted',
            'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'
        }
        
        # Callback funkcje
        self.on_text_change: Optional[Callable] = None
        self.on_line_change: Optional[Callable] = None
        
        # Utworzenie widgetów
        self.create_widgets()
        self.setup_bindings()
        
        # Inicjalizacja podświetlania
        if self.syntax_highlighting_enabled:
            self.setup_syntax_highlighting()
    
    def create_widgets(self):
        """Utworzenie widgetów edytora"""
        # Konfiguracja grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Frame dla numerów linii
        if self.line_numbers_enabled:
            self.line_numbers_frame = ctk.CTkFrame(self, width=50)
            self.line_numbers_frame.grid(row=0, column=0, sticky="ns", padx=(0, 2))
            self.line_numbers_frame.grid_propagate(False)
            
            # Text widget dla numerów linii
            self.line_numbers_text = ctk.CTkTextbox(
                self.line_numbers_frame,
                width=45,
                font=("Consolas", 11),
                state="disabled",
                wrap="none"
            )
            self.line_numbers_text.pack(fill="both", expand=True)
        
        # Frame dla głównego edytora
        self.editor_frame = ctk.CTkFrame(self)
        self.editor_frame.grid(row=0, column=1, sticky="nsew")
        self.editor_frame.grid_columnconfigure(0, weight=1)
        self.editor_frame.grid_rowconfigure(0, weight=1)
        
        # Główny text widget
        self.text_widget = ctk.CTkTextbox(
            self.editor_frame,
            font=("Consolas", 12),
            wrap="none",
            undo=True,
            maxundo=50
        )
        self.text_widget.grid(row=0, column=0, sticky="nsew")
        
        # Pasek statusu
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        
        # Informacje o pozycji kursora
        self.cursor_position_label = ctk.CTkLabel(
            self.status_frame,
            text="Linia: 1, Kolumna: 1",
            font=("Arial", 10)
        )
        self.cursor_position_label.pack(side="left", padx=5)
        
        # Informacje o trybie edycji
        self.mode_label = ctk.CTkLabel(
            self.status_frame,
            text="Tryb: Edycja",
            font=("Arial", 10)
        )
        self.mode_label.pack(side="right", padx=5)
        
        # Licznik znaków
        self.char_count_label = ctk.CTkLabel(
            self.status_frame,
            text="Znaków: 0",
            font=("Arial", 10)
        )
        self.char_count_label.pack(side="right", padx=5)
    
    def setup_bindings(self):
        """Konfiguracja bindingów klawiatury i myszy"""
        # Binding dla zmian tekstu
        self.text_widget.bind('<KeyRelease>', self.on_text_modified)
        self.text_widget.bind('<Button-1>', self.on_cursor_moved)
        self.text_widget.bind('<KeyPress>', self.on_key_press)
        
        # Binding dla scrollowania
        self.text_widget.bind('<MouseWheel>', self.on_mouse_wheel)
        
        # Binding dla Enter (auto-indent)
        self.text_widget.bind('<Return>', self.on_enter_key)
        
        # Binding dla Tab (wcięcia)
        self.text_widget.bind('<Tab>', self.on_tab_key)
        self.text_widget.bind('<Shift-Tab>', self.on_shift_tab_key)
        
        # Binding dla Ctrl+/ (komentowanie)
        self.text_widget.bind('<Control-slash>', self.toggle_comment)
        
        # Binding dla Ctrl+D (duplikowanie linii)
        self.text_widget.bind('<Control-d>', self.duplicate_line)
        
        # Binding dla Ctrl+L (przejście do linii)
        self.text_widget.bind('<Control-l>', self.goto_line)
    
    def setup_syntax_highlighting(self):
        """Konfiguracja podświetlania składni"""
        # Definicja tagów dla różnych elementów składni
        self.text_widget.tag_configure("keyword", foreground=self.syntax_colors['keyword'])
        self.text_widget.tag_configure("string", foreground=self.syntax_colors['string'])
        self.text_widget.tag_configure("comment", foreground=self.syntax_colors['comment'])
        self.text_widget.tag_configure("number", foreground=self.syntax_colors['number'])
        self.text_widget.tag_configure("function", foreground=self.syntax_colors['function'])
        self.text_widget.tag_configure("class", foreground=self.syntax_colors['class'])
        self.text_widget.tag_configure("error", foreground=self.syntax_colors['error'])
        
        # Tag dla podświetlania bieżącej linii
        self.text_widget.tag_configure("current_line", background="#2d2d30")
    
    def on_text_modified(self, event=None):
        """Obsługa zmiany tekstu"""
        # Aktualizacja numerów linii
        if self.line_numbers_enabled:
            self.update_line_numbers()
        
        # Aktualizacja podświetlania składni
        if self.syntax_highlighting_enabled:
            self.update_syntax_highlighting()
        
        # Aktualizacja pozycji kursora
        self.update_cursor_position()
        
        # Aktualizacja licznika znaków
        self.update_char_count()
        
        # Podświetlenie bieżącej linii
        if self.line_highlight_enabled:
            self.highlight_current_line()
        
        # Wywołanie callback funkcji
        if self.on_text_change:
            self.on_text_change()
    
    def on_cursor_moved(self, event=None):
        """Obsługa ruchu kursora"""
        self.update_cursor_position()
        
        if self.line_highlight_enabled:
            self.highlight_current_line()
        
        if self.on_line_change:
            self.on_line_change()
    
    def on_key_press(self, event):
        """Obsługa naciśnięcia klawisza"""
        # Auto-uzupełnianie nawiasów
        if event.char in '([{':
            self.auto_complete_brackets(event.char)
        elif event.char in ')]}':
            self.handle_closing_bracket(event.char)
    
    def on_mouse_wheel(self, event):
        """Obsługa scrollowania myszą"""
        if self.line_numbers_enabled:
            # Synchronizacja scrollowania numerów linii
            self.line_numbers_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_enter_key(self, event):
        """Obsługa klawisza Enter z auto-wcięciem"""
        if not self.auto_indent_enabled:
            return
        
        # Pobieranie bieżącej linii
        current_line = self.get_current_line()
        
        # Obliczanie wcięcia
        indent = self.calculate_indent(current_line)
        
        # Wstawianie nowej linii z wcięciem
        self.text_widget.insert("insert", f"\n{indent}")
        
        return "break"  # Zapobiega domyślnej obsłudze Enter
    
    def on_tab_key(self, event):
        """Obsługa klawisza Tab"""
        # Wstawianie 4 spacji zamiast tabulatora
        self.text_widget.insert("insert", "    ")
        return "break"
    
    def on_shift_tab_key(self, event):
        """Obsługa Shift+Tab (zmniejszenie wcięcia)"""
        current_line = self.get_current_line()
        
        if current_line.startswith("    "):
            # Usunięcie 4 spacji z początku linii
            line_start = self.text_widget.index("insert linestart")
            line_end = self.text_widget.index("insert linestart + 4c")
            self.text_widget.delete(line_start, line_end)
        
        return "break"
    
    def toggle_comment(self, event):
        """Przełączanie komentarza w linii"""
        current_line = self.get_current_line()
        line_start = self.text_widget.index("insert linestart")
        line_end = self.text_widget.index("insert lineend")
        
        if current_line.strip().startswith("#"):
            # Usunięcie komentarza
            new_line = current_line.replace("#", "", 1).lstrip()
            self.text_widget.delete(line_start, line_end)
            self.text_widget.insert(line_start, new_line)
        else:
            # Dodanie komentarza
            indent = len(current_line) - len(current_line.lstrip())
            new_line = current_line[:indent] + "# " + current_line[indent:]
            self.text_widget.delete(line_start, line_end)
            self.text_widget.insert(line_start, new_line)
        
        return "break"
    
    def duplicate_line(self, event):
        """Duplikowanie bieżącej linii"""
        current_line = self.get_current_line()
        line_end = self.text_widget.index("insert lineend")
        self.text_widget.insert(line_end, f"\n{current_line}")
        return "break"
    
    def goto_line(self, event):
        """Przejście do określonej linii"""
        dialog = ctk.CTkInputDialog(
            text="Podaj numer linii:",
            title="Przejdź do linii"
        )
        
        line_number = dialog.get_input()
        
        if line_number and line_number.isdigit():
            line_num = int(line_number)
            self.text_widget.mark_set("insert", f"{line_num}.0")
            self.text_widget.see("insert")
            self.highlight_current_line()
        
        return "break"
    
    def update_line_numbers(self):
        """Aktualizacja numerów linii"""
        if not self.line_numbers_enabled:
            return
        
        # Pobieranie liczby linii
        line_count = int(self.text_widget.index("end-1c").split('.')[0])
        
        # Generowanie numerów linii
        line_numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        
        # Aktualizacja text widget numerów linii
        self.line_numbers_text.configure(state="normal")
        self.line_numbers_text.delete("1.0", "end")
        self.line_numbers_text.insert("1.0", line_numbers)
        self.line_numbers_text.configure(state="disabled")
    
    def update_syntax_highlighting(self):
        """Aktualizacja podświetlania składni"""
        if not self.syntax_highlighting_enabled:
            return
        
        # Usunięcie poprzednich tagów
        for tag in ["keyword", "string", "comment", "number", "function", "class"]:
            self.text_widget.tag_remove(tag, "1.0", "end")
        
        content = self.text_widget.get("1.0", "end-1c")
        
        # Podświetlanie komentarzy
        self.highlight_pattern(r"#.*$", "comment")
        
        # Podświetlanie stringów
        self.highlight_pattern(r'"[^"]*"', "string")
        self.highlight_pattern(r"'[^']*'", "string")
        self.highlight_pattern(r'""".*?"""', "string")
        self.highlight_pattern(r"'''.*?'''", "string")
        
        # Podświetlanie liczb
        self.highlight_pattern(r"\b\d+\.?\d*\b", "number")
        
        # Podświetlanie słów kluczowych
        for keyword in self.python_keywords:
            self.highlight_pattern(rf"\b{keyword}\b", "keyword")
        
        # Podświetlanie builtins
        for builtin in self.python_builtins:
            self.highlight_pattern(rf"\b{builtin}\b", "function")
        
        # Podświetlanie nazw klas
        self.highlight_pattern(r"\bclass\s+(\w+)", "class")
        
        # Podświetlanie nazw funkcji
        self.highlight_pattern(r"\bdef\s+(\w+)", "function")
    
    def highlight_pattern(self, pattern: str, tag: str):
        """Podświetlanie wzorca w tekście"""
        content = self.text_widget.get("1.0", "end-1c")
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            start_pos = self.text_widget.index(f"1.0 + {match.start()}c")
            end_pos = self.text_widget.index(f"1.0 + {match.end()}c")
            self.text_widget.tag_add(tag, start_pos, end_pos)
    
    def highlight_current_line(self):
        """Podświetlanie bieżącej linii"""
        # Usunięcie poprzedniego podświetlenia
        self.text_widget.tag_remove("current_line", "1.0", "end")
        
        # Podświetlenie bieżącej linii
        current_line = self.text_widget.index("insert").split('.')[0]
        line_start = f"{current_line}.0"
        line_end = f"{current_line}.end"
        self.text_widget.tag_add("current_line", line_start, line_end)
    
    def update_cursor_position(self):
        """Aktualizacja pozycji kursora"""
        cursor_pos = self.text_widget.index("insert")
        line, column = cursor_pos.split('.')
        self.cursor_position_label.configure(text=f"Linia: {line}, Kolumna: {int(column) + 1}")
    
    def update_char_count(self):
        """Aktualizacja licznika znaków"""
        content = self.text_widget.get("1.0", "end-1c")
        char_count = len(content)
        self.char_count_label.configure(text=f"Znaków: {char_count}")
    
    def get_current_line(self) -> str:
        """Pobieranie tekstu bieżącej linii"""
        line_start = self.text_widget.index("insert linestart")
        line_end = self.text_widget.index("insert lineend")
        return self.text_widget.get(line_start, line_end)
    
    def calculate_indent(self, line: str) -> str:
        """Obliczanie wcięcia dla nowej linii"""
        # Podstawowe wcięcie
        indent = ""
        for char in line:
            if char == ' ':
                indent += char
            else:
                break
        
        # Dodatkowe wcięcie dla dwukropka
        if line.strip().endswith(':'):
            indent += "    "
        
        return indent
    
    def auto_complete_brackets(self, bracket: str):
        """Auto-uzupełnianie nawiasów"""
        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        closing_bracket = bracket_pairs.get(bracket)
        
        if closing_bracket:
            current_pos = self.text_widget.index("insert")
            self.text_widget.insert("insert", closing_bracket)
            self.text_widget.mark_set("insert", current_pos)
    
    def handle_closing_bracket(self, bracket: str):
        """Obsługa zamykającego nawiasu"""
        current_pos = self.text_widget.index("insert")
        next_char = self.text_widget.get(current_pos, f"{current_pos} + 1c")
        
        if next_char == bracket:
            # Przesuń kursor za nawias zamiast wstawiania nowego
            self.text_widget.mark_set("insert", f"{current_pos} + 1c")
            return "break"
    
    def set_content(self, content: str):
        """Ustawienie zawartości edytora"""
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", content)
        self.on_text_modified()
    
    def get_content(self) -> str:
        """Pobieranie zawartości edytora"""
        return self.text_widget.get("1.0", "end-1c")
    
    def clear_content(self):
        """Wyczyszczenie zawartości edytora"""
        self.text_widget.delete("1.0", "end")
        self.on_text_modified()
    
    def highlight_error_line(self, line_number: int):
        """Podświetlanie linii z błędem"""
        line_start = f"{line_number}.0"
        line_end = f"{line_number}.end"
        self.text_widget.tag_add("error", line_start, line_end)
    
    def clear_error_highlights(self):
        """Usunięcie podświetlenia błędów"""
        self.text_widget.tag_remove("error", "1.0", "end")
    
    def find_text(self, search_text: str, case_sensitive: bool = False) -> List[Tuple[str, str]]:
        """Wyszukiwanie tekstu w edytorze"""
        content = self.get_content()
        matches = []
        
        if not case_sensitive:
            content = content.lower()
            search_text = search_text.lower()
        
        start = 0
        while True:
            pos = content.find(search_text, start)
            if pos == -1:
                break
            
            # Konwersja pozycji na indeks tekstu
            lines_before = content[:pos].count('\n')
            line_start = content.rfind('\n', 0, pos) + 1
            column = pos - line_start
            
            start_index = f"{lines_before + 1}.{column}"
            end_index = f"{lines_before + 1}.{column + len(search_text)}"
            
            matches.append((start_index, end_index))
            start = pos + 1
        
        return matches
    
    def replace_text(self, search_text: str, replace_text: str, case_sensitive: bool = False):
        """Zamiana tekstu w edytorze"""
        content = self.get_content()
        
        if not case_sensitive:
            # Zamiana z zachowaniem wielkości liter
            import re
            pattern = re.compile(re.escape(search_text), re.IGNORECASE)
            new_content = pattern.sub(replace_text, content)
        else:
            new_content = content.replace(search_text, replace_text)
        
        self.set_content(new_content)
    
    def set_callbacks(self, on_text_change: Optional[Callable] = None, 
                     on_line_change: Optional[Callable] = None):
        """Ustawienie callback funkcji"""
        self.on_text_change = on_text_change
        self.on_line_change = on_line_change
    
    def get_line_count(self) -> int:
        """Pobieranie liczby linii"""
        return int(self.text_widget.index("end-1c").split('.')[0])
    
    def get_selected_text(self) -> str:
        """Pobieranie zaznaczonego tekstu"""
        try:
            return self.text_widget.selection_get()
        except:
            return ""
    
    def insert_text_at_cursor(self, text: str):
        """Wstawianie tekstu w pozycji kursora"""
        self.text_widget.insert("insert", text)
        self.on_text_modified()
