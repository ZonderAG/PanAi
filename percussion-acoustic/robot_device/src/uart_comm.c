#include "uart_comm.h"
#include "driver/uart.h"
#include "config.h"
#include "esp_log.h"
#include <string.h>

static const char *TAG = "UART_COMM";

void uart_comm_init(void) {
    uart_config_t uart_config = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    ESP_ERROR_CHECK(uart_driver_install(UART_PORT, 1024, 1024, 0, NULL, 0));
    ESP_ERROR_CHECK(uart_param_config(UART_PORT, &uart_config));
    ESP_ERROR_CHECK(uart_set_pin(UART_PORT, UART_TX_PIN, UART_RX_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));
    ESP_LOGI(TAG, "UART initialized at 115200 bps");
}

bool uart_comm_check_strike_cmd(void) {
    uint8_t data[16];
    int length = uart_read_bytes(UART_PORT, data, sizeof(data), 0);
    if (length > 0) {
        for (int i = 0; i < length; i++) {
            if (data[i] == 'S') {
                return true;
            }
        }
    }
    return false;
}

void uart_comm_send_spectrum(int16_t *data, uint16_t length) {
    const char *header = "SPEC";
    uart_write_bytes(UART_PORT, header, 4);
    uint16_t len = length;
    uart_write_bytes(UART_PORT, &len, sizeof(len));
    uart_write_bytes(UART_PORT, data, length * sizeof(int16_t));
    const char *footer = "END\n";
    uart_write_bytes(UART_PORT, footer, 4);
}
