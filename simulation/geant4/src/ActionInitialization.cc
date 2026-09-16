#include "ActionInitialization.hh"
#include "DetectorConstruction.hh"
#include "PrimaryGeneratorAction.hh"
#include "RunAction.hh"
#include "SteppingAction.hh"
#include "G4SystemOfUnits.hh"

ActionInitialization::ActionInitialization(const DetectorConstruction* detector,
                                            const G4String& particleName,
                                            const G4String& materialName,
                                            G4double energyMeV,
                                            G4double x0Cm, G4double y0Cm,
                                            G4double zStartCm,
                                            G4int nR, G4int nZ,
                                            const G4String& outputPath)
    : fDetector(detector), fParticleName(particleName), fMaterialName(materialName),
      fOutputPath(outputPath), fEnergyMeV(energyMeV), fX0Cm(x0Cm), fY0Cm(y0Cm),
      fZStartCm(zStartCm), fNR(nR), fNZ(nZ) {}

void ActionInitialization::BuildForMaster() const {
    SetUserAction(new RunAction(
        fDetector->GetRadius()/cm, fDetector->GetDepth()/cm,
        fNR, fNZ, fParticleName, fMaterialName, fEnergyMeV, fOutputPath));
}

void ActionInitialization::Build() const {
    SetUserAction(new PrimaryGeneratorAction(
        fParticleName, fEnergyMeV, fX0Cm, fY0Cm, fZStartCm));

    auto* runAction = new RunAction(
        fDetector->GetRadius()/cm, fDetector->GetDepth()/cm,
        fNR, fNZ, fParticleName, fMaterialName, fEnergyMeV, fOutputPath);
    SetUserAction(runAction);
    SetUserAction(new SteppingAction(fDetector, runAction->GetRunData()));
}
