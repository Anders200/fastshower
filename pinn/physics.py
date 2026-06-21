# pinn/physics.py
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# Stałe materiałowe dla PbWO4 (przykładowe wartości z PDG, dostosuj jeśli trzeba)
R_MOLIERE = 2.2  # cm
X0 = 0.89        # cm
E_CRIT = 9.37    # MeV

class PhysicsLossEvaluator(nn.Module):
    def __init__(self, init_a=2.0, init_b=0.5):
        super().__init__()
        # Inicjalizujemy teoretyczne parametry kształtu kaskady jako uczone parametry (nn.Parameter)
        # wzorując się na optymalizacji parametru 'alpha' z przesłanego notatnika.
        self.param_a = nn.Parameter(torch.tensor(init_a, dtype=torch.float32))
        self.param_b = nn.Parameter(torch.tensor(init_b, dtype=torch.float32))

    def get_diffusion_coefficient(self):
        """D = R_M^2 / X0 (stała dyfuzji poprzecznej z notatek)"""
        return (R_MOLIERE ** 2) / X0

    def alpha_of_z(self, z):
        """Zwraca człon zaniku podłużnego wzdłuż głębokości z"""
        # Miękkie ograniczenie dodatniości dla b oraz a za pomocą relu/softplus
        b = F.softplus(self.param_b) + 1e-3
        a = F.softplus(self.param_a) + 1.0
        return b - (a - 1.0) / (z + 1e-3)

    def compute_pde_residual(self, model, r, z, E0):
        """
        Oblicza rezyduum PDE adwekcji-dyfuzji w układzie cylindrycznym.
        Równanie: du/dz + alpha*u = D * (1/r * d/dr(r * du/dr))
        """
        # Przechodzimy w tryb obliczania pochodnych
        u = model(r, z, E0)

        # du / dz
        u_z = torch.autograd.grad(
            u, z, grad_outputs=torch.ones_like(u),
            create_graph=True, retain_graph=True
        )[0]

        # du / dr
        u_r = torch.autograd.grad(
            u, r, grad_outputs=torch.ones_like(u),
            create_graph=True, retain_graph=True
        )[0]

        # r * (du / dr)
        r_u_r = r * u_r

        # d/dr (r * du/dr)
        r_u_r_r = torch.autograd.grad(
            r_u_r, r, grad_outputs=torch.ones_like(r_u_r),
            create_graph=True, retain_graph=True
        )[0]

        # Człon dyfuzji w koordynatach cylindrycznych: D * (1/r) * d/dr(r * du/dr)
        D = self.get_diffusion_coefficient()
        # Dodajemy mały epsilon do r w mianowniku, żeby uniknąć dzielenia przez 0 na osi (r=0)
        pde_diffusion = D * (1.0 / (r + 1e-4)) * r_u_r_r
        
        # Człon adwekcji/zaniku podłużnego
        alpha = self.alpha_of_z(z)
        pde_advection = u_z + alpha * u

        # Rezyduum: Lewa Strona - Prawa Strona
        residual = pde_advection - pde_diffusion
        return residual