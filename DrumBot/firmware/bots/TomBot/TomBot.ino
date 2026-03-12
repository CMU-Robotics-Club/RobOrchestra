#include "../../common/DrumBotCommon.h"

using namespace drumbot;

#define ROUTE_BD_TO_TOM 1

static bool shouldTrigger(uint8_t note) {
  switch (note) {
    case 41:
    case 43:
    case 45:
    case 47:
    case 48:
    case 50:
      return true;

#if ROUTE_BD_TO_TOM
    case 35:
    case 36:
      return true;
#endif

    default:
      return false;
  }
}

static constexpr Config TOM_CONFIG = {
    .numServos = 2,
    .servoPins = {5, 4},
    .pwmChannels = {0, 1},
    .upUs = {1500, 1700},
    .servoPwmFreq = 50,
    .servoPwmBits = 14,
    .requireCh10 = false,
};

void setup() { begin("RobOrchestra_Tom", TOM_CONFIG, shouldTrigger); }

void loop() { update(); }
