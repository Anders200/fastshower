#include "SteppingAction.hh"
#include "DetectorConstruction.hh"
#include "RunData.hh"
#include "G4Step.hh"
#include "G4LogicalVolume.hh"
#include "G4SystemOfUnits.hh"

SteppingAction::SteppingAction(const DetectorConstruction* detector, RunData* runData)
    : fDetector(detector), fRunData(runData) {}

void SteppingAction::UserSteppingAction(const G4Step* step) {
    G4double edep = step->GetTotalEnergyDeposit();
    if (edep <= 0.0) return;

    G4LogicalVolume* volume =
        step->GetPreStepPoint()->GetTouchableHandle()->GetVolume()->GetLogicalVolume();
    if (volume != fDetector->GetScoringVolume()) return;

    G4ThreeVector mid = 0.5 * (step->GetPreStepPoint()->GetPosition()
                              + step->GetPostStepPoint()->GetPosition());

    G4double r_cm = std::sqrt(mid.x()*mid.x() + mid.y()*mid.y()) / cm;
    G4double z_cm = mid.z() / cm;  // raw cm -- converted to X0 units in convert_to_npz.py

    fRunData->AddEdep(r_cm, z_cm, edep / MeV);
}
