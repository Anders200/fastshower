#ifndef OUTPUT_WRITER_HH
#define OUTPUT_WRITER_HH

#include "globals.hh"
#include "RunData.hh"

// Writes histogram to a simple binary file (.g4bin).
// No external C++ dependencies -- convert_to_npz.py handles the
// .g4bin -> .npz conversion including the z: cm -> X0 unit conversion.
//
// Binary layout:
//   int32   nR
//   int32   nZ
//   float64 radius_cm
//   float64 depth_cm
//   float64 E0_MeV
//   int64   n_events
//   float64 r_edges[nR+1]
//   float64 z_edges[nZ+1]    (in cm, converted to X0 by Python converter)
//   float64 edep_sum[nR*nZ]  (r-major: idx = ir*nZ + iz)
//   char    particle_name[64]
//   char    material_name[64]
namespace OutputWriter {
    void WriteBinary(const G4String& path, const RunData& data,
                      const G4String& particleName, const G4String& materialName,
                      G4double energyMeV);
}

#endif
