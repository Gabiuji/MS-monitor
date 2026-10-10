#include <Arduino.h>
#include <DHT.h>
constexpr uint8_t DHT_PIN = 17;
constexpr uint8_t VIBRATION_PIN = 22;
DHT dht(DHT_PIN, DHT22);
volatile uint32_t transitions = 0;
portMUX_TYPE counterLock = portMUX_INITIALIZER_UNLOCKED;
unsigned long lastReading = 0;
void ARDUINO_ISR_ATTR recordTransition() {
  portENTER_CRITICAL_ISR(&counterLock);
  transitions++;
  portEXIT_CRITICAL_ISR(&counterLock);
}
void setup() {
  Serial.begin(115200);
  dht.begin();
  pinMode(VIBRATION_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(VIBRATION_PIN), recordTransition, CHANGE);
  Serial.println("Test: DHT22 GPIO 17; vibration GPIO 22");
}
void loop() {
  unsigned long now = millis();
  if (now - lastReading < 2500) { delay(1); return; }
  lastReading = now;
  portENTER_CRITICAL(&counterLock);
  uint32_t transitionCount = transitions;
  transitions = 0;
  portEXIT_CRITICAL(&counterLock);
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  if (isnan(temperature) || isnan(humidity)) {
    Serial.print("DHT22: read failure");
  } else {
    Serial.printf("Temperature: %.1f C | Humidity: %.1f %%", temperature, humidity);
  }
  Serial.printf(" | DO: %d | Transitions in window: %lu\n",
                digitalRead(VIBRATION_PIN), (unsigned long)transitionCount);
}
