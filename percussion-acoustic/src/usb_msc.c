#include "usb_msc.h"
#include "config.h"
#include "storage_fat.h"
#include "tinyusb.h"
#include "tinyusb_msc.h"
#include "esp_log.h"
#include "driver/gpio.h"

static const char *TAG = "USB_MSC";
static tinyusb_msc_storage_handle_t msc_handle;

void usb_msc_enter_mode(wl_handle_t wl_handle) {
    ESP_LOGI(TAG, "Entering MSC Mode");

    const tinyusb_config_t tusb_cfg = { 0 };
    ESP_ERROR_CHECK(tinyusb_driver_install(&tusb_cfg));
    
    
    const tinyusb_msc_storage_config_t msc_config = {
        .medium = { .wl_handle = wl_handle },
    };
    ESP_ERROR_CHECK(tinyusb_msc_new_storage_spiflash(&msc_config, &msc_handle));
    ESP_ERROR_CHECK(tinyusb_msc_set_storage_mount_point(msc_handle, TINYUSB_MSC_STORAGE_MOUNT_USB));

    gpio_set_level(LED_UPLOAD_GPIO, 1);
}

void usb_msc_exit_mode(void) {
    ESP_LOGI(TAG, "Exiting MSC Mode");
    
    tinyusb_driver_uninstall();
    gpio_set_level(LED_UPLOAD_GPIO, 0);
}
