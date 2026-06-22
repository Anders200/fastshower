#include "RunData.hh"
#include <cmath>
#include <algorithm>

RunData::RunData(G4double radiusCm, G4double depthCm, G4int nR, G4int nZ)
    : fRadius(radiusCm), fDepth(depthCm), fNR(nR), fNZ(nZ) {

    // r: sqrt-spaced -> denser near r=0 (shower core)
    fREdges.resize(fNR + 1);
    for (G4int i = 0; i <= fNR; ++i)
        fREdges[i] = fRadius * std::sqrt(static_cast<G4double>(i) / fNR);

    // z: denser in first 40% of depth (shower max region), coarser after
    fZEdges.resize(fNZ + 1);
    G4int nDense  = static_cast<G4int>(0.6 * fNZ);
    G4int nCoarse = fNZ - nDense;
    G4double zBreak = 0.4 * fDepth;

    for (G4int i = 0; i <= nDense; ++i)
        fZEdges[i] = zBreak * (static_cast<G4double>(i) / nDense);
    for (G4int i = 1; i <= nCoarse; ++i)
        fZEdges[nDense + i] = zBreak + (fDepth - zBreak) * (static_cast<G4double>(i) / nCoarse);

    fEdepSum.assign(static_cast<size_t>(fNR) * fNZ, 0.0);
}

G4int RunData::FindRBin(G4double r_cm) const {
    if (r_cm < 0 || r_cm >= fRadius) return -1;
    auto it = std::upper_bound(fREdges.begin(), fREdges.end(), r_cm);
    G4int bin = static_cast<G4int>(it - fREdges.begin()) - 1;
    return (bin >= 0 && bin < fNR) ? bin : -1;
}

G4int RunData::FindZBin(G4double z_cm) const {
    if (z_cm < 0 || z_cm >= fDepth) return -1;
    auto it = std::upper_bound(fZEdges.begin(), fZEdges.end(), z_cm);
    G4int bin = static_cast<G4int>(it - fZEdges.begin()) - 1;
    return (bin >= 0 && bin < fNZ) ? bin : -1;
}

void RunData::AddEdep(G4double r_cm, G4double z_cm, G4double edep_MeV) {
    G4int ir = FindRBin(r_cm);
    G4int iz = FindZBin(z_cm);
    if (ir < 0 || iz < 0) return;
    fEdepSum[static_cast<size_t>(ir) * fNZ + iz] += edep_MeV;
}

void RunData::Merge(const RunData& other) {
    for (size_t i = 0; i < fEdepSum.size(); ++i)
        fEdepSum[i] += other.fEdepSum[i];
    fNEvents += other.fNEvents;
}
