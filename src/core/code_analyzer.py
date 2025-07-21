"""
Moduł analizatora kodu Python z wykorzystaniem AI
Integruje narzędzia statycznej analizy z modelami AI
Autor: Sebastian Ciborowski
"""

import ast
import pylint.lint
from pylint.reporters.text import TextReporter
import io
import openai
from typing import List, Dict, Any, Optional, Tuple
import re
import json
from dataclasses import dataclass
from enum import Enum

class ErrorSeverity(Enum):
    """Enum określający poziom ważności błędu"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class CodeError:
    """Klasa reprezentująca błąd w kodzie"""
    line_number: int
    column: int
    error_type: str
    severity: ErrorSeverity
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Konwersja objektu CodeError na słownik dla MongoDB
        
        Returns:
            Dict[str, Any]: Słownik z wszystkimi atrybutami
        """
        return {
            'line_number': self.line_number,
            'column': self.column,
            'error_type': self.error_type,
            'severity': self.severity.value,  # Konwersja Enum na string
            'message': self.message,
            'suggestion': self.suggestion,
            'code_snippet': self.code_snippet,
            'object_type': 'CodeError'  # Identyfikator typu dla deserializacji
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeError':
        """
        Odtworzenie objektu CodeError ze słownika MongoDB
        
        Args:
            data (Dict[str, Any]): Słownik z bazy danych
            
        Returns:
            CodeError: Odtworzony objekt
        """
        return cls(
            line_number=data['line_number'],
            column=data['column'],
            error_type=data['error_type'],
            severity=ErrorSeverity(data['severity']),  # Konwersja string na Enum
            message=data['message'],
            suggestion=data.get('suggestion'),
            code_snippet=data.get('code_snippet')
        )
        
class CodeAnalyzer:
    """Główna klasa analizatora kodu"""
    
    def __init__(self, openai_api_key: str, hf_api_key: Optional[str] = None):
        """
        Inicjalizacja analizatora
        
        Args:
            openai_api_key (str): Klucz API OpenAI
            hf_api_key (Optional[str]): Klucz API HuggingFace
        """
        self.openai_api_key = openai_api_key
        self.hf_api_key = hf_api_key
        self.setup_openai()
    
    def setup_openai(self):
        """Konfiguracja klienta OpenAI"""
        openai.api_key = self.openai_api_key
        self.client = openai.OpenAI(api_key=self.openai_api_key)
    
    def analyze_code(self, code: str, file_path: str = "temp.py") -> Dict[str, Any]:
        """
        Kompleksowa analiza kodu Python
        
        Args:
            code (str): Kod Python do analizy
            file_path (str): Ścieżka pliku (opcjonalna)
            
        Returns:
            Dict[str, Any]: Wyniki analizy zawierające błędy, sugestie i metryki
        """
        results = {
            'syntax_errors': [],
            'static_analysis': [],
            'ai_suggestions': [],
            'refactoring_suggestions': [],
            'code_metrics': {},
            'status': 'success'
        }
        
        try:
            # 1. Analiza składniowa
            syntax_errors = self._check_syntax(code)
            results['syntax_errors'] = syntax_errors
            
            # 2. Analiza statyczna (pylint)
            if not syntax_errors:  # Tylko jeśli nie ma błędów składniowych
                static_errors = self._run_pylint(code)
                results['static_analysis'] = static_errors
                
                # 3. Analiza AI
                ai_analysis = self._analyze_with_ai(code)
                results['ai_suggestions'] = ai_analysis.get('suggestions', [])
                results['refactoring_suggestions'] = ai_analysis.get('refactoring', [])
                
                # 4. Metryki kodu
                results['code_metrics'] = self._calculate_metrics(code)
            
        except Exception as e:
            results['status'] = 'error'
            results['error_message'] = str(e)
        
        return results
    
    def _check_syntax(self, code: str) -> List[CodeError]:
        """
        Sprawdzanie błędów składniowych
        
        Args:
            code (str): Kod Python
            
        Returns:
            List[CodeError]: Lista błędów składniowych
        """
        errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            error = CodeError(
                line_number=e.lineno or 1,
                column=e.offset or 1,
                error_type="SyntaxError",
                severity=ErrorSeverity.ERROR,
                message=str(e.msg),
                code_snippet=e.text
            )
            errors.append(error)
        except Exception as e:
            error = CodeError(
                line_number=1,
                column=1,
                error_type="ParseError",
                severity=ErrorSeverity.CRITICAL,
                message=f"Nie można sparsować kodu: {str(e)}"
            )
            errors.append(error)
        
        return errors
    
    def _run_pylint(self, code: str) -> List[CodeError]:
        """
        Uruchomienie analizy pylint
        
        Args:
            code (str): Kod Python
            
        Returns:
            List[CodeError]: Lista błędów znalezionych przez pylint
        """
        errors = []
        
        # Utworzenie tymczasowego pliku w pamięci
        pylint_output = io.StringIO()
        reporter = TextReporter(pylint_output)
        
        try:
            # Utworzenie tymczasowego pliku
            with open('temp_analysis.py', 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Uruchomienie pylint
            pylint.lint.Run(['temp_analysis.py'], reporter=reporter, exit=False)
            
            # Parsowanie wyników
            pylint_output.seek(0)
            output_lines = pylint_output.read().split('\n')
            
            for line in output_lines:
                if ':' in line and any(severity in line for severity in ['E', 'W', 'R', 'C']):
                    error = self._parse_pylint_line(line)
                    if error:
                        errors.append(error)
        
        except Exception as e:
            print(f"Błąd podczas analizy pylint: {e}")
        
        finally:
            # Usunięcie tymczasowego pliku
            try:
                import os
                os.remove('temp_analysis.py')
            except:
                pass
        
        return errors
    
    def _parse_pylint_line(self, line: str) -> Optional[CodeError]:
        """
        Parsowanie linii wyniku pylint
        
        Args:
            line (str): Linia wyniku pylint
            
        Returns:
            Optional[CodeError]: Obiekt błędu lub None
        """
        # Pattern: temp_analysis.py:line:column: severity: message
        pattern = r'temp_analysis\.py:(\d+):(\d+):\s*([EWRC]\d+):\s*(.+)'
        match = re.match(pattern, line)
        
        if match:
            line_num, col_num, error_code, message = match.groups()
            
            # Określenie poziomu ważności
            severity_map = {
                'E': ErrorSeverity.ERROR,    # Error
                'W': ErrorSeverity.WARNING,  # Warning
                'R': ErrorSeverity.INFO,     # Refactor
                'C': ErrorSeverity.INFO      # Convention
            }
            
            severity = severity_map.get(error_code[0], ErrorSeverity.INFO)
            
            return CodeError(
                line_number=int(line_num),
                column=int(col_num),
                error_type=error_code,
                severity=severity,
                message=message.strip()
            )
        
        return None
    
    def _analyze_with_ai(self, code: str) -> Dict[str, Any]:
        """
        Analiza kodu z wykorzystaniem AI
        
        Args:
            code (str): Kod Python
            
        Returns:
            Dict[str, Any]: Wyniki analizy AI
        """
        try:
            # Prompt dla analizy kodu
            prompt = f"""
            Bardzo dokładnie i szczegółowo przeanalizuj następujący kod Python i zwróć wynik w formacie JSON:
            
            ```
            {code}
            ```
            
            Zwróć JSON zawierający:
            - "suggestions": lista sugestii poprawy kodu
            - "refactoring": lista sugestii refaktoryzacji
            - "security_issues": potencjalne problemy bezpieczeństwa
            - "performance_tips": wskazówki dotyczące wydajności
            
            Każda sugestia powinna mieć format:
            {{
                "line": numer_linii,
                "type": "typ_sugestii",
                "message": "opis_problemu",
                "suggestion": "proponowana_poprawa"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14",
                messages=[
                    {"role": "system", "content": "Jesteś ekspertem w analizie i optymalizacji kodu Python. Zwracaj zawsze poprawny JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=20000,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            
            # Parsowanie JSON z odpowiedzi AI
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                # Jeśli AI nie zwróciło poprawnego JSON, zwróć domyślną strukturę
                return {
                    "suggestions": [],
                    "refactoring": [],
                    "security_issues": [],
                    "performance_tips": []
                }
        
        except Exception as e:
            print(f"Błąd podczas analizy AI: {e}")
            return {
                "suggestions": [],
                "refactoring": [],
                "security_issues": [],
                "performance_tips": []
            }
    
    def _calculate_metrics(self, code: str) -> Dict[str, Any]:
        """
        Obliczanie metryk kodu
        
        Args:
            code (str): Kod Python
            
        Returns:
            Dict[str, Any]: Metryki kodu
        """
        metrics = {
            'lines_of_code': len(code.split('\n')),
            'non_empty_lines': len([line for line in code.split('\n') if line.strip()]),
            'comment_lines': len([line for line in code.split('\n') if line.strip().startswith('#')]),
            'function_count': 0,
            'class_count': 0,
            'complexity_score': 0
        }
        
        try:
            tree = ast.parse(code)
            
            # Liczenie funkcji i klas
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics['function_count'] += 1
                elif isinstance(node, ast.ClassDef):
                    metrics['class_count'] += 1
            
            # Podstawowa złożoność cyklomatyczna
            metrics['complexity_score'] = self._calculate_complexity(tree)
            
        except Exception as e:
            print(f"Błąd podczas obliczania metryk: {e}")
        
        return metrics
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """
        Obliczanie podstawowej złożoności cyklomatycznej
        
        Args:
            tree (ast.AST): Drzewo AST
            
        Returns:
            int: Poziom złożoności
        """
        complexity = 1  # Bazowa złożoność
        
        for node in ast.walk(tree):
            # Zwiększanie złożoności dla struktur kontrolnych
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def get_line_suggestions(self, code: str, line_number: int) -> List[str]:
        """
        Pobieranie sugestii dla konkretnej linii kodu
        
        Args:
            code (str): Kod Python
            line_number (int): Numer linii
            
        Returns:
            List[str]: Lista sugestii dla linii
        """
        lines = code.split('\n')
        if line_number > len(lines) or line_number < 1:
            return []
        
        target_line = lines[line_number - 1]
        
        # Kontekst - kilka linii przed i po
        context_start = max(0, line_number - 3)
        context_end = min(len(lines), line_number + 3)
        context = '\n'.join(lines[context_start:context_end])
        
        try:
            prompt = f"""
            Przeanalizuj tę linię kodu Python i zaproponuj poprawki:
            
            Linia {line_number}: {target_line}
            
            Kontekst:
            {context}
            
            Zwróć konkretne sugestie poprawy tej linii.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14",
                messages=[
                    {"role": "system", "content": "Jesteś ekspertem Python. Dawaj konkretne, praktyczne sugestie."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=20000,
                temperature=0.3
            )
            
            suggestions = response.choices[0].message.content.split('\n')
            return [s.strip() for s in suggestions if s.strip()]
        
        except Exception as e:
            print(f"Błąd podczas pobierania sugestii dla linii: {e}")
            return []
