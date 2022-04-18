import unittest
from contextlib import redirect_stdout
from io import StringIO
from string import Template

from pylims import config
from pylims import shell
from pylims.dba import DataSet


class ShellTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dataset = DataSet(config.test_database)

    def setUp(self):
        self.dataset._reset_tables()

    def test_help(self):
        with redirect_stdout(StringIO()) as fp:
            args = []
            app = shell.Shell()
            code = app.main(args)

        """
        Labware & Containers LIMS
        Usage: python3 lims.py <command> [args...]
        
        where commands and their arguments are:
        
        record_receipt <customer_sample_name> <tube_barcode>
            Records customer sample and prints the assigned sample_id.
            customer_sample_name format is <customer_name>-<sample_name>. 
            Example: record_receipt customer1-sample1 NT00001
        
        add_to_tube <sample_id> <tube_barcode>
            Records addition of a sample to a tube.
            Example: add_to_tube 12345 NT00002
        
        add_to_plate <sample_id> <plate_barcode> <well_position>
            Records addition of a sample to a plate.
            Example: add_to_plate 12345 DN00001 A1
        
        tube_transfer <source_tube_barcode> <destination_tube_barcode>
            Records transferring a sample to another tube.
            Example: tube_transfer NT00001 NT00003
        
        list_samples_in <container_barcode>
            Reports information about samples in tubes or plates.
            Example: list_samples_in DN00004
        
        tag <sample_id> <tag>
            Appends a tag to a sample. 
            Example: tag 12345 ATTGGCAT

        """

        self.assertEqual(code, app.EXIT_SUCCESS)

        actual = fp.getvalue().strip()
        expected = shell.HELP.strip()
        self.assertMultiLineEqual(expected, actual)

    def test_unknown_command(self):
        with redirect_stdout(StringIO()) as fp:
            args = ['unknown_command']
            app = shell.Shell()
            code = app.main(args)

        """
        Unknown command: unknown_command
        Run the application without arguments for help.
        """

        self.assertEqual(code, app.EXIT_FAILURE)
        actual = fp.getvalue().strip()
        expected = (shell.UNKNOWN_COMMAND_TEMP % args[0]).strip()
        self.assertMultiLineEqual(expected, actual)

    def test_number_of_parameters(self):
        with redirect_stdout(StringIO()) as fp:
            args = ['record_receipt', 'one']
            app = shell.Shell()
            code = app.main(args)
        """
        Incorrect number of arguments for command: record_receipt
        """
        self.assertEqual(code, app.EXIT_FAILURE)

        actual = fp.getvalue().strip()
        expected = (shell.INCORRECT_NUMBER_OF_PARAMS_TEMP % args[0]).strip()
        self.assertMultiLineEqual(expected, actual)

    def test_init_without_process(self):
        with redirect_stdout(StringIO()) as fp:
            app = shell.Shell()  # without Process
            args = 'list_samples_in XX'.split()  # It will fail but it is OK.
            code = app.main(args)  # it creates a Process for Methods.
        actual = fp.getvalue().strip()
        expected = self._render(
            shell.INVALID_BARCODE_PREFIX_TEMP, dict(prefix='XX'))

        self.assertEqual(code, app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def _render(self, temp, data):
        return Template(temp).safe_substitute(data).strip()
