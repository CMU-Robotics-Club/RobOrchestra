#pragma once

#include <Arduino.h>
#if defined(ESP32)
// Prevent Arduino core from releasing BT memory before sketch setup().
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

struct Config {
  uint8_t numServos;
  uint8_t servoPins[2];
  uint8_t pwmChannels[2];

  uint16_t upUs[2];
  uint16_t downUs[2];

  uint32_t servoPwmFreq;
  uint8_t servoPwmBits;

  uint32_t stickDownUs;
  uint32_t stickUpUs;

  bool requireCh10;
  bool debugPrintNotes;
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
static uint32_t lastStateLogMs = 0;
static uint32_t connectedAtMs = 0;

static constexpr uint32_t kActiveSenseIntervalMs = 1000;
static constexpr uint32_t kConnectGraceMs = 500;

static inline uint8_t statusLedPin() {
#ifdef LED_BUILTIN
  return LED_BUILTIN;
#else
  return 2;
#endif
}

static inline uint32_t stickCycleUs() { return cfg.stickDownUs + cfg.stickUpUs; }
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
  return servoAttached[i] && static_cast<uint32_t>(nowUs - lastHitUs[i]) >= stickCycleUs();
}

static inline void hit(uint8_t i, uint32_t nowUs) {
  lastHitUs[i] = nowUs;
  stickIsDown[i] = true;
  writeServoUS(i, cfg.downUs[i]);
}

static inline void serviceReturns(uint32_t nowUs) {
  for (uint8_t i = 0; i < cfg.numServos; ++i) {
    if (!servoAttached[i] || !stickIsDown[i]) continue;
    if (static_cast<uint32_t>(nowUs - lastHitUs[i]) >= cfg.stickDownUs) {
      writeServoUS(i, cfg.upUs[i]);
      stickIsDown[i] = false;
    }
  }
}

static inline void hitPreferred() {
  const uint32_t nowUs = micros();

  if (ready(0, nowUs)) {
    hit(0, nowUs);
    return;
  }

  if (cfg.numServos == 2 && ready(1, nowUs)) {
    hit(1, nowUs);
  }
}

static void attachAll() {
  const uint32_t nowUs = micros();
  for (uint8_t i = 0; i < cfg.numServos; ++i) {
    if (attachServo(i)) {
      lastHitUs[i] = nowUs - stickCycleUs();  // Ready immediately.
    }
  }
}

static void detachAll() {
  for (uint8_t i = 0; i < cfg.numServos; ++i) {
    detachServo(i);
  }
}

struct CallbackHandler : FineGrainedMIDI_Callbacks<CallbackHandler> {
  void onNoteOn(Channel ch, uint8_t note, uint8_t vel, Cable) {
    if (vel == 0) return;
    if (cfg.requireCh10 && ch != Channel_10) return;

    if (cfg.debugPrintNotes) {
      Serial.print("ch=");
      Serial.print(static_cast<uint8_t>(ch.getRaw()));
      Serial.print(" note=");
      Serial.println(note);
    }

    if (noteMatcher && noteMatcher(note)) {
      hitPreferred();
    }
  }

  void onNoteOff(Channel, uint8_t, uint8_t, Cable) {}
};

static CallbackHandler callbacks;

static void begin(const char *bleName, const Config &config, NoteMatcher matcher) {
  cfg = config;
  noteMatcher = matcher;

  pinMode(statusLedPin(), OUTPUT);
  digitalWrite(statusLedPin(), LOW);

  Serial.begin(115200);
#if defined(ESP32)
  // Enable backend logs so disconnect reasons are visible in serial monitor.
  esp_log_level_set("CS-BLEMIDI", ESP_LOG_INFO);
  Serial.print("ESP reset reason: ");
  Serial.println(static_cast<int>(esp_reset_reason()));
#if defined(DRUMBOT_USE_BLUEDROID_BLE)
  Serial.println("BLE backend: Bluedroid (forced)");
#else
  Serial.println("BLE backend: Default (NimBLE on ESP32-S3)");
#endif
#endif

  // Wide connection interval range lets macOS pick a comfortable value.
  // Apple recommends min >= 15 ms, max <= 150 ms for stable peripherals.
  // Values are BLE units of 1.25 ms: 0x0C=15 ms, 0x0060=120 ms.
  midi_ble.ble_settings.connection_interval.minimum = 0x000C;
  midi_ble.ble_settings.connection_interval.maximum = 0x0060;
  midi_ble.ble_settings.initiate_security = false;
  midi_ble.setName(bleName);
  // Match the direct MIDI-interface lifecycle used by prior stable firmware.
  MIDI_Interface::beginAll();
  midi_ble.setCallbacks(callbacks);

  Serial.print("BLE MIDI ready: ");
  Serial.println(bleName);
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
      // Defer Active Sensing until GATT discovery settles (see grace period below).
      connectedAtMs = nowMs;
      lastActiveSenseMs = nowMs;
    } else {
      detachAll();
    }
  }

  // Keep BLE MIDI link active on hosts that drop idle peripherals.
  // Wait for grace period after connect so GATT discovery can finish.
  if (connected && static_cast<uint32_t>(nowMs - connectedAtMs) >= kConnectGraceMs) {
    if (static_cast<uint32_t>(nowMs - lastActiveSenseMs) >= kActiveSenseIntervalMs) {
      lastActiveSenseMs = nowMs;
      midi_ble.send(static_cast<cs::RealTimeMessage>(cs::RealTimeMessage::ActiveSensing));
    }
  }

  // Periodic status line for runtime diagnostics.
  if (static_cast<uint32_t>(nowMs - lastStateLogMs) >= 5000) {
    lastStateLogMs = nowMs;
    Serial.print("BLE state: ");
    Serial.println(connected ? "connected" : "advertising");
  }

  serviceReturns(micros());
}

}  // namespace drumbot
