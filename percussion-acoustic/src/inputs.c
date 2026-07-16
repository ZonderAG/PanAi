#include "inputs.h"
#include "config.h"

void inputs_init(void) {
    gpio_config_t io_conf = {
        .intr_type = GPIO_INTR_DISABLE,
        .mode = GPIO_MODE_INPUT,
        .pin_bit_mask = (1ULL << BTN_TRIGGER_GPIO) | (1ULL << SW_DEFECT_NORMAL_GPIO) | (1ULL << SW_MODE_UPLOAD_GPIO),
        .pull_down_en = 0,
        .pull_up_en = 1 
    };
    gpio_config(&io_conf);
}

bool inputs_is_trigger_pressed(void) {
    
    return gpio_get_level(BTN_TRIGGER_GPIO) == 0;
}

bool inputs_is_upload_mode_pressed(void) {
    
    return gpio_get_level(SW_MODE_UPLOAD_GPIO) == 0;
}

hit_label_t inputs_read_current_label(void) {
    
    return gpio_get_level(SW_DEFECT_NORMAL_GPIO) ? LABEL_NORMAL : LABEL_DEFECT;
}
