// led_animation.hpp
#pragma once

#include <cstdint>
#include <vector>
#include "led_strip.h" 

class LedAnimation {
public:
    LedAnimation(led_strip_handle_t strip) : ledstrip(strip), active(false) {}
    virtual ~LedAnimation() = default;

    virtual void start() 
    {
        active = true;
    }

    virtual bool act_frame() = 0;

    virtual void stop() {
       active = false;
    }

    bool isActive() const { return active; }

protected:
    led_strip_handle_t ledstrip = nullptr;
    bool active = false;
    uint32_t startTime = 0;  // Start time in milliseconds
    float beatTime = 0.0f;  // Time per beat in milliseconds
    bool hasMultipleFrames;
    uint32_t frameNumber = 0;  // Frame number for animations that have multiple frames

};
