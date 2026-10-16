#pragma once
#include <math.h>
#include "risk_model.h"

namespace ms_monitor_ai {
struct Prediction {
  bool valid;
  unsigned classIndex;
  float probabilities[kClassCount];
  float riskScore;
  float confidence;
};

inline Prediction predictRisk(float air, float humidity, float grain) {
  Prediction result = {};
  if (!isfinite(air) || !isfinite(humidity) || !isfinite(grain)
      || air < -40 || air > 80 || humidity < 0 || humidity > 100 || grain < 0 || grain > 1024) return result;
  const float features[kFeatureCount] = {air, humidity, grain, grain - air};
  double totals[kClassCount] = {};
  for (unsigned tree = 0; tree < kTreeCount; ++tree) {
    int16_t index = kRoots[tree];
    while (kNodes[index].feature >= 0) {
      const RiskNode& node = kNodes[index];
      index = features[node.feature] <= node.threshold ? node.left : node.right;
    }
    for (unsigned cls = 0; cls < kClassCount; ++cls) totals[cls] += kNodes[index].probabilities[cls];
  }
  double score = 0;
  for (unsigned cls = 0; cls < kClassCount; ++cls) {
    totals[cls] /= kTreeCount;
    result.probabilities[cls] = static_cast<float>(totals[cls]);
    if (totals[cls] > totals[result.classIndex]) result.classIndex = cls;
    score += totals[cls] * kRiskWeights[cls];
  }
  result.riskScore = static_cast<float>(score);
  result.confidence = static_cast<float>(totals[result.classIndex]);
  result.valid = true;
  return result;
}
}  // namespace ms_monitor_ai
