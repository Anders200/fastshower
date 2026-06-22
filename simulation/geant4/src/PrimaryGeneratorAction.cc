#include "PrimaryGeneratorAction.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4ParticleDefinition.hh"
#include "G4SystemOfUnits.hh"
#include "G4Event.hh"

PrimaryGeneratorAction::PrimaryGeneratorAction(const G4String& particleName,
                                                G4double energyMeV,
                                                G4double x0Cm, G4double y0Cm,
                                                G4double zStartCm) {
    fParticleGun = new G4ParticleGun(1);
    G4ParticleDefinition* particle =
        G4ParticleTable::GetParticleTable()->FindParticle(particleName);
    if (!particle)
        G4Exception("PrimaryGeneratorAction", "ParticleNotFound", FatalException,
                    ("Unknown particle: " + particleName).c_str());
    fParticleGun->SetParticleDefinition(particle);
    fParticleGun->SetParticleEnergy(energyMeV * MeV);
    fParticleGun->SetParticleMomentumDirection(G4ThreeVector(0, 0, 1));
    fParticleGun->SetParticlePosition(G4ThreeVector(x0Cm*cm, y0Cm*cm, zStartCm*cm));
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() { delete fParticleGun; }

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event) {
    fParticleGun->GeneratePrimaryVertex(event);
}
