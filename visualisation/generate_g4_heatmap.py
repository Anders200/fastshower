#!/usr/bin/env python3
import argparse
import numpy as np
import matplotlib
# Use the 'Agg' backend strictly for saving files without popping up a GUI
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Generate a heatmap from G4 .npz data.")
    parser.add_argument("input_file", type=Path, help="Path to the input .npz file")
    parser.add_argument("--output", type=Path, nargs='?', 
                        help="Optional: Path to save the image. Defaults to <input_file>.png")

    args = parser.parse_args()

    if not args.input_file.exists():
        print(f"Error: File '{args.input_file}' not found.")
        return

    # Auto-generate output filename if not explicitly provided
    output_path = args.output if args.output else args.input_file.with_suffix('.png')

    # Load data
    try:
        with np.load(args.input_file) as data:
            # Note: Adjust these keys if interface/io.py explicitly names them differently.
            # Fallback to positional arrays (arr_0, arr_1, etc.) if save_run didn't use kwargs.
            r = data.get('r_centers', data.get('arr_0'))
            z = data.get('z_centers_X0', data.get('arr_1'))
            dEdV = data.get('dEdV', data.get('arr_2'))
            E0_MeV = data.get('E0_MeV', data.get('arr_3', None))

            if r is None or z is None or dEdV is None:
                raise ValueError("Could not find required arrays (r, z, dEdV) in the .npz file.")
    except Exception as e:
        print(f"Failed to load data from {args.input_file}: {e}")
        return

    # Setup the plot
    plt.figure(figsize=(10, 6))

    # Create meshgrid for pcolormesh
    # dEdV shape is (nR, nZ) based on convert_to_npz.py
    Z, R = np.meshgrid(z, r)

    # Mask zero or negative values so LogNorm doesn't complain
    dEdV_masked = np.ma.masked_where(dEdV <= 0, dEdV)

    # Generate heatmap
    mesh = plt.pcolormesh(Z, R, dEdV_masked, shading='nearest', norm=LogNorm(), cmap='viridis')

    # Labeling according to your project's units
    plt.colorbar(mesh, label='Energy Density (dEdV) [MeV/cm$^3$]')
    plt.xlabel('Depth (z) [$X_0$ units]')
    plt.ylabel('Radius (r) [cm]')

    title = 'Geant4 Energy Deposition Heatmap'
    if E0_MeV is not None:
        title += f' ($E_0$ = {float(E0_MeV)} MeV)'
    plt.title(title)

    plt.tight_layout()

    # Save and close (no plt.show())
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"[heatmap] Successfully generated and saved to: {output_path}")

if __name__ == "__main__":
    main()
