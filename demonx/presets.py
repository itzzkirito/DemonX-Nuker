"""
Preset management for operations
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger('DemonX')


class PresetManager:
    """Manage operation presets"""
    
    def __init__(self, preset_file: str = "presets.json"):
        self.preset_file = preset_file
        self.presets: Dict[str, List[Dict]] = {}
        self.load_presets()
    
    def load_presets(self):
        """Load presets from file"""
        try:
            if Path(self.preset_file).exists():
                with open(self.preset_file, 'r') as f:
                    self.presets = json.load(f)
        except Exception as e:
            logger.error(f"Error loading presets: {e}")
    
    def save_presets(self):
        """Save presets to file"""
        try:
            with open(self.preset_file, 'w') as f:
                json.dump(self.presets, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving presets: {e}")
    
    def create_preset(self, name: str, operations: List[Dict]):
        """Create a new preset"""
        self.presets[name] = operations
        self.save_presets()
    
    def get_preset(self, name: str) -> Optional[List[Dict]]:
        """Get preset by name"""
        return self.presets.get(name)
    
    def list_presets(self) -> List[str]:
        """List all preset names"""
        return list(self.presets.keys())
    
    def delete_preset(self, name: str):
        """Delete a preset"""
        if name in self.presets:
            del self.presets[name]
            self.save_presets()

