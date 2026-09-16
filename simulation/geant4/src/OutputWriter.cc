#include "OutputWriter.hh"
#include <fstream>
#include <cstring>
#include <cstdint>

void OutputWriter::WriteBinary(const G4String& path, const RunData& data,
                                const G4String& particleName,
                                const G4String& materialName,
                                G4double energyMeV) {
    std::ofstream out(path, std::ios::binary);
    if (!out.is_open())
        G4Exception("OutputWriter::WriteBinary", "CannotOpenFile", FatalException,
                    ("Could not open: " + path).c_str());

    int32_t nR = data.GetNR(), nZ = data.GetNZ();
    double radius = data.GetRadius(), depth = data.GetDepth(), E0 = energyMeV;
    int64_t nEvents = data.GetNEventsAccumulated();

    out.write(reinterpret_cast<const char*>(&nR),     sizeof(nR));
    out.write(reinterpret_cast<const char*>(&nZ),     sizeof(nZ));
    out.write(reinterpret_cast<const char*>(&radius), sizeof(radius));
    out.write(reinterpret_cast<const char*>(&depth),  sizeof(depth));
    out.write(reinterpret_cast<const char*>(&E0),     sizeof(E0));
    out.write(reinterpret_cast<const char*>(&nEvents),sizeof(nEvents));

    const auto& rE = data.GetREdges();
    const auto& zE = data.GetZEdges();
    const auto& ed = data.GetEdepSum();
    out.write(reinterpret_cast<const char*>(rE.data()), rE.size()*sizeof(double));
    out.write(reinterpret_cast<const char*>(zE.data()), zE.size()*sizeof(double));
    out.write(reinterpret_cast<const char*>(ed.data()), ed.size()*sizeof(double));

    char buf[64];
    std::memset(buf, 0, 64); std::strncpy(buf, particleName.c_str(), 63);
    out.write(buf, 64);
    std::memset(buf, 0, 64); std::strncpy(buf, materialName.c_str(), 63);
    out.write(buf, 64);
}
