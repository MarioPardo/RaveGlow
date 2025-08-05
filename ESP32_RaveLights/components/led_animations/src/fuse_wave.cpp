// fuse_wave.cpp
#include "animations/fuse_wave.hpp"
#include "esp_timer.h"
#include "esp_log.h"

FuseWave::FuseWave(led_strip_handle_t strip, uint8_t r, uint8_t g, uint8_t b, uint32_t BPM)
            : LedAnimation(strip), red(r), green(g), blue(b){

               
    this->beatTime = 60000 / BPM; // Convert BPM to milliseconds per beat
    ESP_LOGI("FuseWave", "BPM: %u, Beat Time: %f ms", BPM, this->beatTime);
    this->hasMultipleFrames = true;
    }

void FuseWave::start() 
{
    LedAnimation::start();
    start_time = esp_timer_get_time() / 1000; // Get current time in milliseconds

    ESP_LOGI("FuseWave", "Starting FuseWave animation at time %u", start_time);

    act_frame(); 

}

bool FuseWave::act_frame() {

    if(!active) {
        return false; // Animation is not active
    }

    ESP_LOGI("FuseWave", "Acting frame !");


    this->active = false;

    return false;
}

void FuseWave::stop() {
    LedAnimation::stop();
}
