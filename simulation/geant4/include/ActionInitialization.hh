#ifndef ACTION_INITIALIZATION_HH
#define ACTION_INITIALIZATION_HH

#include "G4VUserActionInitialization.hh"
#include "globals.hh"

class DetectorConstruction;

class ActionInitialization : public G4VUserActionInitialization {
public:
    ActionInitialization(const DetectorConstruction* detector,
                          const G4String& particleName, const G4String& materialName,
                          G4double energyMeV, G4double x0Cm, G4double y0Cm,
                          G4double zStartCm, G4int nR, G4int nZ,
                          const G4String& outputPath);
    ~ActionInitialization() override = default;
    void Build() const override;
    void BuildForMaster() const override;

private:
    const DetectorConstruction* fDetector;
    G4String fParticleName, fMaterialName, fOutputPath;
    G4double fEnergyMeV, fX0Cm, fY0Cm, fZStartCm;
    G4int fNR, fNZ;
};

#endif
