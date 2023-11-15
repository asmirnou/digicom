#!/usr/bin/env venv/bin/python

import re
import sys
import logging
import threading
import collections
import contact_id
from os import environ
from functools import partial
from signal import signal, SIGINT, SIGTERM
from threading import Event
from modem import Modem
from mqtt import event_queue, publish
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


def init_signals(stop_event):
    for s in [SIGINT, SIGTERM]:
        signal(s, partial(lambda se, *_args: se.set(), stop_event))


def init_logs(names, level):
    formatter = logging.Formatter(fmt='%(name)-10s   %(levelname)-8s: %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setStream(sys.stdout)

    for name in names:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)


def gather(digit, phone_number, phone_number_pattern):
    phone_number.append(digit)
    return phone_number_pattern.match(''.join(phone_number))


def arc(stop_event):
    logger = logging.getLogger(__name__)

    phone_num_pattern = re.compile(args.pattern + '$')
    msg_pattern = re.compile(r'^[0-9B-F]{16}$')

    with Modem(port=args.device, stop_event=stop_event) as modem:
        assert 'OK' in modem.at_command('I3')
        configuration = modem.at_command('&V')
        assert 'OK' in configuration

        # Get value of S7 register, which is wait time for carrier in seconds.
        # It will be used also as waiting time for messages, until the alarm panel
        # disconnects, then modem transmits NO CARRIER.
        m = re.search(r'\sS07:(\d+)\s', '\n'.join(configuration))
        assert m is not None
        wait_time_for_carrier = int(m.group(1))

        # Select DTMF Alarm mode operation (Ademco DTMF Contact ID protocol)
        assert 'OK' in modem.at_command('+MS=ALM1')

        try:
            while True:
                # Select voice mode
                assert 'OK' in modem.at_command('+FCLASS=8')
                # Connect DCE to the line and go off-hook
                assert 'OK' in modem.at_command('+VLS=1')

                # Listen for DTMF tones in format, gather phone number
                phone_number = collections.deque(maxlen=20)
                modem.dtmf_listen(gather, phone_number, phone_num_pattern)

                # Select data mode
                assert 'OK' in modem.at_command('+FCLASS=0')
                # Answer call and transmit the Handshake tone
                assert 'CONNECT' in modem.at_command('A')

                # Read messages. The Kissoff tone is sent automatically by modem.
                messages = modem.read_lines(wait_time_for_carrier)
                assert 'NO CARRIER' in messages

                # Handle messages
                for msg in filter(lambda m: msg_pattern.match(m), messages):
                    event = contact_id.parse_message(msg)
                    logger.info(event)
                    event_queue.put(event)
        finally:
            modem.at_command('H')


if __name__ == '__main__':
    parser = ArgumentParser(description='Digicom receiver for Alarm Control Panel',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--device', dest='device', metavar='DEVICE', default='/dev/ttyACM0',
                        help='modem device name')
    parser.add_argument('-p', '--pattern', dest='pattern', metavar='PATTERN', type=str, default='\d{11}',
                        help='phone number pattern to answer when the control panel dials')
    parser.add_argument('-l', '--log-level', dest='log_level', metavar='LOG_LEVEL',
                        type=str, choices=['debug', 'info', 'warning', 'error', 'fatal'],
                        default=environ.get('LOG_LEVEL', 'info'), help='log level')
    args = parser.parse_args()

    stop_event = Event()
    try:
        init_signals(stop_event)
        init_logs(['digicom', 'modem', 'mqtt'], args.log_level.upper())

        threading.Thread(target=publish, daemon=True, args=(stop_event, 'digicom')).start()

        arc(stop_event)
    finally:
        stop_event.set()
