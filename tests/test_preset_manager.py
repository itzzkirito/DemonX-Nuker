"""
Tests for PresetManager class
"""

import pytest
import json
from pathlib import Path
from demonx import PresetManager


def test_preset_manager_initialization(tmp_path):
    """Test PresetManager initialization"""
    preset_file = tmp_path / "test_presets.json"
    manager = PresetManager(str(preset_file))
    assert manager is not None
    assert hasattr(manager, 'list_presets')
    assert hasattr(manager, 'get_preset')
    assert hasattr(manager, 'save_preset')


def test_preset_manager_list_presets(tmp_path):
    """Test listing presets"""
    preset_file = tmp_path / "test_presets.json"
    manager = PresetManager(str(preset_file))
    
    presets = manager.list_presets()
    assert isinstance(presets, list)


def test_preset_manager_save_and_get_preset(tmp_path):
    """Test saving and retrieving presets"""
    preset_file = tmp_path / "test_presets.json"
    manager = PresetManager(str(preset_file))
    
    # Create a test preset
    test_preset = [
        {"type": "ban_all", "params": {}},
        {"type": "delete_channels", "params": {}}
    ]
    
    manager.save_preset("test_preset", test_preset)
    
    # Retrieve the preset
    retrieved = manager.get_preset("test_preset")
    assert retrieved == test_preset

