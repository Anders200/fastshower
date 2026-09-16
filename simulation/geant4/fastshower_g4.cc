// fastshower_g4 -- headless, SLURM-array-friendly G4 application.
//
// Usage:
//   fastshower_g4 --config <run_config.json> --energy <MeV> --output <path.g4bin>
//
// The energy and output path come from CLI (so a SLURM array task can select
// one E0 per task). Everything else (geometry, binning, particle, material)
// comes from the JSON config -- the single source of truth shared with the
// Python pipeline side. See simulation/geant4/config/run_config.json.

#include "G4RunManagerFactory.hh"
#include "G4UImanager.hh"
#include "FTFP_BERT.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"

#include "DetectorConstruction.hh"
#include "ActionInitialization.hh"

#include <nlohmann/json.hpp>
#include <fstream>
#include <iostream>
#include <string>
#include <cstdlib>

using json = nlohmann::json;

struct CliArgs {
    std::string configPath, outputPath;
    double energyMeV = -1.0;
    int seedOverride = -1;
};

static CliArgs ParseArgs(int argc, char** argv) {
    CliArgs args;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        auto next = [&]() -> std::string {
            if (i+1 >= argc) { std::cerr << "Missing value for: " << a << "\n"; std::exit(1); }
            return argv[++i];
        };
        if      (a == "--config")  args.configPath  = next();
        else if (a == "--energy")  args.energyMeV   = std::stod(next());
        else if (a == "--output")  args.outputPath   = next();
        else if (a == "--seed")    args.seedOverride = std::stoi(next());
        else { std::cerr << "Unknown arg: " << a << "\n"; std::exit(1); }
    }
    if (args.configPath.empty() || args.energyMeV < 0 || args.outputPath.empty()) {
        std::cerr << "Usage: fastshower_g4 --config <cfg.json> --energy <MeV> --output <path.g4bin> [--seed <int>]\n";
        std::exit(1);
    }
    return args;
}

int main(int argc, char** argv) {
    CliArgs args = ParseArgs(argc, argv);

    std::ifstream cfgFile(args.configPath);
    if (!cfgFile.is_open()) { std::cerr << "Cannot open: " << args.configPath << "\n"; return 1; }
    json cfg; cfgFile >> cfg;

    std::string particle = cfg["particle"].get<std::string>();
    std::string material = cfg["material"].get<std::string>();
    double radiusCm  = cfg["geometry"]["radius_cm"].get<double>();
    double depthCm   = cfg["geometry"]["depth_cm"].get<double>();
    int nR           = cfg["binning"]["n_r"].get<int>();
    int nZ           = cfg["binning"]["n_z"].get<int>();
    double x0Cm      = cfg["beam"]["x0_cm"].get<double>();
    double y0Cm      = cfg["beam"]["y0_cm"].get<double>();
    double zStartCm  = cfg["beam"]["z_start_cm"].get<double>();
    int nEvents      = cfg["n_events_per_energy"].get<int>();
    int seedBase     = cfg["random_seed_base"].get<int>();

    int seed = (args.seedOverride >= 0) ? args.seedOverride
                                         : seedBase + static_cast<int>(args.energyMeV);
    G4Random::setTheSeed(seed);

    std::cout << "[fastshower_g4] " << particle << " in " << material
              << " E0=" << args.energyMeV << " MeV"
              << " n_events=" << nEvents
              << " seed=" << seed
              << " -> " << args.outputPath << "\n";

    auto* runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial);

    auto* detector = new DetectorConstruction(material, radiusCm, depthCm);
    runManager->SetUserInitialization(detector);
    runManager->SetUserInitialization(new FTFP_BERT());
    runManager->SetUserInitialization(new ActionInitialization(
        detector, particle, material, args.energyMeV,
        x0Cm, y0Cm, zStartCm, nR, nZ, args.outputPath));

    runManager->Initialize();
    runManager->BeamOn(nEvents);

    delete runManager;
    return 0;
}
