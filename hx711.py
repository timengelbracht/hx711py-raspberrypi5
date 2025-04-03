import gpiod
import time
import threading
from logzero import logger
from typing import Dict, List

# from https://pinout.xyz
# from https://pinout.xyz
DEFAULT_LINE_MAP: Dict[str, Dict[int, str]] = {
    'RPI_5': {
        29: 5,
        31: 6,
    }
}
DEFAULT_GPIOD_CONSUMER = 'hx711'

class HX711:
    def get_line_no(self, pin_no: int) -> int:
        if pin_no not in self.line_map:
            raise RuntimeError(f"pin:{pin_no} is not found in line map.")
        return self.line_map[pin_no]

    def __init__(self, dout: int, pd_sck: int, gain: int = 128, mutex: bool = False, chip=None, line_map_name: str = 'RPI_5', custome_line_map: Dict[int, str] = None):
        self.line_map = DEFAULT_LINE_MAP.get(line_map_name, custome_line_map)
        if not self.line_map:
            raise RuntimeError(f"line_map_name={line_map_name} is not found. You can also specify custome_line_map for your device.")

        self.chip = chip or gpiod.Chip("4", gpiod.Chip.OPEN_BY_NUMBER)
        self.PD_SCK = self.chip.get_line(self.get_line_no(pd_sck))
        self.DOUT = self.chip.get_line(self.get_line_no(dout))
        self.mutex_flag = mutex
        if self.mutex_flag:
            self.readLock = threading.Lock()

        self.PD_SCK.request(consumer=DEFAULT_GPIOD_CONSUMER, type=gpiod.LINE_REQ_DIR_OUT)
        self.DOUT.request(consumer=DEFAULT_GPIOD_CONSUMER, type=gpiod.LINE_REQ_DIR_IN)

        self.GAIN = 0
        self.REFERENCE_UNIT = 1
        self.REFERENCE_UNIT_B = 1
        self.OFFSET = 1.0
        self.OFFSET_B = 1.0
        self.lastVal = 0.0
        self.byte_format = 'MSB'
        self.bit_format = 'MSB'
        self.set_gain(gain)
        time.sleep(0.1)

    def convertFromTwosComplement24bit(self, inputValue) -> int:
        return -(inputValue & 0x800000) + (inputValue & 0x7fffff)

    def is_ready(self) -> bool:
        return self.DOUT.get_value() == 0

    def set_gain(self, gain):
        self.GAIN = {128: 1, 64: 3, 32: 2}.get(gain, 1)
        self.PD_SCK.set_value(0)
        self.readRawBytes()

    def get_gain(self) -> int:
        return {1: 128, 3: 64, 2: 32}.get(self.GAIN, 0)

    def readNextBit(self) -> int:
        self.PD_SCK.set_value(1)
        self.PD_SCK.set_value(0)
        return self.DOUT.get_value()

    def readNextByte(self) -> int:
        byteValue = 0
        for _ in range(8):
            if self.bit_format == 'MSB':
                byteValue = (byteValue << 1) | self.readNextBit()
            else:
                byteValue = (byteValue >> 1) | (self.readNextBit() * 0x80)
        return byteValue

    def readRawBytes(self) -> List[int]:
        if self.mutex_flag:
            self.readLock.acquire()
        while not self.is_ready():
            pass
        bytes_ = [self.readNextByte() for _ in range(3)]
        for _ in range(self.GAIN):
            self.readNextBit()
        if self.mutex_flag:
            self.readLock.release()
        return bytes_[::-1] if self.byte_format == 'LSB' else bytes_

    def read_long(self) -> int:
        dataBytes = self.readRawBytes()
        value = (dataBytes[0] << 16) | (dataBytes[1] << 8) | dataBytes[2]
        return self.convertFromTwosComplement24bit(value)

    def read_average(self, times: int = 3) -> float:
        return sum(self.read_long() for _ in range(times)) / max(times, 1)

    def read_median(self, times: int = 3) -> float:
        values = sorted(self.read_long() for _ in range(times))
        mid = len(values) // 2
        return values[mid] if times % 2 else (values[mid - 1] + values[mid]) / 2.0

    def get_value(self, times: int = 3) -> float:
        return self.get_value_A(times)

    def get_value_A(self, times: int = 3) -> float:
        return self.read_median(times) - self.get_offset_A()

    def get_value_B(self, times: int = 3) -> float:
        g = self.get_gain()
        self.set_gain(32)
        value = self.read_median(times) - self.get_offset_B()
        self.set_gain(g)
        return value

    def get_weight(self, times: int = 3) -> float:
        return self.get_weight_A(times)

    def get_weight_A(self, times: int = 3) -> float:
        return self.get_value_A(times) / self.REFERENCE_UNIT

    def get_weight_B(self, times: int = 3) -> float:
        return self.get_value_B(times) / self.REFERENCE_UNIT_B

    def tare(self, times: int = 15) -> float:
        return self.tare_A(times)

    def tare_A(self, times: int = 15) -> float:
        ref_backup = self.get_reference_unit_A()
        self.set_reference_unit_A(1)
        offset = self.read_average(times)
        self.set_offset_A(offset)
        self.set_reference_unit_A(ref_backup)
        return offset

    def tare_B(self, times: int = 15) -> float:
        ref_backup = self.get_reference_unit_B()
        gain_backup = self.get_gain()
        self.set_reference_unit_B(1)
        self.set_gain(32)
        offset = self.read_average(times)
        self.set_offset_B(offset)
        self.set_gain(gain_backup)
        self.set_reference_unit_B(ref_backup)
        return offset

    def set_reading_format(self, byte_format: str = "LSB", bit_format: str = "MSB"):
        self.byte_format = byte_format if byte_format in ["LSB", "MSB"] else self.byte_format
        self.bit_format = bit_format if bit_format in ["LSB", "MSB"] else self.bit_format

    def set_offset(self, offset: float):
        self.set_offset_A(offset)

    def set_offset_A(self, offset: float):
        self.OFFSET = offset

    def set_offset_B(self, offset: float):
        self.OFFSET_B = offset

    def get_offset(self) -> float:
        return self.OFFSET

    def get_offset_A(self) -> float:
        return self.OFFSET

    def get_offset_B(self) -> float:
        return self.OFFSET_B

    def set_reference_unit(self, ref: int):
        self.set_reference_unit_A(ref)

    def set_reference_unit_A(self, ref: int):
        if ref == 0:
            raise ValueError("Reference unit cannot be 0")
        self.REFERENCE_UNIT = ref

    def set_reference_unit_B(self, ref: int):
        if ref == 0:
            raise ValueError("Reference unit cannot be 0")
        self.REFERENCE_UNIT_B = ref

    def get_reference_unit(self) -> int:
        return self.REFERENCE_UNIT

    def get_reference_unit_A(self) -> int:
        return self.REFERENCE_UNIT

    def get_reference_unit_B(self) -> int:
        return self.REFERENCE_UNIT_B

    def power_down(self):
        if self.mutex_flag:
            self.readLock.acquire()
        self.PD_SCK.set_value(0)
        self.PD_SCK.set_value(1)
        time.sleep(0.0001)
        if self.mutex_flag:
            self.readLock.release()

    def power_up(self):
        if self.mutex_flag:
            self.readLock.acquire()
        self.PD_SCK.set_value(0)
        time.sleep(0.0001)
        if self.mutex_flag:
            self.readLock.release()
        if self.get_gain() != 128:
            self.readRawBytes()

    def reset(self):
        self.power_down()
        self.power_up()
