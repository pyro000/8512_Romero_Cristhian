import sys
from cx_Freeze import setup, Executable

build_exe_options = {"packages": [], "excludes": [], 'include_files': ['lib/']}

base_gui = "Win32GUI"

setup(
    name = "LTS",
    version = "0.1",
    description = "LTS",
    options = {"build_exe": build_exe_options},
    executables = [Executable("test4.py", target_name='LTS.exe', icon='lib/icon.ico', base=base_gui)]
)