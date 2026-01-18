#include "WiFiS3.h"
#include <math.h>

char ssid[] = "nwHacks2026";    
char pass[] = "nw_Hacks_2026";
int status = WL_IDLE_STATUS;

WiFiServer server(80);

// Thermistor parameters for Grove Temp Sensor v1.2
const int B = 3975; 

void setup() {
  Serial.begin(9600);
  
  // Attempt to connect to WiFi
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(ssid);
    status = WiFi.begin(ssid, pass);
    delay(5000); 
  }
  
  server.begin();
  Serial.println("Connected! View temp at IP:");
  Serial.println(WiFi.localIP());
}

void loop() {
  WiFiClient client = server.available();
  if (client) {
    // Read Analog value from A0
    int val = analogRead(A0);
    
    // Convert to Celsius using the v1.2 formula
    float resistance = (float)(1023 - val) * 10000 / val;
    float temperature = 1 / (log(resistance / 10000) / B + 1 / 298.15) - 273.15;

    // Standard HTTP Response
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: text/html");
    client.println("Connection: close");
    client.println();
    client.print("<h1>Current Temperature</h1>");
    client.print("<p style='font-size:24px;'>Celsius: ");
    client.print(temperature);
    client.print("</p>");
    
    delay(1);
    client.stop();
  }
}