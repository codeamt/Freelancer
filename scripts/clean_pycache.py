#!/usr/bin/env python3
"""
Clean all pycache and bytecode files from the project.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List

def find_pycache_dirs(root_dir: Path) -> List[Path]:
    """Find all __pycache__ directories"""
    return list(root_dir.rglob("__pycache__"))

def find_bytecode_files(root_dir: Path) -> List[Path]:
    """Find all bytecode files"""
    patterns = ["*.pyc", "*.pyo", "*.pyd"]
    bytecode_files = []
    for pattern in patterns:
        bytecode_files.extend(root_dir.rglob(pattern))
    return bytecode_files

def clean_pycache(root_dir: Path) -> dict:
    """Clean all pycache and bytecode files"""
    stats = {
        "pycache_dirs_removed": 0,
        "bytecode_files_removed": 0,
        "bytes_freed": 0
    }
    
    print(f"🧹 Cleaning pycache from: {root_dir}")
    
    # Find and remove __pycache__ directories
    pycache_dirs = find_pycache_dirs(root_dir)
    for pycache_dir in pycache_dirs:
        try:
            size = sum(f.stat().st_size for f in pycache_dir.rglob("*") if f.is_file())
            shutil.rmtree(pycache_dir)
            stats["pycache_dirs_removed"] += 1
            stats["bytes_freed"] += size
            print(f"  🗑️  Removed: {pycache_dir.relative_to(root_dir)}")
        except Exception as e:
            print(f"  ❌ Error removing {pycache_dir}: {e}")
    
    # Find and remove bytecode files
    bytecode_files = find_bytecode_files(root_dir)
    for bytecode_file in bytecode_files:
        try:
            size = bytecode_file.stat().st_size
            bytecode_file.unlink()
            stats["bytecode_files_removed"] += 1
            stats["bytes_freed"] += size
            print(f"  🗑️  Removed: {bytecode_file.relative_to(root_dir)}")
        except Exception as e:
            print(f"  ❌ Error removing {bytecode_file}: {e}")
    
    return stats

def format_bytes(bytes_count: int) -> str:
    """Format bytes in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} TB"

def main():
    """Main function"""
    # Get project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Clean pycache
    stats = clean_pycache(project_root)
    
    # Print summary
    print("\n" + "="*50)
    print("🧹 PYCACHE CLEANUP SUMMARY")
    print("="*50)
    print(f"📁 Directories removed: {stats['pycache_dirs_removed']}")
    print(f"📄 Files removed: {stats['bytecode_files_removed']}")
    print(f"💾 Space freed: {format_bytes(stats['bytes_freed'])}")
    
    if stats['pycache_dirs_removed'] == 0 and stats['bytecode_files_removed'] == 0:
        print("✅ Project is already clean!")
    else:
        print("🎉 Cleanup completed successfully!")
    
    print("\n💡 To prevent future pycache creation:")
    print("   • PYTHONDONTWRITEBYTECODE=1 is set")
    print("   • .pythonrc is configured")
    print("   • .gitignore blocks pycache files")

if __name__ == "__main__":
    main()
