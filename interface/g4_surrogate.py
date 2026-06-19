# interface/g4_surrogate.py
"""
The PINN-facing API for G4 data. 
pinn gada tylko z tym
"""

from pathlib import Path
from interface.io import load_dataset


class G4Surrogate:

    def __init__(self, model=None):
        self.model = model  # injected PINN, has .predict(r, z, E0)

    def get_training_points(self, data_dir: Path) -> dict:
        """Flat arrays (r, z, E0, dEdV) from all G4 runs in data_dir."""
        return load_dataset(data_dir)

    def query_pinn(self, r, z, E0):
        """Batch query  (jak już będzie wytrenowany to bierzemy całą siatkę)"""
        assert self.model is not None, "PINN model not injected"
        return self.model.predict(r, z, E0)
