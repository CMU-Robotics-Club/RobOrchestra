#include "../../common/DrumBotCommon.h"

using namespace drumbot;

#define ROUTE_HIHATS_TO_SNARE 1
#define ROUTE_CYMBALS_TO_SNARE 1

static bool shouldTrigger(uint8_t note) {
  switch (note) {
    case 37:
    case 38:
    case 39:
    case 40:
      return true;

#if ROUTE_HIHATS_TO_SNARE
    case 42:
    case 44:
    case 46:
      return true;
#endif

#if ROUTE_CYMBALS_TO_SNARE
    case 49:
    case 51:
    case 52:
    case 53:
    case 55:
    case 57:
      return true;
#endif

    default:
      return false;
  }
}

static constexpr Config SNARE_CONFIG = {
    .numServos = 1,
    .servoPins = {5, 4},
    .pwmChannels = {0, 1},
    .upUs = {1485, 1700},
    .downUs = {1035, 1250},
    .servoPwmFreq = 50,
    .servoPwmBits = 14,
    .stickDownUs = 50000,
    .stickUpUs = 25000,
    .requireCh10 = false,
    .debugPrintNotes = false,
};

void setup() { begin("RobOrchestra_Snare", SNARE_CONFIG, shouldTrigger); }

void loop() { update(); }
