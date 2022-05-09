import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from string import Template

from pylims import config
from pylims import shell
from pylims.dba import DataSet
from pylims.process import Process
from pylims.lab import Sample, SampleTube


class ShellTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dataset = DataSet(config.test_database)  # To reset the database.
        cls.app = shell.Shell(Process(cls.dataset))  # The application instance.

    def setUp(self):
        self.dataset._reset_tables()  # reset test_db tables and sequences.

    def test_update_sample_concentration(self):
        # User registers a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)

        # User updates concentration
        with redirect_stdout(StringIO()) as fp:
            args = 'update_concentration 1 50'.split()
            code = self.app.main(args)

        actual = fp.getvalue().strip()
        # print(actual)

        temp = shell.UPDATED_SAMPLE_CONCENTRATION_TEMP
        sample = Sample('customer1', 'sample1', 1, concentration=50)
        data = dict(sample=sample)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_SUCCESS)
        self.assertMultiLineEqual(expected, actual)


    def test_sample_not_found(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'update_concentration 1 100'.split()
            code = self.app.main(args)
        """
        Sample not found: 1
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.SAMPLE_NOT_FOUND_TEMP
        data = dict(value='100', sample_id=1)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    # TODO: Add validation test

    def _render(self, temp, data):
        return Template(temp).safe_substitute(data).strip()