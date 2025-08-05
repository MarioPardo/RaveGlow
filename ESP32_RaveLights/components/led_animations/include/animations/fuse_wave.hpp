#pragma once

#include "led_animation.hpp"
#include <cstdint>

class FuseWave : public LedAnimation {
public:
    FuseWave(led_strip_handle_t strip, uint8_t r, uint8_t g, uint8_t b, uint32_t BPM);

    void start() override;
    bool act_frame() override;
    void stop() override;

private:
    uint8_t red, green, blue;
    uint32_t start_time;
    int current_pos;
};
