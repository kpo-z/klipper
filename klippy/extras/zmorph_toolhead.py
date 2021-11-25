import logging
import pins
from . import bus


BACKCART_I2C = {
    'ADDRESS': 0x5E,
    'THRESHOLD' : 0x4B,
    'TARE' : 0x4C,
    'RAW' : 0x4E,
    'REBOOT' : 0xD9
}

TOOLHEAD_I2C = {
    'ADDRESS': 0x17,
    'REG_FILAMENT_SENSOR': 0xAF
}

class ZmorphToolhead:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name().split()[-1]
        self.reactor = self.printer.get_reactor()

        # set up backcart i2c
        logging.info("Backcart: Setting up backcart I2C.")
        self.backcart_i2c = bus.MCU_I2C_from_config(config, default_addr = BACKCART_I2C['ADDRESS'], default_speed = 100000)
        self.backcart_mcu = self.backcart_i2c.get_mcu()
        
        # set up toolhead i2c
        logging.info("Backcart: Setting up toolhead I2C.")
        self.toolhead_address = TOOLHEAD_I2C['ADDRESS']
        self.toolhead_i2c = bus.MCU_I2C_from_config(config, default_addr = TOOLHEAD_I2C['ADDRESS'], default_speed = 100000)
        self.toolhead_mcu = self.toolhead_i2c.get_mcu()

        # register GCODE command
        logging.info("Backcart: Registering commands.")
        gcode = self.printer.lookup_object('gcode')
        gcode.register_mux_command('BACKCART_REBOOT', 'TOOLHEAD', self.name, self.cmd_BACKCART_REBOOT, desc="Reboot backcart MCU")
        gcode.register_mux_command('BACKCART_TARE', 'TOOLHEAD', self.name, self.cmd_BACKCART_TARE, desc="Tare the backcart tenso")
        gcode.register_mux_command('BACKCART_THRESHOLD', 'TOOLHEAD', self.name, self.cmd_BACKCART_THRESHOLD, desc="Set the backcart threshold")
        gcode.register_mux_command('BACKCART_READ_RAW', 'TOOLHEAD', self.name, self.cmd_BACKCART_READ_RAW, desc="Get raw data from tenso")

        self.printer.register_event_handler("klippy:connect", self.handle_connect)

    def backcart_reboot(self):
        logging.info("Backcart: Rebooting backcart.")
        self.backcart_i2c.i2c_write([BACKCART_I2C['REBOOT']])
        self.reactor.pause(self.reactor.monotonic() + .15)

    def backcart_tare(self):
        logging.info("Backcart: Taring tenso.")
        self.backcart_i2c.i2c_write([BACKCART_I2C['TARE']])
        self.reactor.pause(self.reactor.monotonic() + .15)

    def backcart_set_threshold(self, threshold):
        logging.info("Backcart: Setting threshold to: %d." % threshold)
        self.backcart_i2c.i2c_write([BACKCART_I2C['THRESHOLD'], threshold])
        self.reactor.pause(self.reactor.monotonic() + .15)

    def backcart_read_raw(self):
        params = self.backcart_i2c.i2c_read([BACKCART_I2C['RAW']], 1)
        response = bytearray(params['response'])
        logging.info("Backcart: Read raw: %d." % response[0])

    def cmd_BACKCART_REBOOT(self, gcmd):
        self.backcart_reboot()

    def cmd_BACKCART_TARE(self, gcmd):
        self.backcart_tare()

    def cmd_BACKCART_THRESHOLD(self, gcmd):
        threshold = gcmd.get_int('THRESHOLD', None)
        self.backcart_set_threshold(threshold)

    def cmd_BACKCART_READ_RAW(self, gcmd):
        self.backcart_read_raw()

    def handle_connect(self):
        logging.info("Backcart: Initializing backcart.")
        self.backcart_reboot()
        self.backcart_tare()
        # change value to read from config
        self.backcart_set_threshold(7)


def load_config_prefix(config):
    return ZmorphToolhead(config)