import re
import sys
import time
import serial
import logging
import collections


class Modem(object):
    """Wraps all low-level serial communications (actual read/write operations)
    """

    _logger = logging.getLogger(__name__)

    __RESPONSE_TERM = re.compile(r'^OK|ERROR|CONNECT|NO CARRIER$')
    __RESPONSE_IGNORE = re.compile(r'^$|RING$')
    __DTMF_PATTERN = re.compile(b'\x10/\x10([0-9A-D*#]{1})\x10~')

    def __init__(self, port, stop_event):
        self.__serial = serial.Serial(port=port, baudrate=115200, timeout=1)
        self.__serial.readlines()
        self.__stop_event = stop_event

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__serial.close()

    def at_command(self, cmd, timeout=3):
        self.__serial.write('AT{}\r'.format(cmd).encode('ascii'))
        return self.read_lines(timeout=timeout)

    def read_lines(self, timeout):
        start_time = time.time()
        messages = []
        while time.time() - start_time < timeout:
            if self.__stop_event.is_set():
                sys.exit()

            line = self.__serial.readline().decode('ascii').rstrip()
            self._logger.debug(line)
            if self.__RESPONSE_IGNORE.match(line):
                continue
            messages.append(line)
            if self.__RESPONSE_TERM.match(line):
                break

        return messages

    def _read_char(self):
        return self.__serial.read(1)

    def dtmf_listen(self, callback, *args):
        """Listen for DTMF tones, gather phone number
        """

        buffer = collections.deque(maxlen=6)
        while True:
            if self.__stop_event.is_set():
                sys.exit()

            buffer.append(self._read_char())
            m = self.__DTMF_PATTERN.match(b''.join(buffer))
            if m is None:
                continue
            digit = m.group(1).decode('ascii')
            self._logger.debug('/{}~'.format(digit))
            if callback(digit, *args):
                break
