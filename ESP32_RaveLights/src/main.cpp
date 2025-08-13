

extern "C" {
    #include <stdio.h>
    #include "freertos/FreeRTOS.h"
    #include "freertos/task.h"
    #include "freertos/semphr.h"
    #include "freertos/queue.h"
    #include "driver/gpio.h"

    #include "led_strip.h"
    
    #include "esp_log.h"
    #include "esp_err.h"
}

#include "led_animation.hpp"
#include "animations/fuse_wave.hpp"


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
#define MAX_ANIM_PRIORITY 7
typedef enum {
    CMD_FUSE_WAVE,
    CMD_BLINK_LEDS
}LightingCommand;
QueueHandle_t inputQueue;
uint8_t numActiveAnimations = 0;
SemaphoreHandle_t led_strip_mutex = NULL;
pixel_t LED_STRIP_BUFFER[LED_STRIP_LENGTH] = {};  //init to all 0
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


// LED Task Handling ////

#define MAX_LED_TASKS 5



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

        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

void lighting_handler_task(void *pvParameters) {
    LightingCommand cmd;
    while (1) {
        if (xQueueReceive(inputQueue, &cmd, portMAX_DELAY)) {
            switch (cmd) {
                case CMD_FUSE_WAVE: {
                    ESP_LOGI(TAG, "Creating fusewave");
                    FuseWave* fusewave = new FuseWave(LED_STRIP_BUFFER,LED_STRIP_LENGTH, 255, 255, 255, 160);
                    xTaskCreate(animation_task, "FuseWaveTask", 2048, fusewave, MAX_ANIM_PRIORITY, NULL);
                    numActiveAnimations++;
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

        vTaskDelay(pdMS_TO_TICKS(10));
    }
}


// Responsible for refreshing the LED strip 
void lighting_refresh_task(void *pvParameters) {
    while (1)
    {
        if (xSemaphoreTake(led_strip_mutex, portMAX_DELAY) == pdTRUE) 
        {
            // Clear LED Strip
            ESP_ERROR_CHECK(led_strip_clear(led_strip));

            // Copy LED Buffer into actual strip
            for (int i = 0; i < LED_STRIP_LENGTH; i++) {
                ESP_ERROR_CHECK(led_strip_set_pixel(led_strip, i, LED_STRIP_BUFFER[i].r, LED_STRIP_BUFFER[i].g, LED_STRIP_BUFFER[i].b));
            }

            // Refresh LED strip
            ESP_ERROR_CHECK(led_strip_refresh(led_strip));

            // Clear buffer
            memset(LED_STRIP_BUFFER, 0, sizeof(LED_STRIP_BUFFER));

            xSemaphoreGive(led_strip_mutex);
        } 

        vTaskDelay(pdMS_TO_TICKS(30)); // 30fps
    }
}

void animation_task(void *pvParameters) {
    LedAnimation* animation = static_cast<LedAnimation*>(pvParameters);
    
    while(1)
    {
        if(!animation->started)
            animation->start();

        if(animation->active)
        {
            // Get control of led strip
            if (xSemaphoreTake(led_strip_mutex, portMAX_DELAY) == pdTRUE) {
                animation->act_frame();
                xSemaphoreGive(led_strip_mutex);
            } else
                ESP_LOGW("AnimationTask", "Failed to take LED strip mutex");
            
            vTaskDelay(pdMS_TO_TICKS(10));
        }
        else
        {
            numActiveAnimations--;
            vTaskDelete(NULL);
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

    led_strip_mutex = xSemaphoreCreateMutex();
    if (led_strip_mutex == NULL) {
        ESP_LOGE(TAG, "Failed to create LED strip mutex");
        return;
    }

    ESP_LOGI(TAG, "Reached main loop");

    inputQueue = xQueueCreate(5, sizeof(LightingCommand));

    xTaskCreate(input_task, "InputTask", 2048, NULL, 1, NULL);
    xTaskCreate(lighting_handler_task, "LightingTask", 2048, NULL, 2, NULL);
    xTaskCreate(lighting_refresh_task, "LightingRefreshTask", 2048, NULL, 10, NULL);

}