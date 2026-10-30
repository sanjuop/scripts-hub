"""
Manifest Manager for Scripts Hub
Loads, validates, and updates scripts_manifest.json
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "scripts_manifest.json"


class ScriptManifest:
    def __init__(self, manifest_file: Optional[Path] = None):
        self.manifest_file = manifest_file or MANIFEST_PATH
        self.data: Dict = {}
        self.load()

    def load(self) -> None:
        """Load manifest from disk or initialize defaults."""
        if not self.manifest_file.exists():
            self.data = {
                "version": "1.0",
                "categories": ["All Scripts"],
                "scripts": []
            }
            self.save()
            return

        try:
            with open(self.manifest_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception as e:
            print(f"[Error] Failed to load manifest {self.manifest_file}: {e}")
            self.data = {"version": "1.0", "categories": ["All Scripts"], "scripts": []}

    def save(self) -> bool:
        """Persist current manifest to disk."""
        try:
            self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.manifest_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            return True
        except Exception as e:
            print(f"[Error] Failed to save manifest: {e}")
            return False

    def get_categories(self) -> List[str]:
        return self.data.get("categories", ["All Scripts"])

    def get_scripts(self) -> List[Dict]:
        return self.data.get("scripts", [])

    def get_script_by_id(self, script_id: str) -> Optional[Dict]:
        for s in self.get_scripts():
            if s.get("id") == script_id:
                return s
        return None

    def add_script(self, script_data: Dict) -> bool:
        """Add or update a script entry."""
        scripts = self.data.setdefault("scripts", [])
        # Replace if ID already exists
        for idx, s in enumerate(scripts):
            if s.get("id") == script_data.get("id"):
                scripts[idx] = script_data
                return self.save()

        scripts.append(script_data)
        # Ensure category is registered
        cat = script_data.get("category", "General")
        categories = self.data.setdefault("categories", ["All Scripts"])
        if cat not in categories:
            categories.append(cat)
        return self.save()

    def remove_script(self, script_id: str) -> bool:
        scripts = self.data.get("scripts", [])
        self.data["scripts"] = [s for s in scripts if s.get("id") != script_id]
        return self.save()

