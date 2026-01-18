#include "WiFiS3.h"
#include <math.h>

char ssid[] = "nwHacks2026";    
char pass[] = "nw_Hacks_2026";
int status = WL_IDLE_STATUS;
WiFiServer server(80);

const int B = 3975; 

void setup() {
  Serial.begin(9600);
  while (!Serial); 

  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(ssid);
    status = WiFi.begin(ssid, pass);
    delay(5000); 
  }

  // Safety: Ensure IP is fully assigned before starting server
  while (WiFi.localIP() == IPAddress(0,0,0,0)) {
    delay(500);
  }
  
  server.begin();
  Serial.println("Connected! View temp at IP:");
  Serial.println(WiFi.localIP());
}

void loop() {
  WiFiClient client = server.available();
  if (client) {
    // Read the incoming request from the browser
    boolean currentLineIsBlank = true;
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        // If we've received a blank line, the HTTP request has ended
        if (c == '\n' && currentLineIsBlank) {
          
          // 1. PERFORM SENSOR READ
          int val = analogRead(A0);
          if (val <= 0) val = 1; // Prevent division by zero crash
          float resistance = (float)(1023 - val) * 10000 / val;
          float temperature = 1 / (log(resistance / 10000) / B + 1 / 298.15) - 273.15;

          // 2. SEND STANDARD HTTP HEADER
          client.println("HTTP/1.1 200 OK");
          client.println("Content-Type: text/html");
          client.println("Connection: close");
          client.println();
          
          // 3. SEND HTML BODY
          client.println("<!DOCTYPE HTML><html>");
          client.println("<head><title>Arduino Temp</title></head><body>");
          client.println("<h1>Current Temperature</h1>");
          client.print("<p style='font-size:40px; font-weight:bold;'>");
          client.print(temperature);
          client.println(" &deg;C</p>");
          client.print("<p>Raw Value: ");
          client.print(val);
          client.println("</p></body></html>");
          break;
        }
        if (c == '\n') { currentLineIsBlank = true; }
        else if (c != '\r') { currentLineIsBlank = false; }
      }
    }
    delay(10); // Give the browser time to receive the data
    client.stop();
  }
}