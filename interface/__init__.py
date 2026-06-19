# interface/__init__.py
from interface.g4_surrogate import G4Surrogate
from interface.io import save_run, load_dataset

__all__ = ["G4Surrogate", "save_run", "load_dataset"]
