// led_animation.hpp
#pragma once

#include <cstdint>
#include <vector>

extern "C" {
#include "led_strip.h" 
}

class LedAnimation {
public:
    LedAnimation(led_strip_handle_t strip, uint32_t length) : ledstrip(strip), ledcount(length) {}
    virtual ~LedAnimation() = default;

    virtual void start() 
    {
        active = true;
        started = true;
        
    }

    virtual bool act_frame() = 0;

    virtual void stop() {
       active = false;
    }

    bool isActive() const { return active; }

    bool active = false;
    bool started = false;
    bool hasMultipleFrames;
    float frameTime;

protected:
    led_strip_handle_t ledstrip;
    uint32_t ledcount;
    float startTime = 0;  // Start time in milliseconds
    float beatTime; // Time per beat in milliseconds
    uint32_t numFrames;
    uint32_t frameNumber = 0; // Frame number for animations that have multiple frames
    float lastFrameTime = 0;

    uint8_t red, green, blue;
};
