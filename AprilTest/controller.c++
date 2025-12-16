#include <rpcWiFi.h>
#include <WiFiUdp.h>
#include <TFT_eSPI.h>

// --- CONFIGURATION ---
const char* ssid = "Sam iPhone"; 
const char* password = "12345678";

// TARGET IPS
IPAddress carIP(172, 20, 10, 3);      
IPAddress dispIP(172, 20, 10, 4);     
unsigned int localPort = 5000;

WiFiUDP udp;
TFT_eSPI tft;

// State Tracking
String currentState = "";
bool isDispensing = false;
unsigned long lastDispenseTime = 0;

// Arm & Speed Tracking
bool armIsUp = false; 
bool isFastMode = true; // Start in Fast Mode

// Button Latches (to prevent double-clicks)
bool buttonBPressed = false; 
bool stickPressed = false;

void setup() {
  // 1. Controls
  pinMode(WIO_5S_UP, INPUT_PULLUP);
  pinMode(WIO_5S_DOWN, INPUT_PULLUP);
  pinMode(WIO_5S_LEFT, INPUT_PULLUP);
  pinMode(WIO_5S_RIGHT, INPUT_PULLUP);
  pinMode(WIO_5S_PRESS, INPUT_PULLUP); // Joystick Click
  
  pinMode(WIO_KEY_C, INPUT_PULLUP); // Left Button
  pinMode(WIO_KEY_B, INPUT_PULLUP); // Middle Button

  // 2. Screen Setup
  tft.begin();
  tft.setRotation(3);
  tft.fillScreen(TFT_BLACK);
  
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  tft.drawCentreString("CONNECTING...", 160, 100, 1);

  // 3. Connect Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(200);
  }

  // 4. Start Dashboard
  udp.begin(localPort);
  drawBackground();
  updateDashboard("STOP");
  updateArmStatus(); 
  updateSpeedStatus(); // Show initial speed
}

void loop() {
  // --- CAR CONTROL ---
  String nextState = "STOP";
  
  if (digitalRead(WIO_5S_UP) == LOW) {
    sendUDP(carIP, "fwd");
    nextState = "FWD";
  }
  else if (digitalRead(WIO_5S_DOWN) == LOW) {
    sendUDP(carIP, "bwd");
    nextState = "BWD";
  }
  else if (digitalRead(WIO_5S_LEFT) == LOW) {
    sendUDP(carIP, "rgt"); // Swapped for steering fix
    nextState = "LEFT"; 
  }
  else if (digitalRead(WIO_5S_RIGHT) == LOW) {
    sendUDP(carIP, "lft"); // Swapped for steering fix
    nextState = "RIGHT"; 
  }
  else {
    sendUDP(carIP, "stop");
    nextState = "STOP";
  }

  if (!isDispensing) updateDashboard(nextState);

  // --- DISPENSER CONTROL (Button C) ---
  if (digitalRead(WIO_KEY_C) == LOW) {
    sendUDP(dispIP, "dispense");
    if (!isDispensing) {
        drawDispenseScreen(true);
        isDispensing = true;
    }
    lastDispenseTime = millis();
  }
  
  if (isDispensing && (millis() - lastDispenseTime > 500)) {
    drawDispenseScreen(false);
    isDispensing = false;
    currentState = ""; 
    // Redraw statuses that got wiped
    updateArmStatus();
    updateSpeedStatus();
  }

  // --- ARM CONTROL (Button B) ---
  if (digitalRead(WIO_KEY_B) == LOW) {
    if (!buttonBPressed) {
        sendUDP(carIP, "arm");
        armIsUp = !armIsUp;
        updateArmStatus(); 
        buttonBPressed = true; 
    }
  } else {
    buttonBPressed = false; 
  }

  // --- SPEED TOGGLE (Joystick Press) ---
  if (digitalRead(WIO_5S_PRESS) == LOW) {
    if (!stickPressed) {
        // Toggle Mode
        isFastMode = !isFastMode;
        
        // Send Command
        if (isFastMode) sendUDP(carIP, "fast");
        else sendUDP(carIP, "slow");
        
        // Update Screen
        updateSpeedStatus();
        stickPressed = true;
    }
  } else {
    stickPressed = false;
  }

  delay(50);
}

// --- NETWORK HELPER ---
void sendUDP(IPAddress& targetIP, const char* msg) {
  udp.beginPacket(targetIP, localPort);
  udp.write((const uint8_t*)msg, strlen(msg));
  udp.endPacket();
}

// --- GRAPHICS ---

void drawBackground() {
  tft.fillScreen(TFT_BLACK);
  
  // Header
  tft.fillRect(0, 0, 320, 30, TFT_DARKGREY);
  tft.setTextColor(TFT_WHITE, TFT_DARKGREY);
  tft.setTextSize(2);
  tft.drawString("RC CONTROL", 10, 8);
  tft.fillCircle(300, 15, 6, TFT_GREEN);
  
  // Crosshairs
  tft.drawLine(160, 60, 160, 220, TFT_DARKGREY); 
  tft.drawLine(60, 140, 260, 140, TFT_DARKGREY); 
}

void updateArmStatus() {
    // Bottom RIGHT Corner
    tft.fillRect(200, 35, 120, 25, TFT_BLACK); 
    tft.setTextSize(2);
    if (armIsUp) {
        tft.setTextColor(TFT_CYAN, TFT_BLACK);
        tft.drawString("ARM: DWN", 215, 40);
    } else {
        tft.setTextColor(TFT_MAGENTA, TFT_BLACK);
        tft.drawString("ARM: UP", 215, 40);
    }
}

void updateSpeedStatus() {
    // Bottom LEFT Corner (Opposite of Arm)
    tft.fillRect(0, 200, 120, 40, TFT_BLACK); 
    tft.setTextSize(2);
    
    if (isFastMode) {
        tft.setTextColor(TFT_GREEN, TFT_BLACK);
        tft.drawString("FAST", 10, 210);
    } else {
        tft.setTextColor(TFT_ORANGE, TFT_BLACK);
        tft.drawString("SLOW", 10, 210);
    }
}

void updateDashboard(String state) {
  if (state == currentState) return; 
  
  tft.fillRect(60, 40, 200, 190, TFT_BLACK); 
  
  tft.drawLine(160, 60, 160, 220, TFT_DARKGREY);
  tft.drawLine(60, 140, 260, 140, TFT_DARKGREY);

  if (state == "STOP") {
      tft.fillCircle(160, 140, 40, TFT_RED);
  }
  else if (state == "FWD") {
      tft.fillTriangle(160, 60, 100, 160, 220, 160, TFT_GREEN);
  }
  else if (state == "BWD") {
      tft.fillTriangle(160, 210, 100, 120, 220, 120, TFT_BLUE);
  }
  else if (state == "LEFT") {
      tft.fillTriangle(60, 140, 140, 80, 140, 200, TFT_YELLOW);
  }
  else if (state == "RIGHT") {
      tft.fillTriangle(260, 140, 180, 80, 180, 200, TFT_YELLOW);
  }
  currentState = state;
}

void drawDispenseScreen(bool active) {
    if (active) {
        tft.fillRect(50, 40, 220, 190, TFT_BLACK);
        tft.fillCircle(160, 140, 70, TFT_BLUE);
        tft.setTextColor(TFT_WHITE, TFT_BLUE);
        tft.setTextSize(3);
        tft.drawCentreString("DISPENSE", 160, 130, 1);
    } 
}