idf_component_register(
    SRCS "main.c"
         "audio_i2s.c"
         "dsp_pipeline.c"
         "solenoid.c"
         "inputs.c"
         "storage_fat.c"
         "usb_msc.c"
         "state_machine.c"
         "led_status.c"
    INCLUDE_DIRS "."
    REQUIRES esp-dsp esp_tinyusb fatfs wear_levelling
)
