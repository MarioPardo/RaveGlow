#include "animations/blink.hpp"

#include <cmath>

extern "C" {
    #include "esp_timer.h"
    #include "led_strip.h" 
}

Blink::Blink(pixel_t* ledstrip_buffer, uint32_t length, uint8_t r, uint8_t g, uint8_t b, uint32_t BPM, float beatPercentage)
    : LedAnimation(ledstrip_buffer, length)
{
    this->red = r;
    this->green = g;
    this->blue = b;

    this->beatPercentage = beatPercentage  ; 

    this->beatTime = 60000 / BPM; // Convert BPM to milliseconds per beat
    this->duration = std::round(this->beatTime * this->beatPercentage * 100.0) / 100.0;
    
}

void Blink::start() 
{
   LedAnimation::start();

   for(int i = 0; i < ledcount; i++)
    {
        set_pixel(i, red, green, blue);
    }

   this->lastFrameTime = esp_timer_get_time() / 1000;
}

bool Blink::act_frame() 
{

    if(!active) 
        return false;


    float timeSinceLastFrame = (esp_timer_get_time() / 1000) - lastFrameTime;

    //Turn off if time to do so
    if( timeSinceLastFrame >= duration)
    {
        for(int i = 0; i < ledcount; i++)
        {
            set_pixel(i,0,0,0);
        }

        stop();
        return false;
    }

    return true;
}

void Blink::stop() {
    LedAnimation::stop();
   
}