#include "blink.hpp"

Blink::FuseWave(pixel_t* ledstrip_buffer, uint32_t length, uint8_t r, uint8_t g, uint8_t b, uint32_t BPM)
    : LedAnimation(ledstrip_buffer, length)
{
 
}

void Blink::start() 
{
   LedAnimation::start() 

}

bool Blink::act_frame() 
{

    if(!active) 
        return false;

    if (frameNumber > numFrames) {
        stop();
        return false;
    }




    return true;
}

void Blink::stop() {
    LedAnimation::stop();
   
}