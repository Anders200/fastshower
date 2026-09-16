# generate_mock_data.py
import numpy as np
from pathlib import Path
from interface import config
from interface.io import save_run
from scipy.special import gamma

# Parametry fizyczne bazy do wygenerowania sztucznego kształtu
E_CRIT = 9.37  # MeV
b_true = 0.5
C = 0.5
R_MOLIERE = 2.2  # cm
X0 = 0.89        # cm

def analytical_shower(r, z, E0):
    """
    Analityczny model kaskady: Profil podłużny (Gamma) * Profil poprzeczny (Gauss)
    Zwraca gęstość depozycji energii w MeV/cm^3.
    """
    # 1. Profil podłużny (Rossi)
    y = E0 / E_CRIT
    a_true = b_true * np.log(y) + C
    
    # Funkcja Gamma dla profilu podłużnego
    # (używamy małego epsilona z+1e-3, żeby nie wywaliło błędu dla z=0)
    longitudinal = E0 * (b_true**a_true) / gamma(a_true) * (z + 1e-3)**(a_true - 1) * np.exp(-b_true * z)
    
    # 2. Profil poprzeczny (Rozmycie radialne zależne od promienia Moliere'a)
    # shower rozszerza się delikatnie wraz z głębokością z
    sigma_r = (R_MOLIERE / 2.0) * (1.0 + 0.05 * z) 
    lateral = (1.0 / (2.0 * np.pi * sigma_r**2)) * np.exp(-(r**2) / (2.0 * sigma_r**2))
    
    # Gęstość energii dE/dV
    return longitudinal * lateral

def main():
    # Tworzymy katalog na dane, jeśli nie istnieje
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Wygenerujemy np. 5 różnych runów dla różnych energii początkowych E0
    np.random.seed(42)
    sample_energies = [25.0, 50.0, 100.0, 150.0, 200.0]  # MeV (w przedziale z config.py)
    
    # Rozdzielczość siatki detektora (biny)
    num_r = 30
    num_z = 40
    
    # Środki binów (tak jak opisano w io.py)
    r_centers = np.linspace(0.1, config.R_MAX, num_r)
    z_centers = np.linspace(0.1, config.Z_MAX, num_z)
    
    print("Generowanie sztucznych danych treningowych...")
    
    for i, E0 in enumerate(sample_energies):
        # Tworzymy pustą macierz na dEdV (Nr, Nz)
        dEdV = np.zeros((num_r, num_z))
        
        # Wypełniamy macierz wartościami z modelu analitycznego + dodajemy lekki szum
        # żeby symulować statystykę Monte Carlo z Geanta
        for ir, r in enumerate(r_centers):
            for iz, z in enumerate(z_centers):
                val = analytical_shower(r, z, E0)
                # Dodajemy 5% szumu gaussowskiego
                noise = np.random.normal(0, 0.05 * val)
                dEdV[ir, iz] = max(0.0, val + noise)  # gęstość nie może być ujemna
                
        # Zapisujemy plik za pomocą Waszej funkcji z interfejsu
        file_path = data_dir / f"g4_run_E_{int(E0)}MeV.npz"
        save_run(file_path, r_centers, z_centers, dEdV, E0)
        print(f"-> Zapisano: {file_path} (E0 = {E0} MeV)")

    print("\nGotowe! Możesz teraz uruchomić: python -m pinn.train")

if __name__ == "__main__":
    main()