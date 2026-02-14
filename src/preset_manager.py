"""
Preset Manager Module
Manages saving, loading, and deleting presets
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default data directory
DATA_DIR = Path.home() / 'AppData' / 'Roaming' / 'WindowRestore'
PRESETS_FILE = DATA_DIR / 'presets.json'


class PresetManager:
    """Manages window preset storage"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir if data_dir is not None else DATA_DIR
        self.presets_file = self.data_dir / 'presets.json'
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_presets(self) -> Dict[str, Any]:
        """Load presets from JSON file"""
        if not self.presets_file.exists():
            return {'presets': []}
        
        try:
            with open(self.presets_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing presets file: {e}")
            # Backup corrupted file
            backup = self.presets_file.with_suffix('.json.bak')
            self.presets_file.rename(backup)
            return {'presets': []}
        except Exception as e:
            logger.error(f"Error loading presets: {e}")
            return {'presets': []}
    
    def _save_presets(self, data: Dict[str, Any]) -> bool:
        """Save presets to JSON file"""
        try:
            with open(self.presets_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving presets: {e}")
            return False
    
    def save_preset(self, name: str, windows: List[Dict[str, Any]]) -> bool:
        """
        Save a new preset
        
        Args:
            name: Preset name
            windows: List of window information dicts
        
        Returns:
            True if successful
        """
        data = self._load_presets()
        
        # Check for duplicate name
        existing_names = [p['name'].lower() for p in data['presets']]
        final_name = name
        counter = 1
        while final_name.lower() in existing_names:
            counter += 1
            final_name = f"{name} ({counter})"
        
        # Create preset
        preset = {
            'id': str(uuid.uuid4()),
            'name': final_name,
            'created': datetime.now().isoformat(),
            'windows': windows
        }
        
        data['presets'].append(preset)
        
        if self._save_presets(data):
            logger.info(f"Saved preset: {final_name}")
            return True
        
        return False
    
    def load_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a preset by name
        
        Args:
            name: Preset name
        
        Returns:
            Preset dict or None
        """
        data = self._load_presets()
        
        for preset in data['presets']:
            if preset['name'].lower() == name.lower():
                return preset
        
        return None
    
    def load_preset_by_id(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a preset by ID
        
        Args:
            preset_id: Preset ID
        
        Returns:
            Preset dict or None
        """
        data = self._load_presets()
        
        for preset in data['presets']:
            if preset['id'] == preset_id:
                return preset
        
        return None
    
    def list_presets(self) -> List[Dict[str, Any]]:
        """
        List all saved presets
        
        Returns:
            List of preset dicts (without window data)
        """
        data = self._load_presets()
        
        # Return presets with summary info
        presets = []
        for p in data['presets']:
            presets.append({
                'id': p['id'],
                'name': p['name'],
                'created': p.get('created', ''),
                'window_count': len(p.get('windows', []))
            })
        
        return presets
    
    def delete_preset(self, name: str) -> bool:
        """
        Delete a preset by name
        
        Args:
            name: Preset name
        
        Returns:
            True if deleted
        """
        data = self._load_presets()
        
        original_count = len(data['presets'])
        data['presets'] = [p for p in data['presets'] if p['name'].lower() != name.lower()]
        
        if len(data['presets']) < original_count:
            if self._save_presets(data):
                logger.info(f"Deleted preset: {name}")
                return True
        
        return False
    
    def delete_preset_by_id(self, preset_id: str) -> bool:
        """
        Delete a preset by ID
        
        Args:
            preset_id: Preset ID
        
        Returns:
            True if deleted
        """
        data = self._load_presets()
        
        original_count = len(data['presets'])
        data['presets'] = [p for p in data['presets'] if p['id'] != preset_id]
        
        if len(data['presets']) < original_count:
            if self._save_presets(data):
                logger.info(f"Deleted preset: {preset_id}")
                return True
        
        return False
    
    def rename_preset(self, old_name: str, new_name: str) -> bool:
        """
        Rename a preset
        
        Args:
            old_name: Current name
            new_name: New name
        
        Returns:
            True if renamed
        """
        data = self._load_presets()
        
        for preset in data['presets']:
            if preset['name'].lower() == old_name.lower():
                preset['name'] = new_name
                if self._save_presets(data):
                    logger.info(f"Renamed preset: {old_name} -> {new_name}")
                    return True
        
        return False
    
    def get_preset_names(self) -> List[str]:
        """Get list of preset names"""
        return [p['name'] for p in self.list_presets()]
