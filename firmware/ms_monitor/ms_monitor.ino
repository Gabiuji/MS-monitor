#include <Arduino.h>
#include <DHT.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <max6675.h>
#include "config.h"
#include "embedded_inference.h"

constexpr uint8_t DHT_PIN = 17;
constexpr uint8_t VIBRATION_PIN = 22;
constexpr uint8_t PROBE_SCK_PIN = 13;
constexpr uint8_t PROBE_CS_PIN = 23;
constexpr uint8_t PROBE_SO_PIN = 39;
constexpr uint32_t READING_INTERVAL_MS = 2500;
constexpr uint32_t WIFI_RETRY_INTERVAL_MS = 10000;
DHT dht(DHT_PIN, DHT22);
MAX6675 probe(PROBE_SCK_PIN, PROBE_CS_PIN, PROBE_SO_PIN);
volatile uint32_t transitions = 0;
portMUX_TYPE counterLock = portMUX_INITIALIZER_UNLOCKED;
uint32_t windowStart = 0;
uint32_t lastWifiAttempt = 0;
bool wasConnected = false;

void ARDUINO_ISR_ATTR recordTransition() {
  portENTER_CRITICAL_ISR(&counterLock);
  transitions++;
  portEXIT_CRITICAL_ISR(&counterLock);
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  pinMode(VIBRATION_PIN, INPUT);
  pinMode(PROBE_SO_PIN, INPUT);
  pinMode(PROBE_CS_PIN, OUTPUT);
  pinMode(PROBE_SCK_PIN, OUTPUT);
  digitalWrite(PROBE_SCK_PIN, LOW);
  digitalWrite(PROBE_CS_PIN, HIGH);
  // The first 2500 ms window also covers the initial conversion (up to 220 ms).
  portENTER_CRITICAL(&counterLock);
  windowStart = millis();
  portEXIT_CRITICAL(&counterLock);
  attachInterrupt(digitalPinToInterrupt(VIBRATION_PIN), recordTransition, CHANGE);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  lastWifiAttempt = millis();
  Serial.println("MS-Monitor: DHT22 GPIO 17; vibration GPIO 22; waiting for Wi-Fi");
  Serial.printf("Embedded AI: %s | Model: %u bytes | Source: ESP32\n",
                ms_monitor_ai::kModelVersion, ms_monitor_ai::kModelBytes);
}

void loop() {
  uint32_t now = millis();
  bool connected = WiFi.status() == WL_CONNECTED;
  if (connected && !wasConnected) {
    Serial.print("Wi-Fi connected; IP: ");
    Serial.println(WiFi.localIP());
  } else if (!connected && wasConnected) {
    Serial.println("Wi-Fi disconnected; local readings continue");
  }
  wasConnected = connected;
  if (!connected && now - lastWifiAttempt >= WIFI_RETRY_INTERVAL_MS) {
    lastWifiAttempt = now;
    WiFi.reconnect();
    Serial.println("Attempting Wi-Fi reconnection");
  }
  if (now - windowStart < READING_INTERVAL_MS) { delay(1); return; }

  // The timestamp and counter belong to the same atomic window snapshot.
  portENTER_CRITICAL(&counterLock);
  uint32_t windowEnd = millis();
  uint32_t windowMs = windowEnd - windowStart;
  uint32_t transitionCount = transitions;
  transitions = 0;
  windowStart = windowEnd;
  portEXIT_CRITICAL(&counterLock);
  int signalLevel = digitalRead(VIBRATION_PIN);
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  bool dhtOk = isfinite(temperature) && isfinite(humidity)
    && temperature >= -40 && temperature <= 80 && humidity >= 0 && humidity <= 100;
  float probeTemperature = probe.readCelsius();
  bool probeOk = isfinite(probeTemperature) && probeTemperature >= 0 && probeTemperature <= 1024;
  // Run locally before the Wi-Fi check; inference remains available offline.
  ms_monitor_ai::Prediction prediction = {};
  uint32_t inferenceUs = 0;
  if (dhtOk && probeOk) {
    uint32_t started = micros();
    prediction = ms_monitor_ai::predictRisk(temperature, humidity, probeTemperature);
    inferenceUs = micros() - started;
  }
  if (dhtOk) Serial.printf("Temperature: %.1f C | Humidity: %.1f %%", temperature, humidity);
  else Serial.print("DHT22: read failure");
  if (probeOk) Serial.printf(" | Probe: %.2f C", probeTemperature);
  else Serial.print(" | MAX6675: read failure");
  Serial.printf(" | DO: %d | Transitions: %lu | Window: %lu ms", signalLevel,
                (unsigned long)transitionCount, (unsigned long)windowMs);
  if (prediction.valid) Serial.printf(" | AI (ESP32): %s | Confidence: %.3f | Inference: %lu us\n",
      ms_monitor_ai::kClassNames[prediction.classIndex], prediction.confidence, (unsigned long)inferenceUs);
  else Serial.println(" | AI (ESP32): unavailable; invalid sensor inputs");

  // No queue: one attempt per reading; skip sending when unavailable.
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Cannot send: Wi-Fi unavailable");
    return;
  }
  JsonDocument document;
  document["device_id"] = DEVICE_ID;
  document["uptime_ms"] = windowEnd;
  document["window_ms"] = windowMs;
  document["dht_ok"] = dhtOk;
  if (dhtOk) {
    document["temperature_c"] = temperature;
    document["humidity_pct"] = humidity;
  } else {
    document["temperature_c"] = nullptr;
    document["humidity_pct"] = nullptr;
  }
  document["vibration_do"] = signalLevel;
  document["vibration_transitions"] = transitionCount;
  document["probe_ok"] = probeOk;
  if (probeOk) document["probe_temperature_c"] = probeTemperature;
  else document["probe_temperature_c"] = nullptr;
  JsonObject diagnosis = document["embedded_diagnosis"].to<JsonObject>();
  diagnosis["source"] = "esp32";
  diagnosis["model_version"] = ms_monitor_ai::kModelVersion;
  diagnosis["inference_us"] = inferenceUs;
  diagnosis["risk_level"] = prediction.valid ? ms_monitor_ai::kClassNames[prediction.classIndex] : "unavailable";
  if (prediction.valid) {
    diagnosis["risk_score"] = prediction.riskScore;
    diagnosis["confidence"] = prediction.confidence;
  } else {
    diagnosis["risk_score"] = nullptr;
    diagnosis["confidence"] = nullptr;
  }
  String payload;
  serializeJson(document, payload);
  WiFiClient client;
  HTTPClient http;
  http.setConnectTimeout(700);
  http.setTimeout(1000);
  if (http.begin(client, API_URL)) {
    http.addHeader("Content-Type", "application/json");
    int statusCode = http.POST(payload);
    if (statusCode == 201) Serial.println("Reading accepted: HTTP 201");
    else Serial.printf("Send failed; HTTP/network code: %d\n", statusCode);
  } else {
    Serial.println("Failed to initialize HTTP");
  }
  http.end();
}
