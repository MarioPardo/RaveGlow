// fuse_wave.cpp
#include "animations/fuse_wave.hpp"
#include <cmath>

extern "C" {
#include "esp_timer.h"
#include "esp_log.h"

#include "led_strip.h" 
}


FuseWave::FuseWave(pixel_t* ledstrip_buffer, uint32_t length, uint8_t r, uint8_t g, uint8_t b, uint32_t BPM, float beatPercentage)
            : LedAnimation(ledstrip_buffer, length){
    this->red = r;
    this->green = g;
    this->blue = b;

    this->hasMultipleFrames = true;   
    this->beatPercentage = beatPercentage  ; 

    this->beatTime = 60000 / BPM; // Convert BPM to milliseconds per beat
    this->numFrames =  ledcount / chunkSize; // Calculate number of frames based on chunk size
    
    this->frameTime = this->beatTime * this->beatPercentage / this->numFrames;
    this->frameTime = std::round(this->frameTime * 100.0) / 100.0; // Round to 2 decimal places


    ESP_LOGI("FuseWave", "BPM: %u, Beat Time: %f ms, Frame Time: %f ms", BPM, this->beatTime, this->frameTime);
   
    }

void FuseWave::start() 
{
    LedAnimation::start();
    this->frameNumber = 0;
    
    ESP_LOGI("FuseWave", "Starting FuseWave animation");

}

bool FuseWave::act_frame() {
    

    // Ensure we should be acting on this frame
    if(!active) 
        return false;

    if (frameNumber > numFrames) {
        stop();
        return false;
    }

    // Only update if it is time to do so 
    float timeSinceLastFrame = (esp_timer_get_time() / 1000) - lastFrameTime;
    if(frameNumber == 0 || timeSinceLastFrame >= frameTime)
    {
        frameNumber++;
        lastFrameTime = esp_timer_get_time() / 1000; // Update last frame time
    }

    // Set the current chunk of LEDSs
    int startIndex = (frameNumber-1) * chunkSize;
    int endIndex = startIndex + chunkSize;
    if (endIndex > ledcount) {
        endIndex = ledcount;
    }

    for (int i = startIndex; i < endIndex; i++) {
        set_pixel(i, red, green, blue);
    }

    return true;
}

void FuseWave::stop() {
    LedAnimation::stop();
    ESP_LOGI("FuseWave", "Stopping animation ");
}
