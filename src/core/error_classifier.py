"""
Klasyfikator błędów dla analizatora kodu
Kategoryzuje i priorytetyzuje błędy znalezione w kodzie
"""

import re
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from ..core.code_analyzer import CodeError, ErrorSeverity

class ErrorCategory(Enum):
    """Kategorie błędów"""
    SYNTAX = "syntax"
    LOGIC = "logic"
    STYLE = "style"
    PERFORMANCE = "performance"
    SECURITY = "security"
    IMPORTS = "imports"
    NAMING = "naming"
    COMPLEXITY = "complexity"

class ErrorPriority(Enum):
    """Priorytety błędów"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class ClassifiedError:
    """Sklasyfikowany błąd"""
    original_error: CodeError
    category: ErrorCategory
    priority: ErrorPriority
    fix_suggestion: str
    explanation: str
    documentation_link: Optional[str] = None

class ErrorClassifier:
    """Klasyfikator błędów kodu Python"""
    
    def __init__(self):
        """Inicjalizacja klasyfikatora"""
        self.error_patterns = self._initialize_error_patterns()
        self.fix_suggestions = self._initialize_fix_suggestions()
    
    def classify_errors(self, errors: List[CodeError]) -> List[ClassifiedError]:
        """
        Klasyfikacja listy błędów
        
        Args:
            errors (List[CodeError]): Lista błędów do klasyfikacji
            
        Returns:
            List[ClassifiedError]: Lista sklasyfikowanych błędów
        """
        classified_errors = []
        
        for error in errors:
            classified = self._classify_single_error(error)
            if classified:
                classified_errors.append(classified)
        
        # Sortowanie według priorytetu
        classified_errors.sort(key=lambda x: x.priority.value)
        
        return classified_errors
    
    def _classify_single_error(self, error: CodeError) -> Optional[ClassifiedError]:
        """
        Klasyfikacja pojedynczego błędu
        
        Args:
            error (CodeError): Błąd do klasyfikacji
            
        Returns:
            Optional[ClassifiedError]: Sklasyfikowany błąd lub None
        """
        # Identyfikacja kategorii na podstawie typu błędu i wiadomości
        category = self._determine_category(error)
        priority = self._determine_priority(error, category)
        fix_suggestion = self._get_fix_suggestion(error, category)
        explanation = self._get_explanation(error, category)
        documentation_link = self._get_documentation_link(error, category)
        
        return ClassifiedError(
            original_error=error,
            category=category,
            priority=priority,
            fix_suggestion=fix_suggestion,
            explanation=explanation,
            documentation_link=documentation_link
        )
    
    def _determine_category(self, error: CodeError) -> ErrorCategory:
        """Określenie kategorii błędu"""
        error_type = error.error_type.lower()
        message = error.message.lower()
        
        # Błędy składniowe
        if "syntax" in error_type or error.severity == ErrorSeverity.ERROR:
            return ErrorCategory.SYNTAX
        
        # Błędy bezpieczeństwa
        security_keywords = ["eval", "exec", "input", "sql", "shell", "subprocess"]
        if any(keyword in message for keyword in security_keywords):
            return ErrorCategory.SECURITY
        
        # Błędy importów
        import_keywords = ["import", "module", "package"]
        if any(keyword in message for keyword in import_keywords):
            return ErrorCategory.IMPORTS
        
        # Błędy nazewnictwa
        naming_keywords = ["name", "variable", "function", "class", "constant"]
        if any(keyword in message for keyword in naming_keywords):
            return ErrorCategory.NAMING
        
        # Błędy wydajności
        performance_keywords = ["loop", "complexity", "inefficient", "slow"]
        if any(keyword in message for keyword in performance_keywords):
            return ErrorCategory.PERFORMANCE
        
        # Błędy złożoności
        complexity_keywords = ["complex", "long", "nested", "deep"]
        if any(keyword in message for keyword in complexity_keywords):
            return ErrorCategory.COMPLEXITY
        
        # Błędy stylu (domyślnie)
        return ErrorCategory.STYLE
    
    def _determine_priority(self, error: CodeError, category: ErrorCategory) -> ErrorPriority:
        """Określenie priorytetu błędu"""
        # Mapowanie severity na priority
        severity_priority_map = {
            ErrorSeverity.CRITICAL: ErrorPriority.CRITICAL,
            ErrorSeverity.ERROR: ErrorPriority.HIGH,
            ErrorSeverity.WARNING: ErrorPriority.MEDIUM,
            ErrorSeverity.INFO: ErrorPriority.LOW
        }
        
        base_priority = severity_priority_map.get(error.severity, ErrorPriority.LOW)
        
        # Modyfikacja priorytetu na podstawie kategorii
        if category == ErrorCategory.SECURITY:
            return ErrorPriority.CRITICAL
        elif category == ErrorCategory.SYNTAX:
            return ErrorPriority.HIGH
        elif category in [ErrorCategory.LOGIC, ErrorCategory.IMPORTS]:
            return max(base_priority, ErrorPriority.MEDIUM)
        
        return base_priority
    
    def _get_fix_suggestion(self, error: CodeError, category: ErrorCategory) -> str:
        """Generowanie sugestii naprawy"""
        error_type = error.error_type.lower()
        message = error.message.lower()
        
        # Sprawdzenie wzorców specyficznych błędów
        for pattern, suggestion in self.fix_suggestions.items():
            if re.search(pattern, message, re.IGNORECASE):
                return suggestion
        
        # Sugestie na podstawie kategorii
        category_suggestions = {
            ErrorCategory.SYNTAX: "Sprawdź składnię Python w tej linii. Możliwe problemy: brakujące nawiasy, dwukropki, nieprawidłowe wcięcia.",
            ErrorCategory.IMPORTS: "Sprawdź czy moduł jest zainstalowany i czy nazwa importu jest poprawna.",
            ErrorCategory.NAMING: "Zastosuj konwencje nazewnictwa PEP 8: snake_case dla zmiennych i funkcji, PascalCase dla klas.",
            ErrorCategory.SECURITY: "Sprawdź kod pod kątem bezpieczeństwa. Unikaj eval(), exec() i niewalidowanych danych wejściowych.",
            ErrorCategory.PERFORMANCE: "Rozważ optymalizację tego fragmentu kodu.",
            ErrorCategory.STYLE: "Dostosuj kod do konwencji PEP 8.",
            ErrorCategory.COMPLEXITY: "Rozważ refaktoryzację w celu zmniejszenia złożoności."
        }
        
        return category_suggestions.get(category, "Sprawdź i popraw wskazany fragment kodu.")
    
    def _get_explanation(self, error: CodeError, category: ErrorCategory) -> str:
        """Generowanie wyjaśnienia błędu"""
        explanations = {
            ErrorCategory.SYNTAX: f"Błąd składniowy: {error.message}. Ten typ błędu uniemożliwia uruchomienie programu.",
            ErrorCategory.SECURITY: f"Potencjalny problem bezpieczeństwa: {error.message}. Może prowadzić do podatności w aplikacji.",
            ErrorCategory.IMPORTS: f"Problem z importowaniem: {error.message}. Sprawdź dostępność modułu.",
            ErrorCategory.NAMING: f"Naruszenie konwencji nazewnictwa: {error.message}. Wpływa na czytelność kodu.",
            ErrorCategory.PERFORMANCE: f"Problem wydajnościowy: {error.message}. Może wpływać na szybkość działania.",
            ErrorCategory.STYLE: f"Problem stylistyczny: {error.message}. Nie wpływa na działanie, ale na jakość kodu.",
            ErrorCategory.COMPLEXITY: f"Wysoka złożoność: {error.message}. Utrudnia zrozumienie i utrzymanie kodu."
        }
        
        return explanations.get(category, f"Znaleziony problem: {error.message}")
    
    def _get_documentation_link(self, error: CodeError, category: ErrorCategory) -> Optional[str]:
        """Generowanie linku do dokumentacji"""
        documentation_links = {
            ErrorCategory.SYNTAX: "https://docs.python.org/3/reference/grammar.html",
            ErrorCategory.STYLE: "https://pep8.org/",
            ErrorCategory.NAMING: "https://pep8.org/#naming-conventions",
            ErrorCategory.IMPORTS: "https://docs.python.org/3/reference/import.html",
            ErrorCategory.SECURITY: "https://bandit.readthedocs.io/en/latest/",
            ErrorCategory.PERFORMANCE: "https://docs.python.org/3/library/profile.html"
        }
        
        return documentation_links.get(category)
    
    def _initialize_error_patterns(self) -> Dict[str, ErrorCategory]:
        """Inicjalizacja wzorców błędów"""
        return {
            r"invalid syntax": ErrorCategory.SYNTAX,
            r"indentation": ErrorCategory.SYNTAX,
            r"unexpected eof": ErrorCategory.SYNTAX,
            r"missing parentheses": ErrorCategory.SYNTAX,
            r"undefined name": ErrorCategory.LOGIC,
            r"name '.*' is not defined": ErrorCategory.LOGIC,
            r"no module named": ErrorCategory.IMPORTS,
            r"cannot import": ErrorCategory.IMPORTS,
            r"line too long": ErrorCategory.STYLE,
            r"trailing whitespace": ErrorCategory.STYLE,
            r"missing docstring": ErrorCategory.STYLE,
            r"too many.*arguments": ErrorCategory.LOGIC,
            r"unexpected keyword": ErrorCategory.LOGIC,
            r"eval.*": ErrorCategory.SECURITY,
            r"exec.*": ErrorCategory.SECURITY,
            r"subprocess.*shell=true": ErrorCategory.SECURITY
        }
    
    def _initialize_fix_suggestions(self) -> Dict[str, str]:
        """Inicjalizacja sugestii napraw"""
        return {
            r"invalid syntax": "Sprawdź składnię: nawiasy, dwukropki, wcięcia",
            r"indentation.*": "Popraw wcięcia - użyj 4 spacji zamiast tabulatorów",
            r"name '(.*)' is not defined": "Zdefiniuj zmienną '\\1' przed użyciem lub sprawdź literówki",
            r"no module named '(.*)'": "Zainstaluj moduł: pip install \\1",
            r"line too long": "Podziel linię na krósze fragmenty (max 79 znaków)",
            r"trailing whitespace": "Usuń białe znaki na końcu linii",
            r"missing docstring": "Dodaj docstring opisujący funkcję/klasę",
            r"too many.*arguments": "Sprawdź liczbę argumentów przekazywanych do funkcji",
            r"eval.*": "Zastąp eval() bezpieczniejszą alternatywą",
            r"exec.*": "Zastąp exec() bezpieczniejszą alternatywą",
            r"subprocess.*shell=true": "Użyj shell=False lub waliduj dane wejściowe"
        }
    
    def get_error_statistics(self, classified_errors: List[ClassifiedError]) -> Dict[str, Any]:
        """
        Generowanie statystyk błędów
        
        Args:
            classified_errors (List[ClassifiedError]): Lista sklasyfikowanych błędów
            
        Returns:
            Dict[str, Any]: Statystyki błędów
        """
        stats = {
            'total_errors': len(classified_errors),
            'by_category': {},
            'by_priority': {},
            'by_severity': {}
        }
        
        # Statystyki kategorii
        for category in ErrorCategory:
            count = len([e for e in classified_errors if e.category == category])
            if count > 0:
                stats['by_category'][category.value] = count
        
        # Statystyki priorytetów
        for priority in ErrorPriority:
            count = len([e for e in classified_errors if e.priority == priority])
            if count > 0:
                stats['by_priority'][priority.name.lower()] = count
        
        # Statystyki severity
        for severity in ErrorSeverity:
            count = len([e for e in classified_errors if e.original_error.severity == severity])
            if count > 0:
                stats['by_severity'][severity.value] = count
        
        return stats
    
    def filter_errors(self, classified_errors: List[ClassifiedError], 
                     category: Optional[ErrorCategory] = None,
                     priority: Optional[ErrorPriority] = None,
                     max_severity: Optional[ErrorSeverity] = None) -> List[ClassifiedError]:
        """
        Filtrowanie błędów według kryteriów
        
        Args:
            classified_errors (List[ClassifiedError]): Lista błędów
            category (Optional[ErrorCategory]): Filtr kategorii
            priority (Optional[ErrorPriority]): Filtr priorytetu
            max_severity (Optional[ErrorSeverity]): Maksymalny poziom severity
            
        Returns:
            List[ClassifiedError]: Przefiltrowana lista błędów
        """
        filtered = classified_errors
        
        if category:
            filtered = [e for e in filtered if e.category == category]
        
        if priority:
            filtered = [e for e in filtered if e.priority == priority]
        
        if max_severity:
            severity_order = [ErrorSeverity.INFO, ErrorSeverity.WARNING, ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]
            max_index = severity_order.index(max_severity)
            filtered = [e for e in filtered if severity_order.index(e.original_error.severity) <= max_index]
        
        return filtered
