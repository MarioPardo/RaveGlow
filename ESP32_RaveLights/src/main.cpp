extern "C" {
    #include <stdio.h>
    #include "freertos/FreeRTOS.h"
    #include "freertos/task.h"

    #include "driver/gpio.h"
}

#define BUTTON1_GPIO GPIO_NUM_23
#define BUTTON2_GPIO GPIO_NUM_22


extern "C" void app_main(void) {
    // Configure GPIO pins
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << BUTTON1_GPIO) | (1ULL << BUTTON2_GPIO),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,   // Enable internal pull-up resistor
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE       // No interrupts yet
    };
    gpio_config(&io_conf);

    printf("Hello!");
    printf(" ");
    printf(" ");

    while (1) {
        int button1_state = gpio_get_level(BUTTON1_GPIO);
        int button2_state = gpio_get_level(BUTTON2_GPIO);

        if (button1_state == 1) {
            printf("Button 1 is Pressed\n");
        }

        if (button2_state == 1) {
            printf("Button 2 is Pressed\n");
        }

        vTaskDelay(pdMS_TO_TICKS(200));  // Check every 200 ms
    }
}