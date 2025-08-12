// fuse_wave.cpp
#include "animations/fuse_wave.hpp"

extern "C" {
#include "esp_timer.h"
#include "esp_log.h"

#include "led_strip.h" 
}


FuseWave::FuseWave(led_strip_handle_t strip, uint32_t length, uint8_t r, uint8_t g, uint8_t b, uint32_t BPM)
            : LedAnimation(strip, length){
    this->red = r;
    this->green = g;
    this->blue = b;

    this->hasMultipleFrames = true;      
    this->beatTime = 60000 / BPM; // Convert BPM to milliseconds per beat
    this->numFrames =  ledcount / chunkSize; // Calculate number of frames based on chunk size
    this->frameTime = this->beatTime / this->numFrames; // Calculate time per frame
    
    ESP_LOGI("FuseWave", "BPM: %u, Beat Time: %f ms", BPM, this->beatTime);
    ESP_LOGI("FuseWave", "Number of frames: %u, Frame time: %f ms", this->numFrames, this->frameTime);
   
    }

void FuseWave::start() 
{
    LedAnimation::start();
    this->frameNumber = 0;
    this->startTime = esp_timer_get_time() / 1000; // Get current time in milliseconds
    
    ESP_LOGI("FuseWave", "Starting FuseWave animation");

}

bool FuseWave::act_frame() {
    if(!active) 
        return false; // Animation is not active

    // TODO if has taken too long, using start time, end it

    float timeSinceLastFrame = (esp_timer_get_time() / 1000) - lastFrameTime;
    if(frameNumber == 0 || timeSinceLastFrame >= frameTime)
    {
        // Calculate the start index for the current frame
        int startIndex = frameNumber * chunkSize;
        int endIndex = startIndex + chunkSize;

        // Ensure we don't exceed length of the LED strip
        if (endIndex > ledcount) {
            endIndex = ledcount;
        }

        // Set the current chunk of LEDSs
        for (int i = startIndex; i < endIndex; i++) {
            led_strip_set_pixel(ledstrip, i, red, green, blue);
        }


        // Move to the next frame
        frameNumber++;
        lastFrameTime = esp_timer_get_time() / 1000; // Update last frame time

        // If we've reached the end of the frames, reset to the first frame
        if (frameNumber >= numFrames) {
            stop();
            return false; // Animation completed a full cycle
        }
    }

    return true;

}

void FuseWave::stop() {
    LedAnimation::stop();
    ESP_LOGI("FuseWave", "Stopping FuseWave animation ");
}
