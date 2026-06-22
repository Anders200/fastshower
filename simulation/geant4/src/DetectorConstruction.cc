#include "DetectorConstruction.hh"
#include "G4NistManager.hh"
#include "G4Box.hh"
#include "G4Tubs.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4SystemOfUnits.hh"
#include "G4VisAttributes.hh"
#include "G4Colour.hh"

DetectorConstruction::DetectorConstruction(const G4String& materialName,
                                            G4double radiusCm, G4double depthCm)
    : fMaterialName(materialName), fRadius(radiusCm*cm), fDepth(depthCm*cm) {}

G4VPhysicalVolume* DetectorConstruction::Construct() {
    G4NistManager* nist = G4NistManager::Instance();

    G4double worldSize = 1.5 * std::max(fRadius, fDepth);
    G4Material* worldMat = nist->FindOrBuildMaterial("G4_AIR");
    G4Box* solidWorld = new G4Box("World", worldSize, worldSize, worldSize);
    G4LogicalVolume* logicWorld = new G4LogicalVolume(solidWorld, worldMat, "World");
    G4VPhysicalVolume* physWorld =
        new G4PVPlacement(nullptr, G4ThreeVector(), logicWorld, "World", nullptr, false, 0);

    G4Material* caloMat = nist->FindOrBuildMaterial(fMaterialName);
    if (!caloMat)
        G4Exception("DetectorConstruction::Construct", "MaterialNotFound", FatalException,
                    ("Could not find material: " + fMaterialName).c_str());

    G4Tubs* solidCalo = new G4Tubs("Calorimeter", 0.0, fRadius, fDepth/2.0, 0.0, 360.0*deg);
    G4LogicalVolume* logicCalo = new G4LogicalVolume(solidCalo, caloMat, "Calorimeter");

    // Front face at z=0, beam enters from z<0
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, fDepth/2.0), logicCalo,
                       "Calorimeter", logicWorld, false, 0);

    G4VisAttributes* vis = new G4VisAttributes(G4Colour(0.2, 0.4, 0.9, 0.4));
    vis->SetForceSolid(true);
    logicCalo->SetVisAttributes(vis);

    fScoringVolume = logicCalo;
    return physWorld;
}
