#include <iomanip>
#include <iostream>
#include <string>
#include "embedded_inference.h"

int main(int argc, char** argv) {
  if (argc == 2 && std::string(argv[1]) == "--info") {
    std::cout << "Model: " << ms_monitor_ai::kModelVersion << "\n";
    std::cout << "Model bytes: " << ms_monitor_ai::kModelBytes << "\n";
    return 0;
  }
  float air, humidity, grain;
  std::cout << std::setprecision(9);
  while (std::cin >> air >> humidity >> grain) {
    const auto result = ms_monitor_ai::predictRisk(air, humidity, grain);
    if (!result.valid) { std::cout << "invalid\n"; continue; }
    std::cout << result.classIndex;
    for (const float value : result.probabilities) std::cout << ' ' << value;
    std::cout << ' ' << result.riskScore << ' ' << result.confidence << '\n';
  }
}
