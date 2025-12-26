#!/usr/bin/env python3
"""
Core Consolidation Script

Helps consolidate the core directory structure.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(PROJECT_ROOT))


class CoreConsolidator:
    """Consolidates core directory structure"""
    
    def __init__(self, dry_run: bool = True):
        self.core_dir = PROJECT_ROOT / "core"
        self.dry_run = dry_run
        self.actions = []
    
    def analyze_structure(self) -> Dict:
        """Analyze current structure and identify redundancies"""
        analysis = {
            "total_files": 0,
            "total_dirs": 0,
            "redundancies": []
        }
        
        # Count files and directories
        for root, dirs, files in os.walk(self.core_dir):
            analysis["total_files"] += len(files)
            analysis["total_dirs"] += len(dirs)
        
        # Find redundant security files
        security_files = list(self.core_dir.glob("**/security.py"))
        if len(security_files) > 1:
            analysis["redundancies"].append({
                "type": "duplicate_security",
                "files": [str(f.relative_to(self.core_dir)) for f in security_files]
            })
        
        # Find static directories
        static_dirs = list(self.core_dir.glob("**/static"))
        if len(static_dirs) > 1:
            analysis["redundancies"].append({
                "type": "multiple_static",
                "dirs": [str(d.relative_to(self.core_dir)) for d in static_dirs]
            })
        
        # Find utils directories
        utils_dirs = list(self.core_dir.glob("**/utils"))
        if len(utils_dirs) > 1:
            analysis["redundancies"].append({
                "type": "multiple_utils",
                "dirs": [str(d.relative_to(self.core_dir)) for d in utils_dirs]
            })
        
        return analysis
    
    def plan_consolidation(self) -> List[Dict]:
        """Plan consolidation steps"""
        steps = []
        
        # Step 1: Merge security utilities
        steps.append({
            "phase": 1,
            "action": "merge_security",
            "description": "Merge all security utilities into single file",
            "files_to_move": [
                ("core/ui/utils/security.py", "core/utils/security.py"),
                ("core/utils/security.py", "core/utils/security.py")
            ]
        })
        
        # Step 2: Consolidate static files
        steps.append({
            "phase": 1,
            "action": "consolidate_static",
            "description": "Merge static directories",
            "dirs_to_merge": [
                ("core/ui/static", "core/assets"),
                ("core/static", "core/assets")
            ]
        })
        
        # Step 3: Flatten UI structure
        steps.append({
            "phase": 2,
            "action": "flatten_ui",
            "description": "Flatten UI directory structure",
            "moves": [
                ("core/ui/components/*", "core/ui/"),
                ("core/ui/pages/*", "core/ui/"),
                ("core/ui/helpers/*", "core/ui/")
            ]
        })
        
        # Step 4: Remove encryption service
        steps.append({
            "phase": 3,
            "action": "remove_encryption_service",
            "description": "Remove redundant encryption service",
            "to_remove": ["core/services/encryption"]
        })
        
        return steps
    
    def execute_step(self, step: Dict):
        """Execute a consolidation step"""
        print(f"\n🔄 Executing: {step['description']}")
        
        if step["action"] == "merge_security":
            self._merge_security()
        elif step["action"] == "consolidate_static":
            self._consolidate_static()
        elif step["action"] == "flatten_ui":
            self._flatten_ui()
        elif step["action"] == "remove_encryption_service":
            self._remove_encryption_service()
    
    def _merge_security(self):
        """Merge security utilities"""
        # Read existing files
        old_security = self.core_dir / "utils" / "security.py"
        ui_security = self.core_dir / "ui" / "utils" / "security.py"
        new_security = self.core_dir / "utils" / "security_new.py"
        
        if not self.dry_run:
            # Backup originals
            if old_security.exists():
                shutil.move(str(old_security), str(old_security.with_suffix('.py.bak')))
            if ui_security.exists():
                shutil.move(str(ui_security), str(ui_security.with_suffix('.py.bak')))
            
            # Replace with new consolidated file
            if new_security.exists():
                shutil.move(str(new_security), str(old_security))
            
            self.actions.append(f"Merged security utilities")
        else:
            self.actions.append(f"[DRY RUN] Would merge security utilities")
    
    def _consolidate_static(self):
        """Consolidate static directories"""
        assets_dir = self.core_dir / "assets"
        
        if not self.dry_run:
            # Create assets directory
            assets_dir.mkdir(exist_ok=True)
            
            # Move static files
            for static_dir in [self.core_dir / "static", self.core_dir / "ui" / "static"]:
                if static_dir.exists():
                    for item in static_dir.iterdir():
                        dest = assets_dir / item.name
                        if item.is_file():
                            shutil.move(str(item), str(dest))
                        elif item.is_dir() and not dest.exists():
                            shutil.move(str(item), str(dest))
            
            self.actions.append(f"Consolidated static files to assets/")
        else:
            self.actions.append(f"[DRY RUN] Would consolidate static files")
    
    def _flatten_ui(self):
        """Flatten UI directory structure"""
        ui_dir = self.core_dir / "ui"
        
        if not self.dry_run:
            # Move components
            components_dir = ui_dir / "components"
            if components_dir.exists():
                for item in components_dir.iterdir():
                    if item.is_file():
                        shutil.move(str(item), str(ui_dir / f"component_{item.name}"))
            
            # Move pages
            pages_dir = ui_dir / "pages"
            if pages_dir.exists():
                for item in pages_dir.iterdir():
                    if item.is_file():
                        shutil.move(str(item), str(ui_dir / f"page_{item.name}"))
            
            # Remove empty directories
            for empty_dir in [components_dir, pages_dir, ui_dir / "helpers", ui_dir / "utils"]:
                if empty_dir.exists() and not any(empty_dir.iterdir()):
                    empty_dir.rmdir()
            
            self.actions.append(f"Flattened UI directory structure")
        else:
            self.actions.append(f"[DRY RUN] Would flatten UI directory")
    
    def _remove_encryption_service(self):
        """Remove redundant encryption service"""
        encryption_dir = self.core_dir / "services" / "encryption"
        
        if not self.dry_run:
            if encryption_dir.exists():
                shutil.rmtree(str(encryption_dir))
                self.actions.append(f"Removed encryption service directory")
        else:
            self.actions.append(f"[DRY RUN] Would remove encryption service")
    
    def update_imports(self):
        """Update imports after consolidation"""
        print("\n📝 Updating imports...")
        
        # Find all Python files
        py_files = list(self.core_dir.rglob("*.py"))
        
        import_updates = {
            "from core.ui.utils.security import": "from core.utils.security import",
            "from core.services.encryption import": "from core.utils.security import",
            "import core.ui.utils.security": "import core.utils.security",
            "import core.services.encryption": "import core.utils.security"
        }
        
        for py_file in py_files:
            if "bak" in py_file.name or "new" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                updated = False
                
                for old_import, new_import in import_updates.items():
                    if old_import in content:
                        content = content.replace(old_import, new_import)
                        updated = True
                
                if updated and not self.dry_run:
                    py_file.write_text(content)
                    self.actions.append(f"Updated imports in {py_file.relative_to(self.core_dir)}")
                elif updated:
                    self.actions.append(f"[DRY RUN] Would update imports in {py_file.relative_to(self.core_dir)}")
            
            except Exception as e:
                print(f"  Error updating {py_file}: {e}")
    
    def generate_report(self):
        """Generate consolidation report"""
        print("\n📊 Consolidation Report")
        print("=" * 50)
        
        for action in self.actions:
            print(f"  ✓ {action}")
        
        print(f"\nTotal actions: {len(self.actions)}")
        
        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No changes were made")
            print("Run with --execute to apply changes")
    
    def cleanup_empty_dirs(self):
        """Remove empty directories"""
        print("\n🧹 Cleaning up empty directories...")
        
        # Walk through directories bottom-up
        for root, dirs, files in os.walk(self.core_dir, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                
                # Check if directory is empty
                if not any(dir_path.iterdir()):
                    if not self.dry_run:
                        dir_path.rmdir()
                        self.actions.append(f"Removed empty directory: {dir_path.relative_to(self.core_dir)}")
                    else:
                        self.actions.append(f"[DRY RUN] Would remove empty directory: {dir_path.relative_to(self.core_dir)}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Consolidate core directory")
    parser.add_argument("--execute", action="store_true", help="Execute changes (default: dry run)")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3], help="Execute specific phase")
    
    args = parser.parse_args()
    
    consolidator = CoreConsolidator(dry_run=not args.execute)
    
    # Analyze current structure
    print("🔍 Analyzing current structure...")
    analysis = consolidator.analyze_structure()
    print(f"  Total files: {analysis['total_files']}")
    print(f"  Total directories: {analysis['total_dirs']}")
    print(f"  Redundancies found: {len(analysis['redundancies'])}")
    
    # Plan consolidation
    print("\n📋 Planning consolidation...")
    steps = consolidator.plan_consolidation()
    
    # Execute steps
    for step in steps:
        if args.phase and step["phase"] != args.phase:
            continue
        consolidator.execute_step(step)
    
    # Update imports
    consolidator.update_imports()
    
    # Cleanup
    consolidator.cleanup_empty_dirs()
    
    # Generate report
    consolidator.generate_report()


if __name__ == "__main__":
    main()
