# Written by: Kathleen Gegner
# Adapted from: VOLTTRON platform agents


# ---------------------------------------------- OVERVIEW ---------------------------------------------- #
# This agent checks for a message in the message bus with the topic/subtopic name 'userinput/state'      #
# Only messages under that topic name are read.                                                          #
# The received message is assigned to a variable called command.                                         #
# The command is then processed and the necessary action is performed.                                   #
# Possible actions include turning on or off a green or red LED, using BeagleBone GPIO pins.             #
# ------------------------------------------------------------------------------------------------------ #


# --------------------------------------- ASSUME THESE ARE NEEDED --------------------------------------- #
# more import statements may be needed for other agents, but these work for this agent
import logging
import sys

from zmq.utils import jsonapi
from volttron.platform.agent import BaseAgent, PublishMixin
from volttron.platform.agent import utils, matching
#from volttron.platform.messaging import headers as headers_mod

from bbio import *     # For BeagleBone

# Enable information and debug logging
utils.setup_logging()
_log = logging.getLogger(__name__)
# --------------------------------------- ASSUME THESE ARE NEEDED --------------------------------------- #


# Create a class with the convention: NameAgent
# and always include "PublishMixin, BaseAgent" as its arguments.
class LEDAgent(PublishMixin, BaseAgent):
    """ Listens for commands from user input agent, in message stream userinput/state. """

    # --------------------------------------- ASSUME THIS IS NEEDED --------------------------------------- #
    def __init__(self, config_path, **kwargs):
        super(LEDAgent, self).__init__(**kwargs)
        self.config = utils.load_config(config_path)
        # Assign address of GPIO to variable
        self.portGreenLED_Write = GPIO1_28      # P9.12 on BeagleBone
        self.portRedLED_Write = GPIO1_18        # P9.14 on BeagleBone
        self.portGreenLED_Read = GPIO1_16       # P9.15 on BeagleBone
        self.portRedLED_Read = GPIO1_19         # P9.16 on BeagleBone
        # Initialize GPIO pins to be either output or input
        pinMode(self.portGreenLED_Write, OUTPUT)     # P9.12 on BeagleBone is output
        pinMode(self.portRedLED_Write, OUTPUT)       # P9.14 on BeagleBone is output
        pinMode(self.portGreenLED_Read, INPUT)       # P9.15 on BeagleBone is input
        pinMode(self.portRedLED_Read, INPUT)         # P9.16 on BeagleBone is input
        # Initialize GPIO output pins to be off (low)
        digitalWrite(self.portGreenLED_Write, LOW)
        digitalWrite(self.portRedLED_Write, LOW)
        # Initialize flags to be false.
        self.GreenOn = False
        self.RedOn = False

    def setup(self):
        # Demonstrate accessing a value from the config file
        _log.info(self.config['message'])
        self._agent_id = self.config['agentid']
        super(LEDAgent, self).setup()
    # --------------------------------------- ASSUME THIS IS NEEDED --------------------------------------- #

    def green_on(self):
        """Set P9.12 high"""
        digitalWrite(self.portGreenLED_Write, HIGH)     # For BeagleBone
        # Check that the command has been correctly implemented.
        if self.check_output('green LED', HIGH) is True:
            # Set flag, so know green LED is on, and log transition
            self.GreenOn = True
            _log.info("SUCCESS - The green LED is now on.")

    def green_off(self):
        """Set P9.12 low"""
        digitalWrite(self.portGreenLED_Write, LOW)      # For BeagleBone
        # Check that the command has been correctly implemented.
        if self.check_output('green LED', LOW) is True:
            # Set flag, so know green LED is off, and log transition
            self.GreenOn = False
            _log.info("SUCCESS - The green LED is now off.")

    def red_on(self):
        """Set P9.14 high"""
        digitalWrite(self.portRedLED_Write, HIGH)       # For BeagleBone
        # Check that the command has been correctly implemented.
        if self.check_output('red LED', HIGH) is True:
            # Set flag, so know red LED is on, and log transition
            self.RedOn = True
            _log.info("SUCCESS - The red LED is now on.")

    def red_off(self):
        """Set P9.14 low"""
        digitalWrite(self.portRedLED_Write, LOW)        # For BeagleBone
        # Check that the command has been correctly implemented.
        if self.check_output('red LED', LOW) is True:
            # Set flag, so know red LED is off, and log transition
            self.RedOn = False
            _log.info("SUCCESS - The red LED is now off.")

    def check_output(self, component, expected_status):
        """ Input pins connected to output pins. Check if output voltage matches what is expected. """
        if component == 'green LED':
            # Read input pins
            pin_status = digitalRead(self.portGreenLED_Read)
            if pin_status == HIGH:
                mode = 'ON'
            else:
                mode = 'OFF'
            # Log the input pin status
            _log.info("Pin status: {}".format(pin_status))
            # Check if the expected_status equals what the input pins measured (pin_status)
            if expected_status == pin_status:
                # Statuses are equal, publish message with component type, mode, and success text
                self.publish_json('LEDcontrol/status', {}, ('SUCCESS', component, mode))
                return True
            else:
                # Statuses are not equal, publish message with component type, mode, and failed text
                self.publish_json('LEDcontrol/status', {}, ('FAILED', component, mode))
                return False
        elif component == 'red LED':
            pin_status = digitalRead(self.portRedLED_Read)
            if pin_status == HIGH:
                mode = 'ON'
            else:
                mode = 'OFF'
            _log.info("Pin status: {}".format(pin_status))
            if expected_status == pin_status:
                # Statuses are equal, publish message with component type, mode, and success text
                self.publish_json('LEDcontrol/status', {}, ('SUCCESS', component, mode))
                return True
            else:
                # Statuses are not equal, publish message with component type, mode, and failed text
                self.publish_json('LEDcontrol/status', {}, ('FAILED', component, mode))
                return False

    def get_output_status(self):
        """ Log the output status of each GPIO pin. """
        pin_status_green = digitalRead(self.portGreenLED_Read)
        if pin_status_green == HIGH:
            mode = 'ON'
        else:
            mode = 'OFF'
        # Log the input pin status
        _log.info("Green LED : {}".format(mode))

        pin_status_red = digitalRead(self.portRedLED_Read)
        if pin_status_red == HIGH:
            mode = 'ON'
        else:
            mode = 'OFF'
        # Log the input pin status
        _log.info("Red LED   : {}".format(mode))

    # If a message with the subscription name "userinput/state" is in the message bus,
    # execute the text below.
    # The matching.match_start function looks for messages starting with the specified argument.
    # The argument for matching.match_start is ("topic/subtopic").
    # NOTE: For more matching functions see /volttron/volttron/platform/agent/matching.py
    #       MAKE SURE YOU DO NOT EDIT THAT TEXT FILE THOUGH!!!!!
    @matching.match_start("userinput/state")
    def control_led(self, topic, headers, message, match):
        # message published as... self.publish_json('userinput/state', {}, (prev_state, state))
        # message has format [prev_state, state]
        command = jsonapi.loads(message[0])
        command = command[1]
        _log.info("Received the command {}.".format(command))

        # Now, process the command that was sent.
        if command == 'kill':
            self.green_off()
            self.red_off()
        if command == 'status':
            self.get_output_status()
        if self.GreenOn is True:
            # The green LED is currently on.
            if command == 'green off':
                # Turn off the green LED.
                self.green_off()
            else:
                # The green LED is already on, so 'green on' does nothing.
                pass
        if self.GreenOn is False:
            # The green LED is currently off.
            if command == "green on":
                # Turn on the green LED.
                self.green_on()
            else:
                # The green LED is already off, so don't need to do anything.
                pass
        if self.RedOn is True:
            # The red LED is currently on.
            if command == "red off":
                # Turn off the red LED.
                self.red_off()
            else:
                # The red LED is already on, so 'red on' does nothing.
                pass
        if self.RedOn is False:
            # The red LED is currently off.
            if command == "red on":
                # Turn on the red LED.
                self.red_on()
            else:
                # The red LED are already off, so don't need to do anything.
                pass


# --------------------------------------- ALWAYS INCLUDE --------------------------------------- #
# Include this section in every agent, but adjust the agent name and description.
def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    utils.default_main(LEDAgent,
                   description='Control green and red LEDs',
                   argv=argv)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
# --------------------------------------- ALWAYS INCLUDE --------------------------------------- #