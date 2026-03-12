#include "../../common/DrumBotCommon.h"

using namespace drumbot;

static bool shouldTrigger(uint8_t note) {
  switch (note) {
    case 37:
    case 38:
    case 39:
    case 40:
      return true;

    default:
      return false;
  }
}

static constexpr Config SNARE_CONFIG = {
    .numServos = 2,
    .servoPins = {5, 4},
    .pwmChannels = {0, 1},
    .upUs = {1650, 1700},
    .servoPwmFreq = 50,
    .servoPwmBits = 14,
    .requireCh10 = false,
};

void setup() { begin("RobOrchestra_Snare", SNARE_CONFIG, shouldTrigger); }

void loop() { update(); }
