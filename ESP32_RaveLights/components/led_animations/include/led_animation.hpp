// led_animation.hpp
#pragma once

#include <cstdint>
#include <vector>

extern "C" {
#include "led_strip.h" 
}

typedef struct {
    uint8_t r;
    uint8_t g;
    uint8_t b;
} pixel_t;

class LedAnimation {
public:
    LedAnimation(pixel_t* ledstrip_buffer, uint32_t length) : LED_STRIP_BUFFER(ledstrip_buffer), ledcount(length)
    {}

    virtual ~LedAnimation() = default;

    virtual void start() 
    {
        active = true;
        started = true;
        
    }

    inline void set_pixel(uint32_t index, uint8_t r, uint8_t g, uint8_t b) {
        if (index < ledcount) {
            LED_STRIP_BUFFER[index].r = r;
            LED_STRIP_BUFFER[index].g = g;
            LED_STRIP_BUFFER[index].b = b;
        }
    }

    virtual bool act_frame() = 0;

    virtual void stop() {
       active = false;
    }

    bool isActive() const { return active; }

    bool active = false;
    bool started = false;
    float frameTime;

protected:
    pixel_t* LED_STRIP_BUFFER;
    uint32_t ledcount;
    float startTime = 0;  // Start time in milliseconds
    float beatTime; // Time per beat in milliseconds
    uint32_t numFrames;
    uint32_t frameNumber = 0; // Frame number for animations that have multiple frames
    float lastFrameTime = 0;

    uint8_t red, green, blue;
};
