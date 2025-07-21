"""
Modele danych dla bazy danych MongoDB
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum

class AnalysisStatus(Enum):
    """Status analizy kodu"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class CodeAnalysisResult:
    """Model wyniku analizy kodu"""
    id: Optional[str] = None
    timestamp: datetime = None
    file_name: str = ""
    code_content: str = ""
    analysis_results: Dict[str, Any] = None
    status: AnalysisStatus = AnalysisStatus.PENDING
    execution_time: float = 0.0
    error_count: int = 0
    warning_count: int = 0
    
    def __post_init__(self):
        """Inicjalizacja po utworzeniu obiektu"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.analysis_results is None:
            self.analysis_results = {}

@dataclass
class UserSession:
    """Model sesji użytkownika"""
    session_id: str
    start_time: datetime
    last_activity: datetime
    analyses_count: int = 0
    
    def __post_init__(self):
        """Inicjalizacja po utworzeniu obiektu"""
        if self.start_time is None:
            self.start_time = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()
