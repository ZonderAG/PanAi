idf_component_register(
    SRCS "main.c"
         "audio_i2s.c"
         "dsp_pipeline.c"
         "solenoid.c"
         "uart_comm.c"
         "state_machine.c"
         "led_status.c"
    INCLUDE_DIRS "."
    REQUIRES esp-dsp
)
