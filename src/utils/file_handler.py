"""
Moduł obsługi plików dla AI Code Debugger
Zarządza operacjami na plikach Python
"""

import os
import glob
from typing import List, Dict, Optional, Tuple
import ast
import chardet
from pathlib import Path

class FileHandler:
    """Klasa obsługująca operacje na plikach Python"""
    
    def __init__(self):
        """Inicjalizacja handlera plików"""
        self.supported_extensions = ['.py', '.pyw']
        self.encoding_fallbacks = ['utf-8', 'cp1252', 'iso-8859-1']
    
    def read_file(self, file_path: str) -> Optional[str]:
        """
        Odczytanie zawartości pliku Python
        
        Args:
            file_path (str): Ścieżka do pliku
            
        Returns:
            Optional[str]: Zawartość pliku lub None w przypadku błędu
        """
        try:
            # Sprawdzenie czy plik istnieje
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Plik nie istnieje: {file_path}")
            
            # Sprawdzenie rozszerzenia
            if not self._is_python_file(file_path):
                raise ValueError(f"Nieobsługiwane rozszerzenie pliku: {file_path}")
            
            # Detekcja kodowania
            encoding = self._detect_encoding(file_path)
            
            # Odczyt pliku
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            
            return content
            
        except Exception as e:
            print(f"❌ Błąd odczytu pliku {file_path}: {e}")
            return None
    
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        Zapisanie zawartości do pliku
        
        Args:
            file_path (str): Ścieżka do pliku
            content (str): Zawartość do zapisania
            encoding (str): Kodowanie pliku
            
        Returns:
            bool: True jeśli zapisano, False w przeciwnym wypadku
        """
        try:
            # Utworzenie katalogów jeśli nie istnieją
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Zapis pliku
            with open(file_path, 'w', encoding=encoding) as file:
                file.write(content)
            
            print(f"✓ Zapisano plik: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Błąd zapisu pliku {file_path}: {e}")
            return False
    
    def find_python_files(self, directory: str, recursive: bool = True) -> List[str]:
        """
        Znajdowanie plików Python w katalogu
        
        Args:
            directory (str): Ścieżka do katalogu
            recursive (bool): Czy szukać rekurencyjnie
            
        Returns:
            List[str]: Lista ścieżek do plików Python
        """
        python_files = []
        
        try:
            if recursive:
                # Rekurencyjne szukanie
                for ext in self.supported_extensions:
                    pattern = os.path.join(directory, f"**/*{ext}")
                    python_files.extend(glob.glob(pattern, recursive=True))
            else:
                # Szukanie tylko w głównym katalogu
                for ext in self.supported_extensions:
                    pattern = os.path.join(directory, f"*{ext}")
                    python_files.extend(glob.glob(pattern))
            
            return sorted(python_files)
            
        except Exception as e:
            print(f"❌ Błąd podczas szukania plików: {e}")
            return []
    
    def validate_python_syntax(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Walidacja składni Python w pliku
        
        Args:
            file_path (str): Ścieżka do pliku
            
        Returns:
            Tuple[bool, Optional[str]]: (czy_poprawna_składnia, komunikat_błędu)
        """
        try:
            content = self.read_file(file_path)
            if content is None:
                return False, "Nie można odczytać pliku"
            
            # Parsowanie AST
            ast.parse(content)
            return True, None
            
        except SyntaxError as e:
            error_msg = f"Błąd składni w linii {e.lineno}: {e.msg}"
            return False, error_msg
        except Exception as e:
            return False, str(e)
    
    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """
        Pobieranie informacji o pliku
        
        Args:
            file_path (str): Ścieżka do pliku
            
        Returns:
            Dict[str, any]: Słownik z informacjami o pliku
        """
        try:
            stat = os.stat(file_path)
            content = self.read_file(file_path)
            
            info = {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size_bytes': stat.st_size,
                'modified_time': stat.st_mtime,
                'is_readable': os.access(file_path, os.R_OK),
                'is_writable': os.access(file_path, os.W_OK),
                'encoding': self._detect_encoding(file_path)
            }
            
            if content:
                lines = content.split('\n')
                info.update({
                    'line_count': len(lines),
                    'char_count': len(content),
                    'non_empty_lines': len([line for line in lines if line.strip()]),
                    'comment_lines': len([line for line in lines if line.strip().startswith('#')])
                })
            
            return info
            
        except Exception as e:
            print(f"❌ Błąd pobierania informacji o pliku: {e}")
            return {}
    
    def backup_file(self, file_path: str) -> Optional[str]:
        """
        Utworzenie kopii zapasowej pliku
        
        Args:
            file_path (str): Ścieżka do pliku
            
        Returns:
            Optional[str]: Ścieżka do kopii zapasowej lub None
        """
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.backup_{timestamp}"
            
            content = self.read_file(file_path)
            if content and self.write_file(backup_path, content):
                return backup_path
            
            return None
            
        except Exception as e:
            print(f"❌ Błąd tworzenia kopii zapasowej: {e}")
            return None
    
    def _is_python_file(self, file_path: str) -> bool:
        """Sprawdzenie czy plik ma rozszerzenie Python"""
        return any(file_path.lower().endswith(ext) for ext in self.supported_extensions)
    
    def _detect_encoding(self, file_path: str) -> str:
        """
        Detekcja kodowania pliku
        
        Args:
            file_path (str): Ścieżka do pliku
            
        Returns:
            str: Nazwa kodowania
        """
        try:
            # Próba automatycznej detekcji
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                if result['confidence'] > 0.7:
                    return result['encoding']
        except:
            pass
        
        # Fallback - próba różnych kodowań
        for encoding in self.encoding_fallbacks:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    file.read()
                return encoding
            except:
                continue
        
        # Ostatnia deska ratunku
        return 'utf-8'
    
    def extract_imports(self, file_path: str) -> List[str]:
        """
        Wyodrębnienie importów z pliku Python
        
        Args:
            file_path (str): Ścieżka do pliku
            
        Returns:
            List[str]: Lista importów
        """
        imports = []
        
        try:
            content = self.read_file(file_path)
            if not content:
                return imports
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)
            
            return sorted(list(set(imports)))
            
        except Exception as e:
            print(f"❌ Błąd wyodrębniania importów: {e}")
            return []
