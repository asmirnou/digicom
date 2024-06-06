# Description

DigiCom simulates and replaces [the phone line connection](Telephone%20Line%20Simulator/Telephone%20Line%20Simulator.pdf) 
to the control panel’s Digi-Modem. The control panel’s Digi-Modem must use Contact ID alarm format. In the event the 
control panel needs to send a signal to the ARC, DigiCom will capture the message and forward it via MQTT to the Home 
Assistant. The Digi-Modem must have an ARC telephone number and account number programmed for DigiCom to work. Check 
your control panel configuration for any other settings that may apply.

# Receiving a message using Conexant modem AT commands

## Ademco Contact ID

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

## Ademco Fast Format (not implemented)

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
