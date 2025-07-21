"""
Interfejs komunikacji z modelami AI
Obsługuje OpenAI i HuggingFace API
"""

import openai
import requests
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time

class AIProvider(Enum):
    """Dostawcy usług AI"""
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"

@dataclass
class AIResponse:
    """Odpowiedź z modelu AI"""
    content: str
    provider: AIProvider
    model: str
    tokens_used: int = 0
    execution_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None

class AIInterface:
    """Główna klasa interfejsu AI"""
    
    def __init__(self, openai_api_key: str, hf_api_key: Optional[str] = None):
        """
        Inicjalizacja interfejsu AI
        
        Args:
            openai_api_key (str): Klucz API OpenAI
            hf_api_key (Optional[str]): Klucz API HuggingFace
        """
        self.openai_api_key = openai_api_key
        self.hf_api_key = hf_api_key
        
        # Konfiguracja OpenAI
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
        # Ustawienia domyślne
        self.default_model = "gpt-4.1-nano-2025-04-14"
        self.default_temperature = 0.3
        self.default_max_tokens = 20000
        
        # HuggingFace endpoints
        self.hf_endpoints = {
            "code-analysis": "https://api-inference.huggingface.co/models/microsoft/CodeBERT-base",
            "text-generation": "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
        }
    
    def analyze_code_with_gpt(self, code: str, analysis_type: str = "general") -> AIResponse:
        """
        Analiza kodu z wykorzystaniem GPT
        
        Args:
            code (str): Kod Python do analizy
            analysis_type (str): Typ analizy
            
        Returns:
            AIResponse: Odpowiedź z analizą
        """
        start_time = time.time()
        
        try:
            prompt = self._build_analysis_prompt(code, analysis_type)
            
            response = self.openai_client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": "Jesteś ekspertem w analizie i optymalizacji kodu Python. Zwracaj zawsze strukturalne odpowiedzi w formacie JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.default_max_tokens,
                temperature=self.default_temperature
            )
            
            execution_time = time.time() - start_time
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider=AIProvider.OPENAI,
                model=self.default_model,
                tokens_used=response.usage.total_tokens,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return AIResponse(
                content="",
                provider=AIProvider.OPENAI,
                model=self.default_model,
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
    
    def get_code_suggestions(self, code: str, error_context: str = "") -> AIResponse:
        """
        Pobieranie sugestii poprawy kodu
        
        Args:
            code (str): Kod Python
            error_context (str): Kontekst błędu
            
        Returns:
            AIResponse: Sugestie poprawy
        """
        start_time = time.time()
        
        try:
            prompt = f"""
            Bardzo dokładnie i szczegółowo Przeanalizuj poniższy kod Python i zaproponuj konkretne poprawki:
            
            KOD:
            {code}
            
            {f"KONTEKST BŁĘDU: {error_context}" if error_context else ""}
            
            Zwróć odpowiedź w formacie JSON:
            {{
                "suggestions": [
                    {{
                        "line": numer_linii,
                        "issue": "opis_problemu",
                        "fix": "proponowana_poprawa",
                        "priority": "high|medium|low"
                    }}
                ],
                "overall_quality": "ocena_ogólna",
                "refactoring_opportunities": ["lista_możliwości_refaktoryzacji"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": "Jesteś ekspertem Python skupiającym się na jakości kodu i najlepszych praktykach."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.default_max_tokens,
                temperature=0.2
            )
            
            execution_time = time.time() - start_time
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider=AIProvider.OPENAI,
                model=self.default_model,
                tokens_used=response.usage.total_tokens,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return AIResponse(
                content="",
                provider=AIProvider.OPENAI,
                model=self.default_model,
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
    
    def explain_error(self, error_message: str, code_context: str = "") -> AIResponse:
        """
        Wyjaśnienie błędu z kontekstem
        
        Args:
            error_message (str): Komunikat błędu
            code_context (str): Kontekst kodu
            
        Returns:
            AIResponse: Wyjaśnienie błędu
        """
        start_time = time.time()
        
        try:
            prompt = f"""
            Wyjaśnij następujący błąd Python w sposób zrozumiały dla programisty:
            
            BŁĄD: {error_message}
            
            {f"KONTEKST KODU:\n{code_context}" if code_context else ""}
            
            Zwróć odpowiedź w formacie JSON:
            {{
                "explanation": "dokładne_wyjaśnienie_błędu",
                "cause": "przyczyna_błędu",
                "solution": "jak_naprawić",
                "prevention": "jak_uniknąć_w_przyszłości",
                "example_fix": "przykład_poprawnego_kodu"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": "Jesteś nauczycielem programowania Python. Wyjaśniaj błędy w sposób edukacyjny i praktyczny oraz pokaż możliwą optymalizację."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=20000,
                temperature=0.3
            )
            
            execution_time = time.time() - start_time
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider=AIProvider.OPENAI,
                model=self.default_model,
                tokens_used=response.usage.total_tokens,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return AIResponse(
                content="",
                provider=AIProvider.OPENAI,
                model=self.default_model,
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
    
    def analyze_with_huggingface(self, code: str, task: str = "code-analysis") -> AIResponse:
        """
        Analiza z wykorzystaniem HuggingFace
        
        Args:
            code (str): Kod do analizy
            task (str): Typ zadania
            
        Returns:
            AIResponse: Wynik analizy
        """
        start_time = time.time()
        
        if not self.hf_api_key:
            return AIResponse(
                content="",
                provider=AIProvider.HUGGINGFACE,
                model="N/A",
                execution_time=0,
                success=False,
                error_message="Brak klucza API HuggingFace"
            )
        
        try:
            endpoint = self.hf_endpoints.get(task, self.hf_endpoints["code-analysis"])
            
            headers = {
                "Authorization": f"Bearer {self.hf_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": code,
                "options": {"wait_for_model": True}
            }
            
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            
            execution_time = time.time() - start_time
            
            return AIResponse(
                content=json.dumps(response.json()),
                provider=AIProvider.HUGGINGFACE,
                model=endpoint.split("/")[-1],
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return AIResponse(
                content="",
                provider=AIProvider.HUGGINGFACE,
                model="N/A",
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
    
    def _build_analysis_prompt(self, code: str, analysis_type: str) -> str:
        """Budowanie promptu dla analizy"""
        
        prompts = {
            "general": f"""
                Przeanalizuj ten kod Python pod kątem:
                - Błędów logicznych
                - Problemów z wydajnością
                - Naruszenia konwencji PEP 8
                - Potencjalnych problemów bezpieczeństwa
                
                KOD:
                {code}
                
                Zwróć wynik w formacie JSON z sekcjami: errors, warnings, suggestions, security_issues.
            """,
            
            "security": f"""
                Przeanalizuj ten kod Python pod kątem bezpieczeństwa:
                - SQL injection
                - XSS vulnerabilities
                - Niebezpieczne użycie eval/exec
                - Problemy z walidacją danych
                
                KOD:
                {code}
                
                Zwróć wynik w formacie JSON z opisem zagrożeń i sposobami ich mitygacji.
            """,
            
            "performance": f"""
                Przeanalizuj ten kod Python pod kątem wydajności:
                - Złożoność algorytmiczną
                - Nieefektywne użycie struktur danych
                - Możliwości optymalizacji
                
                KOD:
                {code}
                
                Zwróć wynik w formacie JSON z sugestiami optymalizacji.
            """
        }
        
        return prompts.get(analysis_type, prompts["general"])
    
    def test_connection(self) -> Dict[str, bool]:
        """
        Test połączenia z usługami AI
        
        Returns:
            Dict[str, bool]: Status połączeń
        """
        results = {}
        
        # Test OpenAI
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            results["openai"] = True
        except:
            results["openai"] = False
        
        # Test HuggingFace
        if self.hf_api_key:
            try:
                headers = {"Authorization": f"Bearer {self.hf_api_key}"}
                response = requests.get("https://huggingface.co/api/whoami", headers=headers)
                results["huggingface"] = response.status_code == 200
            except:
                results["huggingface"] = False
        else:
            results["huggingface"] = False
        
        return results
