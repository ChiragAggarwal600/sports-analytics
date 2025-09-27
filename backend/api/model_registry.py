"""
Model registry for centralized model management
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ModelRegistry:
    """Centralized model registry"""
    
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._initialized = False
    
    def register_model(self, name: str, model: Any) -> None:
        """Register a model with the given name"""
        self._models[name] = model
        logger.info(f"Registered model: {name}")
    
    def get_model(self, name: str) -> Optional[Any]:
        """Get a model by name"""
        return self._models.get(name)
    
    def get_all_models(self) -> Dict[str, Any]:
        """Get all registered models"""
        return self._models.copy()
    
    def is_initialized(self) -> bool:
        """Check if models are initialized"""
        return self._initialized
    
    def set_initialized(self, status: bool = True) -> None:
        """Set initialization status"""
        self._initialized = status
    
    def clear(self) -> None:
        """Clear all models"""
        self._models.clear()
        self._initialized = False
        logger.info("Model registry cleared")

# Global model registry instance
model_registry = ModelRegistry()

def get_models() -> Dict[str, Any]:
    """Get all models from the registry"""
    return model_registry.get_all_models()

def get_model(name: str) -> Optional[Any]:
    """Get a specific model from the registry"""
    return model_registry.get_model(name)

def register_model(name: str, model: Any) -> None:
    """Register a model in the registry"""
    model_registry.register_model(name, model)