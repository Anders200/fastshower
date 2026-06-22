#include "RunAction.hh"
#include "RunData.hh"
#include "OutputWriter.hh"
#include "G4Run.hh"

RunAction::RunAction(G4double radiusCm, G4double depthCm, G4int nR, G4int nZ,
                      const G4String& particleName, const G4String& materialName,
                      G4double energyMeV, const G4String& outputPath)
    : fParticleName(particleName), fMaterialName(materialName),
      fOutputPath(outputPath), fEnergyMeV(energyMeV) {
    fRunData = new RunData(radiusCm, depthCm, nR, nZ);
}

RunAction::~RunAction() { delete fRunData; }

void RunAction::EndOfRunAction(const G4Run* run) {
    // Sequential build assumed (one SLURM task = one process, one G4 run).
    // For MT builds, add worker->master RunData merging here before writing.
    G4int n = run->GetNumberOfEvent();
    for (G4int i = 0; i < n; ++i) fRunData->IncrementEventCount();

    OutputWriter::WriteBinary(fOutputPath, *fRunData,
                               fParticleName, fMaterialName, fEnergyMeV);
    G4cout << "[RunAction] wrote " << fOutputPath
           << " (" << n << " events)" << G4endl;
}
