#pragma once

#include "led_animation.hpp"
#include <cstdint>

extern "C" {
#include "led_strip.h" 
}

class FuseWave : public LedAnimation {
public:
    FuseWave(led_strip_handle_t strip, uint32_t length, uint8_t r, uint8_t g, uint8_t b, uint32_t BPM);

    void start() override;
    bool act_frame() override;
    void stop() override;

private:
    uint8_t chunkSize = 5; // Number of LEDs to light up at once

};
