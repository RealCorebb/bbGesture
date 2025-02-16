#include <DFRobot_MGC3130.h>
#include <AnimatedGIF.h>
#include <Adafruit_NeoPixel.h>
#include <FS.h>
#include <LittleFS.h>

// Pin definitions
uint8_t DPin = 2;
uint8_t MCLRPin = 4;
#define PIN 6
#define MATRIX_WIDTH 8
#define MATRIX_HEIGHT 8
#define NUMPIXELS (MATRIX_WIDTH * MATRIX_HEIGHT)
#define BRIGHT_SHIFT 3
#define MAX_GIF_SIZE 32768

// Global objects
DFRobot_MGC3130 myGesture(DPin, MCLRPin);
Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);
AnimatedGIF gif;

// Shared variables
uint8_t *gifBuffer = nullptr;
size_t gifSize = 0;
String currentGifFile = "/question.gif";
volatile bool needToLoadNewGif = true;

// Mutex for protecting shared resources
SemaphoreHandle_t gifMutex = NULL;

uint16_t XY(uint8_t x, uint8_t y) {
  return (y * MATRIX_WIDTH) + x;
}

// GIF drawing callback function
void GIFDraw(GIFDRAW *pDraw) {
  uint8_t r, g, b, *s, *p, *pPal = (uint8_t *)pDraw->pPalette;
  int x, y = pDraw->iY + pDraw->y;

  if (y >= MATRIX_HEIGHT) return;

  s = pDraw->pPixels;
  if (pDraw->ucDisposalMethod == 2) {
    p = &pPal[pDraw->ucBackground * 3];
    r = p[0] >> BRIGHT_SHIFT;
    g = p[1] >> BRIGHT_SHIFT;
    b = p[2] >> BRIGHT_SHIFT;

    for (x = 0; x < pDraw->iWidth && x < MATRIX_WIDTH; x++) {
      if (s[x] == pDraw->ucTransparent) {
        pixels.setPixelColor(XY(x, y), pixels.Color(r, g, b));
      }
    }
    pDraw->ucHasTransparency = 0;
  }

  if (pDraw->ucHasTransparency) {
    const uint8_t ucTransparent = pDraw->ucTransparent;
    for (x = 0; x < pDraw->iWidth && x < MATRIX_WIDTH; x++) {
      if (s[x] != ucTransparent) {
        p = &pPal[s[x] * 3];
        pixels.setPixelColor(XY(x, y), pixels.Color(p[0] >> BRIGHT_SHIFT, p[1] >> BRIGHT_SHIFT, p[2] >> BRIGHT_SHIFT));
      }
    }
  } else {
    for (x = 0; x < pDraw->iWidth && x < MATRIX_WIDTH; x++) {
      p = &pPal[s[x] * 3];
      pixels.setPixelColor(XY(x, y), pixels.Color(p[0] >> BRIGHT_SHIFT, p[1] >> BRIGHT_SHIFT, p[2] >> BRIGHT_SHIFT));
    }
  }

  if (pDraw->y == pDraw->iHeight - 1) {
    pixels.show();
  }
}

bool loadGifFile() {
  File file = LittleFS.open(currentGifFile, "r");
  if (!file) {
    Serial.printf("Failed to open %s\n", currentGifFile);
    return false;
  }

  gifSize = file.read(gifBuffer, MAX_GIF_SIZE);
  file.close();

  if (gifSize == 0) {
    Serial.println("Failed to read file");
    return false;
  }

  return true;
}

// Task for handling gesture detection
void gestureTask(void *parameter) {
  while (1) {
    myGesture.sensorDataRecv();
    
    switch(myGesture.getGestureInfo()) {
      case myGesture.eFilckR:
        Serial.println("Flick Left to Right");
        xSemaphoreTake(gifMutex, portMAX_DELAY);
        needToLoadNewGif = true;
        currentGifFile = "/Right.gif";
        xSemaphoreGive(gifMutex);
        break;
      case myGesture.eFilckL:
        Serial.println("Flick Right to Left");
        xSemaphoreTake(gifMutex, portMAX_DELAY);
        needToLoadNewGif = true;
        currentGifFile = "/Left.gif";
        xSemaphoreGive(gifMutex);
        break;
      case myGesture.eFilckU:
        Serial.println("Flick Down to Up");
        xSemaphoreTake(gifMutex, portMAX_DELAY);
        needToLoadNewGif = true;
        currentGifFile = "/Top.gif";
        xSemaphoreGive(gifMutex);
        break;
      case myGesture.eFilckD:
        Serial.println("Flick Up to Down");
        xSemaphoreTake(gifMutex, portMAX_DELAY);
        needToLoadNewGif = true;
        currentGifFile = "/Bot.gif";
        xSemaphoreGive(gifMutex);
        break;
      case myGesture.eCircleClockwise:
        Serial.println("Circle clockwise");
        break;
      case myGesture.eCircleCounterclockwise:
        Serial.println("Circle counterclockwise");
        break;
      default:
        break;
    }
    
    vTaskDelay(pdMS_TO_TICKS(50)); // Small delay to prevent task starvation
  }
}

// Task for handling GIF animation
void gifTask(void *parameter) {
  while (1) {
    xSemaphoreTake(gifMutex, portMAX_DELAY);
    bool shouldLoadNewGif = needToLoadNewGif;
    xSemaphoreGive(gifMutex);

    if (shouldLoadNewGif) {
      if (loadGifFile()) {
        xSemaphoreTake(gifMutex, portMAX_DELAY);
        needToLoadNewGif = false;
        xSemaphoreGive(gifMutex);
        gif.close();
      } else {
        vTaskDelay(pdMS_TO_TICKS(1000));
        continue;
      }
    }

    int rc = gif.open(gifBuffer, gifSize, GIFDraw);
    if (rc) {
      while (rc) {
        xSemaphoreTake(gifMutex, portMAX_DELAY);
        bool shouldBreak = needToLoadNewGif;
        xSemaphoreGive(gifMutex);
        
        if (shouldBreak) break;
        
        rc = gif.playFrame(true, NULL);
        if (!rc) {
          gif.close();
          rc = gif.open(gifBuffer, gifSize, GIFDraw);
        }
        
        // Small delay to allow other tasks to run
        vTaskDelay(pdMS_TO_TICKS(1));
      }
      gif.close();
    } else {
      Serial.println("Failed to open GIF");
      vTaskDelay(pdMS_TO_TICKS(1000));
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  // Initialize gesture sensor
  while (!myGesture.begin()) {
    Serial.println("begin error! Please check whether the connection is correct");
    delay(100);
  }
  Serial.println("begin success!!!");

  // Initialize NeoPixel matrix
  pixels.begin();
  pixels.clear();
  pixels.show();

  // Initialize filesystem
  if (!LittleFS.begin(true)) {
    Serial.println("LittleFS Mount Failed");
    return;
  }

  // Allocate GIF buffer
  gifBuffer = (uint8_t *)malloc(MAX_GIF_SIZE);
  if (!gifBuffer) {
    Serial.println("Failed to allocate GIF buffer");
    return;
  }

  // Initialize GIF decoder
  gif.begin(GIF_PALETTE_RGB888);

  // Create mutex
  gifMutex = xSemaphoreCreateMutex();
  if (gifMutex == NULL) {
    Serial.println("Failed to create mutex");
    return;
  }

  // Create tasks
  xTaskCreatePinnedToCore(
    gestureTask,           // Task function
    "GestureTask",        // Task name
    4096,                 // Stack size
    NULL,                 // Task parameters
    1,                    // Priority
    NULL,                 // Task handle
    0                     // Core ID (0)
  );

  xTaskCreatePinnedToCore(
    gifTask,              // Task function
    "GifTask",           // Task name
    4096,                // Stack size
    NULL,                // Task parameters
    1,                   // Priority
    NULL,                // Task handle
    1                    // Core ID (1)
  );
}

void loop() {
  // Empty loop - tasks handle everything
  vTaskDelete(NULL);  // Delete the loop task since we don't need it
}