

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

    // wifi stuff
    #include <sys/socket.h>   // socket, connect, send, recv
    #include <netinet/in.h>   // sockaddr_in
    #include <arpa/inet.h>    // inet_addr
    #include <unistd.h>       // close(), shutdown()

    #include "esp_wifi.h"
    #include "esp_event.h"
    #include "esp_netif.h"
    #include "nvs_flash.h"

    #include "cJSON.h"  // JSON parsing/serialization

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


// WIFI DATA

#define WIFI_SSID "REDACTED"
#define WIFI_PASSWORD "REDACTED"
#define SERVER_IP "10.0.0.162"
#define SERVER_PORT 5000
char esp32_mac_str[18] = {0}; 


//Handling Input for Lighting Commands
#define MAX_ANIM_PRIORITY 7

#define MAX_LED_TASKS 5
typedef enum {
    CMD_FUSE_WAVE,
    CMD_BLINK_LEDS
}LightingCommand;

QueueHandle_t inputQueue;
SemaphoreHandle_t led_strip_mutex = NULL;
pixel_t LED_STRIP_BUFFER[LED_STRIP_LENGTH] = {};  //init to all 0



// Forward Declarations
void animation_task(void *pvParameters);
void tcp_client_task(void *pvParameters);

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


/////// WIFI FUNCTIONS ///////

static void event_handler(void* arg, esp_event_base_t event_base,
                          int32_t event_id, void* event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) 
    {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED)
    {
        ESP_LOGI(TAG, "Disconnected. Reconnecting...");
        esp_wifi_connect();
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) 
    {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "Got IP:" IPSTR, IP2STR(&event->ip_info.ip));
        // Safe to start TCP client task now
        xTaskCreate(tcp_client_task, "tcp_client", 4096, NULL, 5, NULL);
    }
}

void wifi_init_sta(void)
{
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &event_handler,
                                                        NULL,
                                                        NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                                                        IP_EVENT_STA_GOT_IP,
                                                        &event_handler,
                                                        NULL,
                                                        NULL));

    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASSWORD,
        },
    };

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_LOGI(TAG, "Wi-Fi initialization complete.");
}


/////// MESSSAGE PARSING FUNCTIONs ////

void ProcessMessage(const char *json_str) {
    cJSON *root = cJSON_Parse(json_str);
    if (!root) {
        ESP_LOGE("JSON", "Failed to parse JSON");
        return;
    }

    cJSON *anim_item = cJSON_GetObjectItem(root, "Animation");
    if (!anim_item || !cJSON_IsString(anim_item)) {
        ESP_LOGE("JSON", "Animation field missing or not a string");
        cJSON_Delete(root);
        return;
    }

    const char *animation_type = anim_item->valuestring;

    // Handle each animation type


    if (strcmp(animation_type, "FuseWave") == 0)        //FuseWave
    {
        cJSON *r_item = cJSON_GetObjectItem(root, "r");
        cJSON *g_item = cJSON_GetObjectItem(root, "g");
        cJSON *b_item = cJSON_GetObjectItem(root, "b");
        cJSON *bpm_item = cJSON_GetObjectItem(root, "BPM");
        cJSON *beatPercent_item = cJSON_GetObjectItem(root, "beatPercentage");

        if (!r_item || !g_item || !b_item || !bpm_item || !beatPercent_item) {
            ESP_LOGE("JSON", "Missing required parameters for FuseWave");
        } else {
            int r = r_item->valueint;
            int g = g_item->valueint;
            int b = b_item->valueint;
            int bpm = bpm_item->valueint;
            float beatPercentage = beatPercent_item->valuedouble;


            ESP_LOGI(TAG, "Creating FuseWave: r=%d g=%d b=%d BPM=%d", r, g, b, bpm);
            FuseWave* fusewave = new FuseWave(LED_STRIP_BUFFER, LED_STRIP_LENGTH, r, g, b, bpm, beatPercentage);
            xTaskCreate(animation_task, "FuseWaveTask", 2048, fusewave, MAX_ANIM_PRIORITY, NULL);
        }
    }
    else if (strcmp(animation_type, "Blink") == 0)      //Blink
    {
        
    }

    cJSON_Delete(root);
}




////// Tasks //////

void input_task(void *pvParameters)
{
    while (1)
    {
        if (gpio_get_level(BUTTON1_GPIO) == 1) {
            ESP_LOGI(TAG, "Button 1 pressed, Fuse Wave");
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


void tcp_client_task(void *pvParameters)
{
    char rx_buffer[128];

    while (1) {
        struct sockaddr_in dest_addr;
        dest_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
        dest_addr.sin_family = AF_INET;
        dest_addr.sin_port = htons(SERVER_PORT);

        int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
        if (sock < 0) {
            ESP_LOGE(TAG, "Unable to create socket: errno %d", errno);
            vTaskDelay(2000 / portTICK_PERIOD_MS);
            continue;
        }

        ESP_LOGI(TAG, "Connecting to %s:%d...", SERVER_IP, SERVER_PORT);
        int err = connect(sock, (struct sockaddr *)&dest_addr, sizeof(dest_addr));
        if (err != 0) {
            ESP_LOGE(TAG, "Socket unable to connect: errno %d", errno);
            close(sock);
            vTaskDelay(2000 / portTICK_PERIOD_MS);
            continue;
        }

        ESP_LOGI(TAG, "Connected!");

        // Send initial hello JSON with MAC address
        char hello[128];
        snprintf(hello, sizeof(hello),
                "{\"id\":\"esp32_%s\",\"status\":\"online\"}\n", esp32_mac_str);

        send(sock, hello, strlen(hello), 0);

        while (1) 
        {
            int len = recv(sock, rx_buffer, sizeof(rx_buffer) - 1, 0);
            if (len < 0) {
                ESP_LOGE(TAG, "recv failed: errno %d", errno);
                break;
            } else if (len == 0) {
                ESP_LOGI(TAG, "Connection closed");
                break;
            } else {
                rx_buffer[len] = 0;
                ESP_LOGI(TAG, "Received: %s", rx_buffer);
                ProcessMessage(rx_buffer);
            }
        }

        if (sock != -1) {
            ESP_LOGI(TAG, "Shutting down socket and restarting...");
            shutdown(sock, 0);
            close(sock);
        }

        vTaskDelay(2000 / portTICK_PERIOD_MS);
    }
}


void lighting_handler_task(void *pvParameters) {
    LightingCommand cmd;
    while (1) {
        if (xQueueReceive(inputQueue, &cmd, portMAX_DELAY)) {
            switch (cmd) {
                case CMD_FUSE_WAVE: {
                    ESP_LOGI(TAG, "Creating fusewave");
                    FuseWave* fusewave = new FuseWave(LED_STRIP_BUFFER,LED_STRIP_LENGTH, 255, 255, 255, 152, 0.5);
                    xTaskCreate(animation_task, "FuseWaveTask", 2048, fusewave, MAX_ANIM_PRIORITY, NULL);
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

        //vTaskDelay(pdMS_TO_TICKS(10));
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



    //setup wifi
    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        nvs_flash_erase();
        nvs_flash_init();
    }

    wifi_init_sta();

    //Store mac address so ESP32 can be identified
    uint8_t mac[6];
    esp_wifi_get_mac(WIFI_IF_STA, mac);
    snprintf(esp32_mac_str, sizeof(esp32_mac_str), "%02X:%02X:%02X:%02X:%02X:%02X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    ESP_LOGI(TAG, "ESP32 MAC Address: %s", esp32_mac_str);


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