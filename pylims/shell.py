"""User Interface."""
import logging
import logging.config

from string import Template

from . import config
from .process import Process
from .lab import Sample

LOG = logging.getLogger(__name__)

# Help texts.

RECORD_RECEIPT_HELP = """record_receipt <customer_sample_name> <tube_barcode>
    Records customer sample and prints the assigned sample_id.
    customer_sample_name format is <customer_name>-<sample_name>. 
    Example: record_receipt customer1-sample1 NT00001
"""
ADD_TO_TUBE_HELP = """add_to_tube <sample_id> <tube_barcode>
    Records addition of a sample to a tube.
    Example: add_to_tube 12345 NT00002
"""
ADD_TO_PLATE_HELP = """add_to_plate <sample_id> <plate_barcode> <well_position>
    Records addition of a sample to a plate.
    Example: add_to_plate 12345 DN00001 A1
"""
TUBE_TRANSFER_HELP = """\
tube_transfer <source_tube_barcode> <destination_tube_barcode>
    Records transferring a sample to another tube.
    Example: tube_transfer NT00001 NT00003
"""
LIST_SAMPLES_IN_HELP = """list_samples_in <container_barcode>
    Reports information about samples in tubes or plates.
    Example: list_samples_in DN00004
"""
TAG_HELP = """tag <sample_id> <tag>
    Appends a tag to a sample. 
    Example: tag 12345 ATTGGCAT
"""

HELP = """Labware & Containers LIMS
Usage: python3 lims.py <command> [args...]

where commands and their arguments are:

%(RECORD_RECEIPT_HELP)s
%(ADD_TO_TUBE_HELP)s
%(ADD_TO_PLATE_HELP)s
%(TUBE_TRANSFER_HELP)s
%(LIST_SAMPLES_IN_HELP)s
%(TAG_HELP)s""" % globals()

# Output templates

# Template variable names must be uppercase and they must match the response
# status name with a _TEMP suffix, except basic templates.

# basic templates

UNKNOWN_COMMAND_TEMP = """Unknown command: %s
Run the application without arguments for help.
"""
INCORRECT_NUMBER_OF_PARAMS_TEMP = """\
Incorrect number of arguments for command: %s
"""

# response templates

INVALID_CUSTOMER_SAMPLE_NAME_TEMP = """\
Invalid customer sample name: ${customer_sample_name}
The name must be in <customer>${name_delimiter}<sample_name> format.
"""
INVALID_TUBE_BARCODE_TEMP = """Invalid tube barcode: ${barcode}
Tube barcode must be in NT<number> format where <number> is padded with zeros.
"""
EXISTING_CUSTOMER_SAMPLE_NAME_TEMP = """Existing customer sample name
${sample}
Please choose a different customer sample name.
"""
DISCARDED_SAMPLE_TUBE_TEMP = """Discarded sample tube
${tube}
The barcode entered belongs to a discarded sample tube. Please check barcode.
"""
EXISTING_SAMPLE_TUBE_TEMP = """Existing sample tube
${tube}
The barcode entered belongs to an existing sample tube (not empty). \
Please check barcode.
"""
DISCARDED_LAB_TUBE_TEMP = """Discarded lab tube
${tube}
The barcode entered belongs to a discarded lab tube. Please check barcode.
"""
EXISTING_LAB_TUBE_TEMP = """Existing lab tube
${tube}
The barcode entered belongs to an existing lab tube (not empty). \
Please check barcode.
"""
UNEXPECTED_ERROR_TEMP = """Unexpected Error
An error was logged. Please contact support.
"""
RECORDED_SAMPLE_TEMP = """Recorded sample successfully
${tube}
"""
SAMPLE_NOT_FOUND_TEMP = """Sample not found: ${sample_id}
"""
ADDED_SAMPLE_TEMP = """Added sample successfully
${tube}
"""
INVALID_SOURCE_TUBE_BARCODE_TEMP = """\
Invalid source tube barcode: ${source_tube_barcode}
Tube barcode must be in NT<number> format where <number> is padded with zeros.
"""
INVALID_DESTINATION_TUBE_BARCODE_TEMP = """\
Invalid destination tube barcode: ${destination_tube_barcode}
Tube barcode must be in NT<number> format where <number> is padded with zeros.
"""
SOURCE_TUBE_NOT_FOUND_TEMP = """\
Source tube not found: ${source_tube_barcode}
"""
DISCARDED_SOURCE_TUBE_TEMP = """Discarded source tube
${source_tube}
The barcode entered for the source tube belongs to a discarded tube. \
Please check barcode.
"""
DISCARDED_DESTINATION_TUBE_TEMP = """Discarded destination tube
${destination_tube}
The barcode entered for the destination tube belongs to a discarded tube. \
Please check barcode.
"""
DESTINATION_TUBE_NOT_EMPTY_TEMP = """Destination tube not empty
${destination_tube}
The barcode entered for the destination tube belongs to an existing tube \
(not empty). Please check barcode.
"""
MOVED_SAMPLE_TEMP = """Moved sample successfully
Source: ${source_tube}
Destination: ${destination_tube}
"""
INVALID_PLATE_BARCODE_TEMP = """Invalid plate barcode: ${plate_barcode}
Plate barcode must be in DN<number> format where <number> is padded with zeros.
"""
INVALID_WELL_POSITION_TEMP = """Invalid well position: ${well_position}
Well labels are in <letter><number> format, where <letter> denotes the row and
<number> denotes the column on a plate, for example, A1. Please check label.
"""
WELL_OUT_OF_RANGE_TEMP = """Plate well out of range: ${well_position}
Plate: Barcode: ${plate_barcode}, Grid: ${plate_grid}
Please check well position.
"""
WELL_NOT_EMPTY_TEMP = """Well not empty: ${well_position}
Plate: Barcode: ${plate_barcode}, Grid: ${plate_grid}
Please check well position.
"""
ADDED_SAMPLE_TO_PLATE_TEMP = """Added sample to plate successfully
Plate: Barcode: ${plate_barcode}
${well}
"""
PLATE_IS_FULL_TEMP = """Plate is full
Plate: Barcode: ${plate_barcode}, Grid: ${plate_grid}
"""
INVALID_TAG_TEMP = """Invalid tag: ${tag}
Tag can contain only the letters A, G, C and T. Please check sequence.
"""
ALREADY_TAGGED_TEMP = """Sample already tagged
${sample}
"""
TAGGED_SAMPLE_TEMP = """Tagged sample successfully
${sample}
"""
UPDATED_SAMPLE_CONCENTRATION_TEMP = """Updated sample concentration successfully
${sample}
"""
INVALID_SAMPLE_CONCENTRATION_TEMP = """Invalid concentration value: {value}
The value must be between 50 and 200 inclusive.
"""

FOUND_DISCARDED_SAMPLE_TUBE_TEMP = """Found discarded sample tube
${result}
"""
FOUND_SAMPLE_TUBE_TEMP = """Found sample tube
${result}
"""
FOUND_DISCARDED_LAB_TUBE_TEMP = """Found discarded lab tube
${result}
"""
FOUND_LAB_TUBE_TEMP = """Found lab tube
${result}
"""
TUBE_NOT_FOUND_TEMP = """Tube not found: ${barcode}
"""
FOUND_PLATE_TEMP = """Found plate
${result}
"""
PLATE_NOT_FOUND_TEMP = """Plate not found
"""
INVALID_BARCODE_PREFIX_TEMP = """Invalid barcode prefix ${prefix}
Barcode prefixes are NT for tubes and DN for plates.
"""


class Shell:
    """Provides command line user interface. Receives user input and sends
    them to Process, receives Process Responses and renders output using
    templates."""

    EXIT_SUCCESS = 0  # exit code for OS.
    EXIT_FAILURE = 1

    def __init__(self, process=None, logfile=None):
        """Initialises Shell using the given Process. A default Process will
        be created later if not given."""
        self._process = process
        self._logfile = logfile

    # Available commands and their parameters.
    command_parameters = {
        'record_receipt': ('customer_sample_name', 'tube_barcode'),
        'add_to_tube': ('sample_id', 'tube_barcode'),
        'add_to_plate': ('sample_id', 'plate_barcode', 'well_position'),
        'tube_transfer': ('source_tube_barcode', 'destination_tube_barcode'),
        'list_samples_in': ('container_barcode',),
        'tag': ('sample_id', 'tag'),
        'update_concentration': ('sample_id', 'concentration')
    }

    def start_process(self):
        """Creates a process instance if it is not available."""
        if self._process is None:
            self._process = Process()

    def start_logging(self):
        """Configures file logging to capture unexpected errors."""
        if self._logfile is None:
            self._logfile = config.logfile
        format = "%(asctime)s %(levelname)s %(name)s:%(lineno)s %(message)s"
        logging.basicConfig(filename=self._logfile, format=format)

    def main(self, args):
        """Receives command arguments and passes them to Process, and
        renders output using templates and Responses from Process."""
        if not args:
            print(HELP)
            return self.EXIT_SUCCESS

        # Check command.
        command = args[0]
        if command not in self.command_parameters:
            print(UNKNOWN_COMMAND_TEMP % command)
            return self.EXIT_FAILURE

        # Check number of parameters for command.
        params = args[1:]
        if len(params) != len(self.command_parameters[command]):
            print(INCORRECT_NUMBER_OF_PARAMS_TEMP % command)
            return self.EXIT_FAILURE

        # Create a Process instance if we don't have one.
        self.start_process()

        # Configure logging
        self.start_logging()

        # Render outputs using templates and process responses.
        method = getattr(self._process, command)
        response = method(*params)
        status = response.get_status()
        template = self._find_template(status)
        data = response.get_data()
        print(Template(template).safe_substitute(data))
        return self._find_exit(status)

    def _find_template(self, status):
        """Returns template text corresponding to status."""
        return globals()[status.upper().replace(' ', '_') + '_TEMP']

    def _find_exit(self, status):
        """Returns exit code for OS by checking the start of status."""
        magic = status.upper().startswith
        if (magic('FOUND') or magic('RECORDED') or magic('ADDED') or
                magic('MOVED') or magic('TAGGED') or magic('UPDATED')):
            return self.EXIT_SUCCESS
        else:
            return self.EXIT_FAILURE
