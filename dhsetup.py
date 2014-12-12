# Configures GPIO pins automatically at startup
#   - Enable GPIO P9.12 and P9.14 to be outputs and set low
#   - Enable GPIO P9.15 and P9.16 to be inputs

from bbio import *

# Assign GPIO address to variable
portDehumWrite = GPIO1_28      # P9.12 on BeagleBone
portFanWrite = GPIO1_18        # P9.14 on BeagleBone
portDehumRead = GPIO1_16       # P9.15 on BeagleBone
portFanRead = GPIO1_19         # P9.16 on BeagleBone

# Initialize GPIO pins to be either output or input
pinMode(portDehumWrite, OUTPUT)     # P9.12 on BeagleBone is output
pinMode(portFanWrite, OUTPUT)       # P9.14 on BeagleBone is output
pinMode(portDehumRead, INPUT)       # P9.15 on BeagleBone is input
pinMode(portFanRead, INPUT)         # P9.16 on BeagleBone is input

# Initialize output GPIO pins to be off (low)
digitalWrite(portDehumWrite, LOW)
digitalWrite(portFanWrite, LOW)