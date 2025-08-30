#include "blink.hpp"

Blink::Blink(pixel_t* ledstrip_buffer, uint32_t length, uint8_t r, uint8_t g, uint8_t b, uint32_t BPM, float beatPercentage)
    : LedAnimation(ledstrip_buffer, length)
{
 this->beatPercentage = beatPercentage;
}

void Blink::start() 
{
   LedAnimation::start();

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