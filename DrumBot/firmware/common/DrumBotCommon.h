#pragma once

#include <Arduino.h>
#if defined(ESP32)
#include <esp32-hal-bt-mem.h>
#include <esp_log.h>
#include <esp_system.h>
#endif
#include <Control_Surface.h>
#if defined(DRUMBOT_USE_BLUEDROID_BLE) && defined(ESP32)
#include <MIDI_Interfaces/GenericBLEMIDI_Interface.hpp>
#include <MIDI_Interfaces/BLEMIDI/ESP32BluedroidBackend.hpp>
#else
#include <MIDI_Interfaces/BluetoothMIDI_Interface.hpp>
#endif

namespace drumbot {

// ── Fixed servo constants (same for every bot) ──────────────────────
// Only upUs varies per bot — everything else is derived or constant.
static constexpr uint16_t kStrokeOffsetUs = 450;    // downUs = upUs - 450
static constexpr uint32_t kStickDownUs    = 80000;  // 80 ms hold in strike position
static constexpr uint32_t kStickUpUs      = 25000;  // 25 ms cooldown before next hit
static constexpr uint32_t kStickCycleUs   = kStickDownUs + kStickUpUs;

struct Config {
  uint8_t numServos;
  uint8_t servoPins[2];
  uint8_t pwmChannels[2];
  uint16_t upUs[2];           // only calibration-sensitive value
  uint32_t servoPwmFreq;
  uint8_t servoPwmBits;
  bool requireCh10;
};

using NoteMatcher = bool (*)(uint8_t note);

#if defined(DRUMBOT_USE_BLUEDROID_BLE) && defined(ESP32)
using DrumBotBLEInterface = GenericBLEMIDI_Interface<ESP32BluedroidBackend>;
#else
using DrumBotBLEInterface = BluetoothMIDI_Interface;
#endif
static DrumBotBLEInterface midi_ble;
static Config cfg{};
static NoteMatcher noteMatcher = nullptr;

static bool servoAttached[2] = {false, false};
static bool stickIsDown[2] = {false, false};
static uint32_t lastHitUs[2] = {0, 0};
static bool wasConnected = false;
static uint32_t lastActiveSenseMs = 0;
static uint32_t connectedAtMs = 0;

static constexpr uint32_t kActiveSenseIntervalMs = 1000;
static constexpr uint32_t kConnectGraceMs = 500;

// Calibration CCs: select servo → coarse → fine (triggers update), test hit.
static constexpr uint8_t kCCServoSelect  = 110;
static constexpr uint8_t kCCValueCoarse  = 111;
static constexpr uint8_t kCCValueFine    = 112;
static constexpr uint8_t kCCTestHit      = 113;

static uint8_t calibServo = 0;
static uint8_t calibCoarse = 0;

static inline uint8_t statusLedPin() {
#ifdef LED_BUILTIN
  return LED_BUILTIN;
#else
  return 2;
#endif
}

static inline uint32_t servoPeriodUs() { return 1000000UL / cfg.servoPwmFreq; }
static inline uint32_t maxDuty() { return (1u << cfg.servoPwmBits) - 1u; }

static inline uint32_t usToDuty(uint16_t us) {
  return (static_cast<uint32_t>(us) * maxDuty() + (servoPeriodUs() / 2)) / servoPeriodUs();
}

static inline void writeServoUS(uint8_t i, uint16_t pulseUs) {
  const uint32_t duty = usToDuty(pulseUs);
#if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
  ledcWriteChannel(cfg.pwmChannels[i], duty);
#else
  ledcWrite(cfg.pwmChannels[i], duty);
#endif
}

static inline uint16_t downUs(uint8_t i) { return cfg.upUs[i] - kStrokeOffsetUs; }

static bool attachServo(uint8_t i) {
#if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
  const bool ok = ledcAttachChannel(cfg.servoPins[i], cfg.servoPwmFreq, cfg.servoPwmBits,
                                    cfg.pwmChannels[i]);
#else
  ledcSetup(cfg.pwmChannels[i], cfg.servoPwmFreq, cfg.servoPwmBits);
  ledcAttachPin(cfg.servoPins[i], cfg.pwmChannels[i]);
  const bool ok = true;
#endif

  servoAttached[i] = ok;
  if (ok) {
    writeServoUS(i, cfg.upUs[i]);
    stickIsDown[i] = false;
  }
  return ok;
}

static void detachServo(uint8_t i) {
  if (!servoAttached[i]) return;

#if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
  ledcDetach(cfg.servoPins[i]);
#else
  ledcDetachPin(cfg.servoPins[i]);
#endif

  servoAttached[i] = false;
  stickIsDown[i] = false;
}

static inline bool ready(uint8_t i, uint32_t nowUs) {
  return servoAttached[i] && static_cast<uint32_t>(nowUs - lastHitUs[i]) >= kStickCycleUs;
}

static inline void hit(uint8_t i, uint32_t nowUs) {
  lastHitUs[i] = nowUs;
  stickIsDown[i] = true;
  writeServoUS(i, downUs(i));
}

static inline void serviceReturns(uint32_t nowUs) {
  for (uint8_t i = 0; i < cfg.numServos; ++i) {
    if (!servoAttached[i] || !stickIsDown[i]) continue;
    if (static_cast<uint32_t>(nowUs - lastHitUs[i]) >= kStickDownUs) {
      writeServoUS(i, cfg.upUs[i]);
      stickIsDown[i] = false;
    }
  }
}

static inline bool hitPreferred() {
  const uint32_t nowUs = micros();

  if (ready(0, nowUs)) {
    hit(0, nowUs);
    return true;
  }

  if (cfg.numServos == 2 && ready(1, nowUs)) {
    hit(1, nowUs);
    return true;
  }

  return false;
}

static void attachAll() {
  const uint32_t nowUs = micros();
  for (uint8_t i = 0; i < cfg.numServos; ++i) {
    if (attachServo(i)) {
      lastHitUs[i] = nowUs - kStickCycleUs;
      Serial.print("attach servo");
      Serial.print(i);
      Serial.println(" OK");
    } else {
      Serial.print("attach servo");
      Serial.print(i);
      Serial.println(" FAIL");
    }
  }
}

static void detachAll() {
  for (uint8_t i = 0; i < cfg.numServos; ++i) {
    detachServo(i);
  }
}

static void printConfig() {
  Serial.println("--- config ---");
  for (uint8_t i = 0; i < cfg.numServos; ++i) {
    Serial.print("  servo "); Serial.print(i);
    Serial.print(": upUs="); Serial.print(cfg.upUs[i]);
    Serial.print("  downUs="); Serial.println(downUs(i));
  }
  Serial.print("  strokeOffset="); Serial.print(kStrokeOffsetUs);
  Serial.print("  stickDown="); Serial.print(kStickDownUs / 1000);
  Serial.print("ms  stickUp="); Serial.print(kStickUpUs / 1000);
  Serial.println("ms");
}

struct CallbackHandler : FineGrainedMIDI_Callbacks<CallbackHandler> {
  void onNoteOn(Channel ch, uint8_t note, uint8_t vel, Cable) {
    if (vel == 0) return;
    if (cfg.requireCh10 && ch != Channel_10) return;

    Serial.print("RX note=");
    Serial.print(note);
    Serial.print(" vel=");
    Serial.print(vel);

    if (noteMatcher && noteMatcher(note)) {
      const bool fired = hitPreferred();
      if (fired) {
        Serial.println(" HIT");
      } else {
        Serial.print(" BLOCKED attached0=");
        Serial.print(servoAttached[0] ? 1 : 0);
        Serial.print(" attached1=");
        Serial.print((cfg.numServos == 2 && servoAttached[1]) ? 1 : 0);
        Serial.print(" down0=");
        Serial.print(stickIsDown[0] ? 1 : 0);
        Serial.print(" down1=");
        Serial.println((cfg.numServos == 2 && stickIsDown[1]) ? 1 : 0);
      }
    } else {
      Serial.println(" skip");
    }
  }

  void onNoteOff(Channel, uint8_t, uint8_t, Cable) {}

  void onControlChange(Channel, uint8_t cc, uint8_t val, Cable) {
    switch (cc) {
      case kCCServoSelect:
        calibServo = val < cfg.numServos ? val : 0;
        if (val == 127) printConfig();
        break;
      case kCCValueCoarse:
        calibCoarse = val;
        break;
      case kCCValueFine: {
        uint16_t upVal = (static_cast<uint16_t>(calibCoarse) << 7) | val;
        cfg.upUs[calibServo] = upVal;
        if (servoAttached[calibServo] && !stickIsDown[calibServo]) {
          writeServoUS(calibServo, upVal);
        }
        Serial.print("CALIB servo");
        Serial.print(calibServo);
        Serial.print(" upUs=");
        Serial.print(upVal);
        Serial.print(" -> downUs=");
        Serial.println(downUs(calibServo));
        break;
      }
      case kCCTestHit: {
        uint8_t servo = val < cfg.numServos ? val : 0;
        const uint32_t nowUs = micros();
        lastHitUs[servo] = nowUs - kStickCycleUs;
        hit(servo, nowUs);
        break;
      }
      default: break;
    }
  }
};

static CallbackHandler callbacks;

static void begin(const char *bleName, const Config &config, NoteMatcher matcher) {
  cfg = config;
  noteMatcher = matcher;

  pinMode(statusLedPin(), OUTPUT);
  digitalWrite(statusLedPin(), LOW);

  Serial.begin(115200);
#if defined(ESP32)
  esp_log_level_set("CS-BLEMIDI", ESP_LOG_INFO);
  Serial.print("ESP reset reason: ");
  Serial.println(static_cast<int>(esp_reset_reason()));
#if defined(DRUMBOT_USE_BLUEDROID_BLE)
  Serial.println("BLE backend: Bluedroid");
#else
  Serial.println("BLE backend: NimBLE");
#endif
#endif

  // 30-120 ms connection interval (BLE units of 1.25 ms).
  midi_ble.ble_settings.connection_interval.minimum = 0x0018;
  midi_ble.ble_settings.connection_interval.maximum = 0x0060;
  midi_ble.ble_settings.initiate_security = false;
  midi_ble.setName(bleName);
  MIDI_Interface::beginAll();
  midi_ble.setCallbacks(callbacks);

  Serial.print("BLE MIDI ready: ");
  Serial.println(bleName);
  printConfig();
}

static void update() {
  MIDI_Interface::updateAll();

  const bool connected = midi_ble.isConnected();
  const uint32_t nowMs = millis();
  if (connected != wasConnected) {
    wasConnected = connected;
    digitalWrite(statusLedPin(), connected ? HIGH : LOW);

    Serial.print("[");
    Serial.print(nowMs);
    Serial.print(" ms] BLE ");
    Serial.println(connected ? "connected" : "disconnected");

    if (connected) {
      attachAll();
      connectedAtMs = nowMs;
      lastActiveSenseMs = nowMs;
    } else {
      detachAll();
    }
  }

  if (connected && static_cast<uint32_t>(nowMs - connectedAtMs) >= kConnectGraceMs) {
    if (static_cast<uint32_t>(nowMs - lastActiveSenseMs) >= kActiveSenseIntervalMs) {
      lastActiveSenseMs = nowMs;
      midi_ble.send(static_cast<cs::RealTimeMessage>(cs::RealTimeMessage::ActiveSensing));
    }
  }

  serviceReturns(micros());
}

}  // namespace drumbot
