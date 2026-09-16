#ifndef RUN_ACTION_HH
#define RUN_ACTION_HH

#include "G4UserRunAction.hh"
#include "globals.hh"

class RunData;
class G4Run;

class RunAction : public G4UserRunAction {
public:
    RunAction(G4double radiusCm, G4double depthCm, G4int nR, G4int nZ,
              const G4String& particleName, const G4String& materialName,
              G4double energyMeV, const G4String& outputPath);
    ~RunAction() override;

    void BeginOfRunAction(const G4Run*) override {}
    void EndOfRunAction(const G4Run* run) override;

    RunData* GetRunData() const { return fRunData; }

private:
    RunData*  fRunData;
    G4String  fParticleName, fMaterialName, fOutputPath;
    G4double  fEnergyMeV;
};

#endif
