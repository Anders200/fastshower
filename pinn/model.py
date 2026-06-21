# pinn/model.py
import torch
import torch.nn as nn
import torch.nn.functional as F

class EnergyDepositionPINN(nn.Module):
    def __init__(self, hidden_dim=128, depth=4):
        """
        PINN dla depozycji energii.
        Wejście: (r, z, E0) -> Wymiar 3
        Wyjście: dE/dV       -> Wymiar 1 (Zawsze > 0)
        """
        super().__init__()
        
        # Wejście to r, z, E0 (wymiar 3)
        layers = [nn.Linear(3, hidden_dim), nn.Tanh()]
        
        for _ in range(depth - 1):
            layers += [nn.Linear(hidden_dim, hidden_dim), nn.Tanh()]
            
        layers += [nn.Linear(hidden_dim, 1)]
        self.net = nn.Sequential(*layers)

    def forward(self, r, z, E0):
        """
        Przyjmuje osobne sensory wejściowe (będą potrzebne do autogradu)
        i zwraca przewidywaną gęstość depozycji energii u.
        """
        # Łączymy wejścia w jeden tensor (N, 3)
        x = torch.cat([r, z, E0], dim=1)
        raw_output = self.net(x)
        
        # Wymuszamy dE/dV > 0 za pomocą Softplus (tak jak w note.txt)
        return F.softplus(raw_output) + 1e-6

    def predict(self, r_np, z_np, E0_np):
        """
        Metoda kompatybilna z interface/g4_surrogate.py (wymaga numpy).
        """
        self.eval()
        device = next(self.parameters()).device
        
        r = torch.tensor(r_np, dtype=torch.float32, device=device).view(-1, 1)
        z = torch.tensor(z_np, dtype=torch.float32, device=device).view(-1, 1)
        E0 = torch.tensor(E0_np, dtype=torch.float32, device=device).view(-1, 1)
        
        with torch.no_grad():
            pred = self.forward(r, z, E0)
        return pred.cpu().numpy().flatten()