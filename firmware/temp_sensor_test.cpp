#include <math.h>

const int B = 3975; // Thermistor constant for v1.2
const int pinTempSensor = A0; 

void setup() {
  Serial.begin(9600);
  while (!Serial); // Wait for Serial Monitor to open
  Serial.println("--- Grove Temp Sensor v1.2 Test ---");
}

void loop() {
  // 1. Get the raw analog signal
  int val = analogRead(pinTempSensor);
  
  // 2. Calculate Resistance
  // If val is 0, the sensor is likely disconnected or shorted
  if (val <= 0) {
    Serial.println("Error: Raw value is 0. Check your Grove cable!");
  } else {
    float resistance = (float)(1023 - val) * 10000 / val;
    float temperature = 1 / (log(resistance / 10000) / B + 1 / 298.15) - 273.15;

    // 3. Print results
    Serial.print("Raw Value: ");
    Serial.print(val);
    Serial.print(" | Celsius: ");
    Serial.println(temperature);
  }

  delay(1000); // Wait 1 second between reads
}