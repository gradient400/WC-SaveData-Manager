import os
import shutil
import subprocess

def clean_build_dirs():
    """Clean up build and dist directories"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # Also remove .spec file if it exists
    if os.path.exists('savedata_manager.spec'):
        os.remove('savedata_manager.spec')

def build_exe():
    """Build the executable"""
    print("Cleaning previous build files...")
    clean_build_dirs()
    
    print("\nCreating .spec file...")
    with open('savedata_manager.spec', 'w', encoding='utf-8') as f:
        f.write(SPEC_CONTENT)
    
    print("\nBuilding executable...")
    subprocess.run(['pyinstaller', 'savedata_manager.spec'], check=True)
    
    print("\nCleaning up...")
    # Remove build directory and .spec file
    shutil.rmtree('build')
    os.remove('savedata_manager.spec')
    
    # Move executable to current directory
    exe_name = 'SavedataManager.exe'
    src_path = os.path.join('dist', exe_name)
    if os.path.exists(exe_name):
        os.remove(exe_name)
    shutil.move(src_path, exe_name)
    shutil.rmtree('dist')
    
    print(f"\nBuild complete! Created: {exe_name}")

# Spec file content
SPEC_CONTENT = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['savedata_manager.py'],
    pathex=[],
    binaries=[],
    datas=[('checkpoints', 'checkpoints')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SavedataManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='blue-male-gender-symbol-free-vector.ico'
)
'''

if __name__ == '__main__':
    build_exe()