#ifndef STEPPING_ACTION_HH
#define STEPPING_ACTION_HH

#include "G4UserSteppingAction.hh"

class DetectorConstruction;
class RunData;

class SteppingAction : public G4UserSteppingAction {
public:
    SteppingAction(const DetectorConstruction* detector, RunData* runData);
    ~SteppingAction() override = default;
    void UserSteppingAction(const G4Step* step) override;

private:
    const DetectorConstruction* fDetector;
    RunData* fRunData;
};

#endif
