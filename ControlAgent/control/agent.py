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

# Enable information and debug logging
utils.setup_logging()
_log = logging.getLogger(__name__)
# --------------------------------------- ASSUME THESE ARE NEEDED --------------------------------------- #


# Create a class with the convention: NameAgent
# and always include "PublishMixin, BaseAgent" as its arguments.
class ControlAgent(PublishMixin, BaseAgent):
    """ Listens for commands from user input agent, in message stream userinput/state. """

    # --------------------------------------- ASSUME THIS IS NEEDED --------------------------------------- #
    def __init__(self, config_path, **kwargs):
        super(ControlAgent, self).__init__(**kwargs)
        self.config = utils.load_config(config_path)
        # Initialize flags to be false.
        self.dehumidifierOn = False
        self.fanOn = False

    def setup(self):
        # Demonstrate accessing a value from the config file
        _log.info(self.config['message'])
        self._agent_id = self.config['agentid']
        super(ControlAgent, self).setup()
    # --------------------------------------- ASSUME THIS IS NEEDED --------------------------------------- #

    def run_dehum(self):
        """Turn on dehumidifier"""
        # Set flag, so know dehumidifier is on, and log transition
        self.dehumidifierOn = True
        _log.info("SUCCESS - The dehumidifier (compressor and fan) is now on.")

    def shed_dehum(self):
        """Turn off dehumidifier"""
        # Set flag, so know dehumidifier is off, and log transition
        self.dehumidifierOn = False
        _log.info("SUCCESS - The dehumidifier (compressor and fan) is now off.")

    def run_fan(self):
        """Turn on fan"""
        # Set flag, so know fan is on, and log transition
        self.fanOn = True
        _log.info("SUCCESS - The fan is now on.")

    def shed_fan(self):
        """Turn off fan"""
        # Set flag, so know fan is off, and log transition
        self.fanOn = False
        _log.info("SUCCESS - The fan is now off.")

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
    utils.default_main(ControlAgent,
                   description='Control dehumidifier',
                   argv=argv)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
# --------------------------------------- ALWAYS INCLUDE --------------------------------------- #