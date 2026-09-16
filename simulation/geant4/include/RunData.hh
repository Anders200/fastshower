#ifndef RUN_DATA_HH
#define RUN_DATA_HH

#include "globals.hh"
#include <vector>

// Accumulates energy deposition into a (r, z) histogram.
// Binning: sqrt-spaced in r (denser near r=0), two-segment linear in z
// (denser in first 40% of depth where shower max lives).
// z is stored in RAW CM internally -- convert_to_npz.py divides by X0_cm
// before writing the .npz, matching interface/io.py's z-in-X0-units contract.
class RunData {
public:
    RunData(G4double radiusCm, G4double depthCm, G4int nR, G4int nZ);

    void AddEdep(G4double r_cm, G4double z_cm, G4double edep_MeV);
    void Merge(const RunData& other);
    void IncrementEventCount() { ++fNEvents; }

    const std::vector<G4double>& GetREdges()  const { return fREdges; }
    const std::vector<G4double>& GetZEdges()  const { return fZEdges; }
    const std::vector<G4double>& GetEdepSum() const { return fEdepSum; }

    G4int    GetNR()                 const { return fNR; }
    G4int    GetNZ()                 const { return fNZ; }
    G4double GetRadius()             const { return fRadius; }
    G4double GetDepth()              const { return fDepth; }
    G4long   GetNEventsAccumulated() const { return fNEvents; }

private:
    G4double fRadius, fDepth;
    G4int    fNR, fNZ;
    std::vector<G4double> fREdges, fZEdges, fEdepSum;
    G4long   fNEvents = 0;

    G4int FindRBin(G4double r_cm) const;
    G4int FindZBin(G4double z_cm) const;
};

#endif
