import logging

class LaserPower:
    def __init__(self, config):
        self.config = config['laser_safety']
        self.gpio_pin = self.config['gpio_pin']
        self.auto_off = self.config['auto_off_on_disconnect']
        self.logger = logging.getLogger(__name__)
        self.is_on = False
        
        # In a real environment, we would use RPi.GPIO or gpiozero here
        # import RPi.GPIO as GPIO
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(self.gpio_pin, GPIO.OUT)
        # GPIO.output(self.gpio_pin, GPIO.LOW)
        self.logger.info(f"Initialized LaserPower on GPIO pin {self.gpio_pin}")

    def turn_on(self):
        if not self.is_on:
            self.logger.info("Turning ON laser...")
            # GPIO.output(self.gpio_pin, GPIO.HIGH)
            self.is_on = True

    def turn_off(self):
        if self.is_on:
            self.logger.info("Turning OFF laser...")
            # GPIO.output(self.gpio_pin, GPIO.LOW)
            self.is_on = False

    def check_watchdog(self, active):
        if self.auto_off and not active:
            if self.is_on:
                self.logger.warning("Watchdog triggered! Turning off laser.")
                self.turn_off()

    def cleanup(self):
        self.turn_off()
        # GPIO.cleanup(self.gpio_pin)
