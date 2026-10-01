#!/usr/bin/env python3
"""
Build script for StickaEngine
Creates Windows executable, installer, and desktop shortcut
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_cmd(cmd, cwd=None):
    """Run a command and return success status."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    repo_root = Path(__file__).resolve().parent
    dist_dir = repo_root / "dist"
    build_dir = repo_root / "build"
    
    print("=" * 60)
    print("StickaEngine Build System")
    print("=" * 60)
    
    # Step 1: Clean previous builds
    print("\n[1/4] Cleaning previous builds...")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Step 2: Create icon if it doesn't exist
    print("\n[2/4] Creating icon...")
    icon_path = repo_root / "icon.ico"
    if not icon_path.exists():
        print("Creating default icon...")
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Blue circle with white border
            draw.ellipse((16, 16, 240, 240), fill=(0, 122, 255, 255))
            draw.ellipse((18, 18, 238, 238), fill=(255, 255, 255, 255), outline=(255, 255, 255, 255))
            img.save(str(icon_path))
            print("Icon created successfully")
        except ImportError:
            print("Pillow not available, skipping icon creation")
    
    # Step 3: Build with PyInstaller
    print("\n[3/4] Building with PyInstaller...")
    spec_path = repo_root / "StickaEngine.spec"
    
    # When using a .spec file, don't pass additional arguments
    cmd = [sys.executable, "-m", "PyInstaller", str(spec_path)]
    
    if not run_cmd(cmd, cwd=repo_root):
        print("ERROR: PyInstaller build failed!")
        return 1
    
    print("\nBuild completed successfully!")
    
    # Step 4: Check output
    if sys.platform == "win32":
        exe_path = dist_dir / "StickaEngine.exe"
        if exe_path.exists():
            print(f"\n[4/4] Executable created: {exe_path}")
            
            # Create desktop shortcut
            print("\nCreating desktop shortcut...")
            desktop = Path.home() / "Desktop"
            if not desktop.exists():
                desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
            
            lnk = desktop / "StickaEngine.lnk"
            ps_script = repo_root / "create_shortcut.ps1"
            
            # Create PowerShell script for shortcut
            ps_content = f'''
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("{lnk}")
$s.TargetPath = "{exe_path}"
$s.WorkingDirectory = "{exe_path.parent}"
$s.Description = "StickaEngine - Desktop Sticker Hub"
$s.IconLocation = "{exe_path},0"
$s.Save()
Write-Host "Desktop shortcut created: {lnk}"
'''
            with open(ps_script, "w") as f:
                f.write(ps_content)
            
            run_cmd(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)], cwd=repo_root)
            
            print(f"\nBuild Summary:")
            print(f"  Executable: {exe_path}")
            print(f"  Shortcut: {lnk}")
            print(f"\nTo run: Double-click the desktop shortcut")
        else:
            print(f"\nWARNING: Executable not found at {exe_path}")
    else:
        print(f"\nNote: Windows .exe can only be built on Windows")
        print(f"      Use a Windows machine to create the final executable")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
