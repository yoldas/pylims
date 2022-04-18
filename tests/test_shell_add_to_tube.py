import unittest
from contextlib import redirect_stdout
from io import StringIO
from string import Template

from pylims import config
from pylims import shell
from pylims.dba import DataSet
from pylims.process import Process
from pylims.lab import Sample, SampleTube, LabTube


class ShellTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dataset = DataSet(config.test_database)  # To reset the database.
        cls.app = shell.Shell(Process(cls.dataset))  # The application instance.

    def setUp(self):
        self.dataset._reset_tables()  # reset test_db tables and sequences.

    def test_discarded_sample_tube(self):
        # Record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)
        # Transfer to another tube
        with redirect_stdout(StringIO()) as fp:
            args = 'tube_transfer NT00001 NT00002'.split()
            code = self.app.main(args)
        # Try to add sample to the barcode of a discarded sample tube
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_tube 1 NT00001'.split()
            code = self.app.main(args)
        """
        Discarded sample tube
        Sample tube: Barcode: NT00001, Sample moved to: NT00002
        The barcode entered belongs to a discarded sample tube. Please check barcode.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.DISCARDED_SAMPLE_TUBE_TEMP
        tube = SampleTube('NT00001')
        tube.set_moved_to('NT00002')
        data = dict(tube=tube)
        expected = self._render(temp, data)
        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_existing_sample_tube(self):
        # Record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)
        # Now try to add to this tube
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_tube 1 NT00001'.split()
            code = self.app.main(args)
        """
        Existing sample tube
        Sample tube: Barcode: NT00001, Sample Id: 1, Customer sample name: customer1-sample1
        The barcode entered belongs to an existing sample tube (not empty). Please check barcode.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.EXISTING_SAMPLE_TUBE_TEMP
        sample = Sample('customer1', 'sample1', 1)
        tube = SampleTube('NT00001', sample)
        data = dict(tube=tube)
        expected = self._render(temp, data)
        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_discarded_lab_tube(self):
        # Record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)
        # Add to a lab tube
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_tube 1 NT00002'.split()
            code = self.app.main(args)
        # Transfer from the lab tube to another lab tube
        with redirect_stdout(StringIO()) as fp:
            args = 'tube_transfer NT00002 NT00003'.split()
            code = self.app.main(args)
        # Now try to add a sample with the tube NT00002 (discarded lab tube)
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_tube 1 NT00002'.split()
            code = self.app.main(args)
        """
        Discarded lab tube
        Lab tube: Barcode: NT00002, Sample moved to: NT00003
        The barcode entered belongs to a discarded lab tube. Please check barcode.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.DISCARDED_LAB_TUBE_TEMP
        tube = LabTube('NT00002')
        tube.set_moved_to('NT00003')
        data = dict(tube=tube)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_existing_lab_tube(self):
        # Record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)
        # Add to a lab tube
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_tube 1 NT00002'.split()
            code = self.app.main(args)
        # Now try to add to NT00002 (not empty, existing)
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_tube 1 NT00002'.split()
            code = self.app.main(args)
        """
        Existing lab tube
        Lab tube: Barcode: NT00002, Sample Id: 1, Customer sample name: customer1-sample1
        The barcode entered belongs to an existing lab tube (not empty). Please check barcode.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.EXISTING_LAB_TUBE_TEMP
        sample = Sample('customer1', 'sample1', 1)
        tube = LabTube('NT00002', sample)
        data = dict(tube=tube)
        expected = self._render(temp, data)
        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_invalid_tube_barcode(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_tube 1 NT0'.split()
            code = self.app.main(args)
        """
        Invalid tube barcode: NT0
        Tube barcode must be in NT<number> format where <number> is padded \
        with zeros.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.INVALID_TUBE_BARCODE_TEMP
        data = dict(barcode=args[2])
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_sample_not_found(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_tube 1 NT12345'.split()
            code = self.app.main(args)
        """
        Sample not found: 1
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.SAMPLE_NOT_FOUND_TEMP
        data = dict(sample_id=args[1], barcode=args[2])
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_unexpected_error(self):
        # Record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)

        def raise_exception(self, *args):
            raise Exception("test exception")

        original = self.dataset.create_lab_tube  # save
        self.dataset.create_lab_tube = raise_exception  # patch
        try:
            with redirect_stdout(StringIO()) as fp:
                args = 'add_to_tube 1 NT00002'.split()
                with self.assertLogs() as ex:
                    code = self.app.main(args)
            """
            Unexpected Error
            An error was logged. Please contact support.
            """
        finally:
            self.dataset.create_lab_tube = original  # restore

        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.UNEXPECTED_ERROR_TEMP
        data = dict()
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_added_sample_successfully(self):
        # First record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            self.app.main(args)
        """
        Recorded sample successfully
        Sample tube: Barcode: NT00001, Sample Id: 1, Customer sample name: customer1-sample1
        """
        # Now add sample to a lab tube: sample_id=1 -> NT00002
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_tube 1 NT00002'.split()
            code = self.app.main(args)
        """
        Added sample successfully
        Lab tube: Barcode: NT00002, Sample Id: 1, Customer sample name: customer1-sample1
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.ADDED_SAMPLE_TEMP
        tube = LabTube('NT00002', Sample('customer1', 'sample1', 1))
        data = dict(sample_id=args[1], barcode=args[2], tube=tube)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_SUCCESS)
        self.assertMultiLineEqual(expected, actual)

    def _render(self, temp, data):
        return Template(temp).safe_substitute(data).strip()
