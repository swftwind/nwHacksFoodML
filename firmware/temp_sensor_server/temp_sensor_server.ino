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
    Serial.println("New Client Request");
    String requestLine = "";
    boolean currentLineIsBlank = true;

    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        
        // Capture only the first line of the request to find the URL path
        if (requestLine.length() < 50 && c != '\n' && c != '\r') {
          requestLine += c;
        }

        if (c == '\n' && currentLineIsBlank) {
          // --- 1. PERFORM SENSOR READ ---
          int val = analogRead(A0);
          if (val <= 0) val = 1; 
          float resistance = (float)(1023 - val) * 10000 / val;
          float temperature = 1 / (log(resistance / 10000) / B + 1 / 298.15) - 273.15;

          // --- 2. ROUTING LOGIC ---
          // Check if the URL contains "/temp"
          if (requestLine.indexOf("/temp") != -1) {
            // API ENDPOINT: Returns just the number for React
            client.println("HTTP/1.1 200 OK");
            client.println("Content-Type: text/plain");
            client.println("Access-Control-Allow-Origin: *"); // ALLOW REACT ACCESS
            client.println("Connection: close");
            client.println();
            client.print(temperature); 
            Serial.println("Served API endpoint (/temp)");
          } 
          else {
            // WEB PAGE: Returns the HTML UI
            client.println("HTTP/1.1 200 OK");
            client.println("Content-Type: text/html");
            client.println("Connection: close");
            client.println();
            client.println("<!DOCTYPE HTML><html>");
            client.println("<head><title>Arduino Temp</title></head><body>");
            client.println("<h1>Current Temperature</h1>");
            client.print("<p style='font-size:40px; font-weight:bold;'>");
            client.print(temperature);
            client.println(" &deg;C</p>");
            client.print("<p>Raw Value: ");
            client.print(val);
            client.println("</p>");
            client.println("<p><a href='/temp'>View API Endpoint</a></p>");
            client.println("</body></html>");
            Serial.println("Served HTML page (/)");
          }
          break;
        }
        if (c == '\n') { currentLineIsBlank = true; }
        else if (c != '\r') { currentLineIsBlank = false; }
      }
    }
    delay(10); 
    client.stop();
  }
}