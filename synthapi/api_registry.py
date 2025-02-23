import json
from pathlib import Path
from typing import List, Dict

REGISTRY_FILE = Path(__file__).parent / "api_registry.json"
GENERATED_API_DIR = Path(__file__).parent / "generated_apis"

def clean_registry():
    """Reset the registry to initial state and clean generated files"""
    # Reset registry file
    initial_content = {
        "apis": {}
    }
    with open(REGISTRY_FILE, "w") as f:
        json.dump(initial_content, f, indent=2)
    
    # Clean generated_apis directory
    if GENERATED_API_DIR.exists():
        # Remove all JSON and txt files
        for file in GENERATED_API_DIR.glob("*.json"):
            file.unlink()
        for file in GENERATED_API_DIR.glob("*.txt"):
            file.unlink()
        
    return True

def get_registry_data() -> Dict:
    """Returns the full registry data including initialization status"""
    if not REGISTRY_FILE.exists():
        return {"apis": {}}
    
    with open(REGISTRY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"apis": {}}

def get_available_specs() -> List[str]:
    """Returns a list of available OpenAPI specs that haven't been initialized"""
    registry_data = get_registry_data()
    return [name for name, data in registry_data.get("apis", {}).items() 
            if not data.get("initialized", False)]

def get_all_specs() -> Dict[str, bool]:
    """Returns all specs with their initialization status"""
    registry_data = get_registry_data()
    return {name: data.get("initialized", False) 
            for name, data in registry_data.get("apis", {}).items()}

def add_api_to_registry(api_name: str):
    """Adds a new API name to the registry"""
    registry_data = get_registry_data()
    
    if api_name not in registry_data.get("apis", {}):
        if "apis" not in registry_data:
            registry_data["apis"] = {}
        registry_data["apis"][api_name] = {
            "initialized": False
        }
        
        with open(REGISTRY_FILE, "w") as f:
            json.dump(registry_data, f, indent=2)

def mark_api_as_initialized(api_name: str) -> bool:
    """Marks an API as initialized. Returns True if successful."""
    registry_data = get_registry_data()
    
    if api_name not in registry_data.get("apis", {}):
        return False
    
    registry_data["apis"][api_name]["initialized"] = True
    
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry_data, f, indent=2)
    
    return True