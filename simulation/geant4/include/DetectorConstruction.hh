#ifndef DETECTOR_CONSTRUCTION_HH
#define DETECTOR_CONSTRUCTION_HH

#include "G4VUserDetectorConstruction.hh"
#include "globals.hh"

class G4LogicalVolume;

class DetectorConstruction : public G4VUserDetectorConstruction {
public:
    DetectorConstruction(const G4String& materialName,
                          G4double radiusCm, G4double depthCm);
    ~DetectorConstruction() override = default;

    G4VPhysicalVolume* Construct() override;

    G4LogicalVolume* GetScoringVolume() const { return fScoringVolume; }
    G4double GetRadius() const { return fRadius; }
    G4double GetDepth()  const { return fDepth;  }

private:
    G4String fMaterialName;
    G4double fRadius, fDepth;
    G4LogicalVolume* fScoringVolume = nullptr;
};

#endif
