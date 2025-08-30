#pragma once

#include "led_animation.hpp"
#include <cstdint>

extern "C" {
#include "led_strip.h" 
}

class Blink: public LedAnimation {
public:
    Blink(pixel_t* ledstrip_buffer, uint32_t length, uint8_t r, uint8_t g, uint8_t b, uint32_t BPM, float beatPercentage);

    void start() override;
    bool act_frame() override;
    void stop() override;

private:
    float duration; // Number of LEDs to light up at once

};
