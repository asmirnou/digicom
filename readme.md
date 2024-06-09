# DigiCom

DigiCom simulates and replaces the phone line connection to the control panel’s Digi-Modem. The control panel’s Digi-Modem must use Contact ID alarm format to report to an Alarm Receiving Centre (ARC). In the event the control panel needs to send a signal to the ARC, DigiCom captures the message and forwards it via MQTT to the Home Assistant. Thus, DigiCom lets you monitor your alarm control panel locally without having to pay monthly fees or have a service contract.

Conexant modem CX930xx is needed for DigiCom. Telephone line connection is wired as shown on the [schematic diagram](Telephone%20Line%20Simulator/Telephone%20Line%20Simulator.pdf). The modem and the panel are connected in series to a 12V power supply that usually can be taken from the control panel auxiliary contacts. It is necessary to ensure that the line current is approximately 25 mA when communicating between the modem and the panel. If the current is higher, a limiting resistor must be installed.

The Digi-Modem must have an ARC telephone number and account number programmed for DigiCom to work. Check your control panel configuration for any other settings that may apply.

## Usage

The application can be deployed to a [Raspberry Pi](https://www.raspberrypi.com/) with the modem connected to a USB port and the panel connected to the modem via RJ11 cable.

```bash
./digicom.py --help
usage: digicom.py [-h] [-d DEVICE] [-p PATTERN] [-l LOG_LEVEL]

Digicom receiver for Alarm Control Panel

options:
  -h, --help            show this help message and exit
  -d DEVICE, --device DEVICE
                        modem device name (default: /dev/ttyACM0)
  -p PATTERN, --pattern PATTERN
                        phone number pattern to answer when the control panel dials (default: \d{11})
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        log level (default: info)
```

The hostname or IP address of the remote MQTT broker can be set using `MQTT_HOST` environmental variable.

Example of the decoded Contact ID event sent to MQTT topic `digicom/events`:

```json
{
    "account": "1234",
    "type": "opening",
    "code": "383",
    "name": "Sensor tamper",
    "group": "1",
    "zone": "3"
}
```

## Dev notes

The below explains how to receive a message from the control panel using Conexant modem AT commands:

### Ademco Contact ID format

Select DTMF Alarm mode operation, select voice mode and go off-hook:
```text
AT+MS=ALM1
OK
AT+FCLASS=8
OK
AT+VLS=1
OK
```

Then listen for DTMF tones, gather phone number:
```text
/0~/1~/2~/3~/4~/5~/6~/7~/8~/9~/9~
```

Then switch to data mode and receive a message:
```text
AT+FCLASS=0
OK
ATA

CONNECT

123418162701000E

NO CARRIER
```

### Ademco Fast Format (not implemented)

Select voice mode and go off-hook:

```text
AT+FCLASS=8
OK
AT+VLS=1
OK
```

Then listen for DTMF tones, gather phone number:
```text
/0~/1~/2~/3~/4~/5~/6~/7~/8~/9~/9~
```

Send handshake tone, receive a message, send kiss-off tone:
```text
AT+VTS=[1400,,10],[,,10],[2300,,10]
OK

/1~/2~/3~/4~/5~/5~/5~/5~/5~/5~/5~/1~/7~

AT+VTS=[1400,,80]
OK
```
