

extern "C" {
    #include <stdio.h>
    #include "freertos/FreeRTOS.h"
    #include "freertos/task.h"
    #include "freertos/queue.h"
    #include "driver/gpio.h"

    #include "led_strip.h"
    
    #include "esp_log.h"
    #include "esp_err.h"
}

#include "animations/fuse_wave.hpp"
#include "animation_queue.hpp"


// GPIO Definitions
#define BUTTON1_GPIO GPIO_NUM_23
#define BUTTON2_GPIO GPIO_NUM_22

#define LED_STRIP_GPIO GPIO_NUM_18    

//LED Strip
#define LED_STRIP_USE_DMA  0
#define LED_STRIP_RMT_RES_HZ 10000000
#define LED_STRIP_MEMORY_BLOCK_WORDS 64 
#define LED_STRIP_LENGTH 50    
led_strip_handle_t led_strip = NULL;

//Handling Input for Lighting Commands
#define MAX_ANIMATIONS 5 //max animations one strip can handle at once
typedef enum {
    CMD_FUSE_WAVE,
    CMD_BLINK_LEDS
}LightingCommand;
QueueHandle_t inputQueue;
uint8_t animationPriority = 9;
void animation_task(void *pvParameters);

static const char *TAG = "ESP32";

/////// LED FUNCTIONS //////

led_strip_handle_t configure_ledstrip(void)
{
    
    led_strip_config_t strip_config = {
        .strip_gpio_num = LED_STRIP_GPIO, 
        .max_leds = LED_STRIP_LENGTH,     
        .led_model = LED_MODEL_WS2812,        
        .color_component_format = LED_STRIP_COLOR_COMPONENT_FMT_RGB,
        .flags = {
            .invert_out = false, 
        }
    };

    // LED strip backend configuration: RMT
    led_strip_rmt_config_t rmt_config = {
        .clk_src = RMT_CLK_SRC_DEFAULT,    
        .resolution_hz = LED_STRIP_RMT_RES_HZ,
        .mem_block_symbols = LED_STRIP_MEMORY_BLOCK_WORDS, 
        .flags = {
            .with_dma = LED_STRIP_USE_DMA,   
        }
    };

    // LED Strip object handle
    led_strip_handle_t led_strip;
    ESP_ERROR_CHECK(led_strip_new_rmt_device(&strip_config, &rmt_config, &led_strip));
    ESP_LOGI(TAG, "Created LED strip object with RMT backend");
    return led_strip;
}

void blink_leds(led_strip_handle_t led_strip, int delay_ms, int times) {

    for (int i = 0; i < times; i++) {
        // Turn all LEDs on (set to white color)
        for (int j = 0; j < LED_STRIP_LENGTH; j++) {
            ESP_ERROR_CHECK(led_strip_set_pixel(led_strip, j, 255, 255, 255));
        }
        ESP_ERROR_CHECK(led_strip_refresh(led_strip));
        vTaskDelay(pdMS_TO_TICKS(delay_ms));

        // Turn all LEDs off
        ESP_ERROR_CHECK(led_strip_clear(led_strip));
        vTaskDelay(pdMS_TO_TICKS(delay_ms));
    }
}
void fuse_wave(led_strip_handle_t led_strip, uint8_t red, uint8_t green, uint8_t blue, int speed_ms) {
    for (int i = 0; i < LED_STRIP_LENGTH; i++) {
        // Clear all LEDs
        ESP_ERROR_CHECK(led_strip_clear(led_strip));

        // Turn on the current LED
        ESP_ERROR_CHECK(led_strip_set_pixel(led_strip, i, red, green, blue));
        ESP_ERROR_CHECK(led_strip_refresh(led_strip));

        // Delay for the specified speed
        vTaskDelay(pdMS_TO_TICKS(speed_ms));
    }
}


////// Tasks //////

void input_task(void *pvParameters)
{
    while (1)
    {
        if (gpio_get_level(BUTTON1_GPIO) == 1) {
            ESP_LOGI(TAG, "Button 1 pressed");
            LightingCommand cmd = CMD_FUSE_WAVE;
            xQueueSend(inputQueue, &cmd, portMAX_DELAY);
            vTaskDelay(pdMS_TO_TICKS(200)); 
        }

        if (gpio_get_level(BUTTON2_GPIO) == 1) {
            ESP_LOGI(TAG, "Button 2 pressed, Blink");
            LightingCommand cmd = CMD_BLINK_LEDS;
            xQueueSend(inputQueue, &cmd, portMAX_DELAY);
            vTaskDelay(pdMS_TO_TICKS(200));
        }

        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

void lighting_handler_task(void *pvParameters) {
    LightingCommand cmd;
    while (1) {
        if (xQueueReceive(inputQueue, &cmd, portMAX_DELAY)) {
            switch (cmd) {
                case CMD_FUSE_WAVE: {
                    ESP_LOGI(TAG, "Creating fusewave");
                    FuseWave* fusewave = new FuseWave(led_strip,LED_STRIP_LENGTH, 255, 255, 255, 120);
                    xTaskCreate(animation_task, "FuseWaveTask", 2048, fusewave, animationPriority--, NULL);
                    break;
                }
                case CMD_BLINK_LEDS:
                    ESP_LOGI(TAG, "Blinking LEDs");
                    break;
                default:
                    ESP_LOGW(TAG, "Unknown command received");
                    break;
            }
        }
    }
}

// Clears LEDs before new "frame" of animations
void lighting_clear_task(void *pvParameters) {
    while (1) {
        ESP_ERROR_CHECK(led_strip_clear(led_strip));
        ESP_LOGI("LightingClearTask", "LEDs cleared");
        vTaskDelay(pdMS_TO_TICKS(100)); // 10 fps
    }
}

// Once all animations have run their frames, refresh
void lighting_refresh_task(void *pvParameters) {
    while (1) {
        ESP_ERROR_CHECK(led_strip_refresh(led_strip));
        ESP_LOGI("LightingRefreshTask", "LEDs refreshed");
        vTaskDelay(pdMS_TO_TICKS(100)); //10 fps
    }
}

void animation_task(void *pvParameters) {
    LedAnimation* animation = static_cast<LedAnimation*>(pvParameters);

    while(1)
    {
        ESP_LOGI("AnimationTask", "Inside animation task");
        
        if(!animation->started)
            animation->start();

        if(animation->active)
        {
            ESP_ERROR_CHECK(led_strip_clear(led_strip));
            animation->act_frame();
            ESP_ERROR_CHECK(led_strip_refresh(led_strip));

            if(!animation->active)
            {
                animation->stop();
                vTaskDelete(NULL);
                animationPriority++;
            }

            vTaskDelay(pdMS_TO_TICKS(animation->frameTime));
        }else
        {
            animation->stop();
            vTaskDelete(NULL);
            animationPriority++;
        }

    }
}


/// Main Code ///

void setup()
{
    // Configure LED GPIO as output
    gpio_config_t led_io_conf = {
        .pin_bit_mask = (1ULL << LED_STRIP_GPIO),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&led_io_conf);

    // Configure BUTTON1_GPIO and BUTTON2_GPIO as input with pull-down
    gpio_config_t button_io_conf = {
        .pin_bit_mask = (1ULL << BUTTON1_GPIO) | (1ULL << BUTTON2_GPIO),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&button_io_conf);




}


extern "C" void app_main(void) 
{

   setup();

    led_strip = configure_ledstrip();
    if (led_strip == NULL) {
        ESP_LOGE(TAG, "Failed to configure LED strip");
        return;
    }

    vTaskDelay(pdMS_TO_TICKS(1000));
    fflush(stdout);
    ESP_LOGI(TAG, "Reached main loop");

    inputQueue = xQueueCreate(5, sizeof(LightingCommand));

    xTaskCreate(input_task, "InputTask", 2048, NULL, 1, NULL);
    xTaskCreate(lighting_handler_task, "LightingTask", 2048, NULL, 2, NULL);
   // xTaskCreate(lighting_clear_task, "LightingClearTask", 2048, NULL, 10, NULL);
    //xTaskCreate(lighting_refresh_task, "LightingRefreshTask", 2048, NULL, 6, NULL);

}