"""
Moduł serializacji dla objektów MongoDB
Konwertuje niestandardowe objekty Python na formaty kompatybilne z BSON
"""

from typing import Any, Dict, List, Union
from enum import Enum
from datetime import datetime
import json

def serialize_for_mongodb(obj: Any) -> Any:
    """
    Uniwersalna funkcja serializacji objektów dla MongoDB
    
    Args:
        obj (Any): Objekt do serializacji
        
    Returns:
        Any: Objekt kompatybilny z BSON
    """
    if obj is None:
        return None
    
    # Podstawowe typy - bez konwersji
    elif isinstance(obj, (str, int, float, bool, datetime)):
        return obj
    
    # Enum - konwersja na wartość
    elif isinstance(obj, Enum):
        return obj.value
    
    # Lista - rekurencyjna serializacja elementów
    elif isinstance(obj, list):
        return [serialize_for_mongodb(item) for item in obj]
    
    # Słownik - rekurencyjna serializacja wartości
    elif isinstance(obj, dict):
        return {key: serialize_for_mongodb(value) for key, value in obj.items()}
    
    # Objekt z metodą to_dict() - użyj jej
    elif hasattr(obj, 'to_dict'):
        return serialize_for_mongodb(obj.to_dict())
    
    # Dataclass - konwersja na dict
    elif hasattr(obj, '__dataclass_fields__'):
        return serialize_for_mongodb(obj.__dict__)
    
    # Fallback - próba konwersji na string
    else:
        try:
            return str(obj)
        except Exception:
            return f"<Unserialized object: {type(obj).__name__}>"

def deserialize_from_mongodb(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deserializacja danych z MongoDB
    Odtwarza objekty na podstawie typu zapisanego w 'object_type'
    
    Args:
        data (Dict[str, Any]): Dane z MongoDB
        
    Returns:
        Dict[str, Any]: Przetworzone dane
    """
    if not isinstance(data, dict):
        return data
    
    # Sprawdź czy dokument zawiera informację o typie objektu
    obj_type = data.get('object_type')
    
    if obj_type == 'CodeError':
        # Importuj tutaj aby uniknąć circular imports
        from ..core.code_analyzer import CodeError
        return CodeError.from_dict(data)
    
    # Rekurencyjna deserializacja zagnieżdżonych struktur
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = deserialize_from_mongodb(value)
        elif isinstance(value, list):
            result[key] = [deserialize_from_mongodb(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
    
    return result

def validate_serialization(obj: Any) -> bool:
    """
    Walidacja czy objekt może być serializowany
    
    Args:
        obj (Any): Objekt do sprawdzenia
        
    Returns:
        bool: True jeśli może być serializowany
    """
    try:
        serialized = serialize_for_mongodb(obj)
        # Próba konwersji na JSON jako test serialization
        json.dumps(serialized, default=str)
        return True
    except Exception:
        return False

def get_serialization_info(obj: Any) -> Dict[str, Any]:
    """
    Informacje diagnostyczne o serializacji objektu
    
    Args:
        obj (Any): Objekt do analizy
        
    Returns:
        Dict[str, Any]: Informacje o serializacji
    """
    info = {
        'type': type(obj).__name__,
        'can_serialize': validate_serialization(obj),
        'has_to_dict': hasattr(obj, 'to_dict'),
        'is_dataclass': hasattr(obj, '__dataclass_fields__'),
        'is_enum': isinstance(obj, Enum)
    }
    
    if isinstance(obj, (list, dict)):
        info['length'] = len(obj)
    
    return info
