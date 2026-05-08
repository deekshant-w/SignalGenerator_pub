import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import yaml
from generator2 import main as signalGenerator
from misc import Blockmaker

##Code used convert downloaded files into structure's sub-unit sequence

def LoadAndRun():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        filetypes=[("YAML files", "*.yaml")], 
        title="Select YAML file", 
        initialdir=Path.home() / "Downloads"
    )
    file_path = Path(file_path)
    file = file_path.stem
    try:
        _, _, radius, resolution, _ = file.split('_')
        radius = float(radius.replace('-', '.'))
        print(f'Radius: {radius}')
        resolution = int(resolution.replace('-', '.'))
        print(f'Resolution: {resolution}')
    except:
        print("Metadata not found in filename")
        radius = input("Enter Nanopore Radius (default 2.2): ") or 2.2
        resolution = input("Enter Resolution (default 1000): ") or 1000

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    blocks = Blockmaker(data)
    print(blocks)
    signal = signalGenerator(blocks[1], radius, resolution)
    print("Signal Generated")

def debug():
    blocks = []
    radius = 2.2
    resolution = 1000
    signal = signalGenerator(blocks, radius, resolution)

if __name__ == "__main__":
    LoadAndRun()