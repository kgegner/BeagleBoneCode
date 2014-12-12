# Written by: Kathleen Gegner
# Adapted from: VOLTTRON platform agents


# ---------------------------------------------- OVERVIEW ---------------------------------------------- #
# This agent checks for a message in the message bus with the topic/subtopic name 'userinput/state'      #
# Only messages under that topic name are read.                                                          #
# The received message is assigned to a variable called command.                                         #
# The command is then processed and the necessary action is performed.                                   #
# Possible actions include turning on or off the dehumidifier or fan, using BBB GPIO pins.               #
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
class DehumAgent(PublishMixin, BaseAgent):
    """ Listens for commands from user input agent, in message stream userinput/state. """

    # --------------------------------------- ASSUME THIS IS NEEDED --------------------------------------- #
    def __init__(self, config_path, **kwargs):
        super(DehumAgent, self).__init__(**kwargs)
        self.config = utils.load_config(config_path)
        # Assign address of GPIO to variable
        self.portDehumWrite = GPIO1_28      # P9.12 on BeagleBone
        self.portFanWrite = GPIO1_18        # P9.14 on BeagleBone
        self.portDehumRead = GPIO1_16       # P9.15 on BeagleBone
        self.portFanRead = GPIO1_19         # P9.16 on BeagleBone
        # Initialize GPIO pins to be either output or input
        pinMode(self.portDehumWrite, OUTPUT)     # P9.12 on BeagleBone is output
        pinMode(self.portFanWrite, OUTPUT)       # P9.14 on BeagleBone is output
        pinMode(self.portDehumRead, INPUT)       # P9.15 on BeagleBone is input
        pinMode(self.portFanRead, INPUT)         # P9.16 on BeagleBone is input
        # Initialize GPIO output pins to be off (low)
        digitalWrite(self.portDehumWrite, LOW)
        digitalWrite(self.portFanWrite, LOW)
        # Initialize flags to be false.
        self.dehumidifierOn = False
        self.fanOn = False

    def setup(self):
        # Demonstrate accessing a value from the config file
        _log.info(self.config['message'])
        self._agent_id = self.config['agentid']
        super(DehumAgent, self).setup()
    # --------------------------------------- ASSUME THIS IS NEEDED --------------------------------------- #

    def run_dehum(self):
        """Set P9.12 high"""
        digitalWrite(self.portDehumWrite, HIGH)     # For BeagleBone
        # Check that the command has been correctly implemented.
        if self.check_output('dehumidifier', HIGH) is True:
            # Set flag, so know dehumidifier is on, and log transition
            self.dehumidifierOn = True
            _log.info("SUCCESS - The dehumidifier (compressor and fan) is now on.")

    def shed_dehum(self):
        """Set P9.12 low"""
        digitalWrite(self.portDehumWrite, LOW)      # For BeagleBone
        # Check that the command has been correctly implemented.
        if self.check_output('dehumidifier', LOW) is True:
            # Set flag, so know dehumidifier is off, and log transition
            self.dehumidifierOn = False
            _log.info("SUCCESS - The dehumidifier (compressor and fan) is now off.")

    def run_fan(self):
        """Set P9.14 high"""
        digitalWrite(self.portFanWrite, HIGH)       # For BeagleBone
        # Check that the command has been correctly implemented.
        if self.check_output('fan', HIGH) is True:
            # Set flag, so know fan is on, and log transition
            self.fanOn = True
            _log.info("SUCCESS - The fan is now on.")

    def shed_fan(self):
        """Set P9.14 low"""
        digitalWrite(self.portFanWrite, LOW)        # For BeagleBone
        # Check that the command has been correctly implemented.
        if self.check_output('fan', LOW) is True:
            # Set flag, so know fan is off, and log transition
            self.fanOn = False
            _log.info("SUCCESS - The fan is now off.")

    def check_output(self, component, expected_status):
        """ Verify that the output from GPIO pins is what is expected based on the user's command.
            Input pins connected to output pins - check if output voltage matches what is expected. """
        if component == 'dehumidifier':
            # Read input pins
            pin_status = digitalRead(self.portDehumRead)
            if pin_status == HIGH:
                mode = 'ON'
            else:
                mode = 'OFF'
            # Log the input pin status
            _log.info("Pin status: {}".format(pin_status))
            # Check if the expected_status equals what the input pins measured (pin_status)
            if expected_status == pin_status:
                # Statuses are equal, publish message with component type, mode, and success text
                self.publish_json('dhcontrol/status', {}, ('SUCCESS', component, mode))
                return True
            else:
                # Statuses are not equal, publish message with component type, mode, and failed text
                self.publish_json('dhcontrol/status', {}, ('FAILED', component, mode))
                return False
        elif component == 'fan':
            pin_status = digitalRead(self.portFanRead)
            if pin_status == HIGH:
                mode = 'ON'
            else:
                mode = 'OFF'
            _log.info("Pin status: {}".format(pin_status))
            if expected_status == pin_status:
                # Statuses are equal, publish message with component type, mode, and success text
                self.publish_json('dhcontrol/status', {}, ('SUCCESS', component, mode))
                return True
            else:
                # Statuses are not equal, publish message with component type, mode, and failed text
                self.publish_json('dhcontrol/status', {}, ('FAILED', component, mode))
                return False

    def get_output_status(self):
        """ Log the output status of each GPIO pin. """
        pin_status_dehum = digitalRead(self.portDehumRead)
        if pin_status_dehum == HIGH:
            mode = 'ON'
        else:
            mode = 'OFF'
        # Log the input pin status
        _log.info("Dehumidifier: {}".format(mode))

        pin_status_fan = digitalRead(self.portFanRead)
        if pin_status_fan == HIGH:
            mode = 'ON'
        else:
            mode = 'OFF'
        # Log the input pin status
        _log.info("         Fan: {}".format(mode))

    # If a message with the subscription name "userinput/state" is in the message bus,
    # execute the text below.
    # The matching.match_start function looks for messages starting with the specified argument.
    # The argument for matching.match_start is ("topic/subtopic").
    # NOTE: For more matching functions see /volttron/volttron/platform/agent/matching.py
    #       MAKE SURE YOU DO NOT EDIT THAT TEXT FILE THOUGH!!!!!
    @matching.match_start("userinput/state")
    def control_dehum(self, topic, headers, message, match):
        """Check message bus for a command sent from the userinput agent"""
        # message published as... self.publish_json('userinput/state', {}, (prev_state, state))
        # message has format [prev_state, state]
        command = jsonapi.loads(message[0])
        command = command[1]
        _log.info("Received the command {}.".format(command))

        # Now, process the command that was sent.
        if command == 'kill':
            self.shed_dehum()
            self.shed_fan()
        elif command == 'status':
            self.get_output_status()

        elif self.dehumidifierOn is True:
            # The dehumidifier (compressor and fan) is currently turned on.
            if command == 'shed dehum':
                # Turn off the dehumidifier.
                self.shed_dehum()
            else:
                # The dehumidifier is already on so 'run dehum' does nothing. Otherwise,
                # 'run fan' or 'shed fan' was issued, but is not allowed when the dehumidifier is on.
                pass
        elif self.fanOn is True:
            # The fan is currently turned on.
            if command == "shed fan":
                # Turn off the fan.
                self.shed_fan()
            else:
                # The fan is already on so 'run fan' does nothing. Otherwise,
                # 'run dehum' or 'shed dehum' was issued, but is not allowed when the fan is on.
                pass
        else:
            # Everything is currently off.
            if command == "run dehum":
                # Turn on the dehumidifier (compressor and fan).
                self.run_dehum()
            elif command == "run fan":
                # Turn on the fan.
                self.run_fan()
            else:
                # The dehumidifier and fan are already off, so don't need to do anything.
                pass


# --------------------------------------- ALWAYS INCLUDE --------------------------------------- #
# Include this section in every agent, but adjust the agent name and description.
def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    utils.default_main(DehumAgent,
                   description='Control dehumidifier',
                   argv=argv)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
# --------------------------------------- ALWAYS INCLUDE --------------------------------------- #