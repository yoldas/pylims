import unittest
from contextlib import redirect_stdout
from io import StringIO
from string import Template, ascii_uppercase

from pylims import config
from pylims import shell
from pylims.dba import DataSet
from pylims.process import Process
from pylims.lab import Sample, SampleTube, LabTube, Plate, Well


class ShellTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dataset = DataSet(config.test_database)  # To reset the database.
        cls.app = shell.Shell(Process(cls.dataset))  # The application instance.

    def setUp(self):
        self.dataset._reset_tables()  # reset test_db tables and sequences.

    def test_invalid_plate_barcode(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DNX A1'.split()
            code = self.app.main(args)
        """
        Invalid plate barcode DNX
        Plate barcode must be in DN<number> format where <number> is padded with zeros.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.INVALID_PLATE_BARCODE_TEMP
        data = dict(plate_barcode='DNX')
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_invalid_well_position(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DN12345 AX'.split()
            code = self.app.main(args)
        """
        Invalid well position: AX
        Well labels are in <letter><number> format, where <letter> denotes the row and
        <number> denotes the column on a plate, for example, A1. Please check label.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.INVALID_WELL_POSITION_TEMP
        data = dict(well_position='AX')
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_sample_not_found(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DN12345 A1'.split()
            code = self.app.main(args)
        """
        Sample not found: 1
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.SAMPLE_NOT_FOUND_TEMP
        data = dict(sample_id=args[1])
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_existing_plate_well_out_of_range(self):
        # First record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            self.app.main(args)
        # Add another sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer2-sample2 NT00002'.split()
            self.app.main(args)
        # Add sample to plate
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DN12345 A1'.split()
            code = self.app.main(args)
        # Add sample to plate
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 2 DN12345 A13'.split()
            code = self.app.main(args)
        """
        Plate well out of range: A13
        Plate: Barcode: DN12345, Grid: 8x12
        Please check well position.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.WELL_OUT_OF_RANGE_TEMP
        data = dict(plate_barcode='DN12345', plate_grid='8x12',
                    well_position='A13')
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_existing_plate_well_not_empty(self):
        # First record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            self.app.main(args)
        # Add sample to plate well
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DN12345 A1'.split()
            code = self.app.main(args)
        # Try adding sample to the same plate well
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DN12345 A1'.split()
            code = self.app.main(args)
        """
        Well not empty: A1
        Plate: Barcode: DN12345, Grid: 8x12
        Please check well position.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.WELL_NOT_EMPTY_TEMP
        data = dict(plate_barcode='DN12345', plate_grid='8x12',
                    well_position='A1')
        expected = self._render(temp, data)
        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_existing_plate_unexpected_error(self):
        # First record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            self.app.main(args)
        # Add sample to plate
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DN12345 A1'.split()
            code = self.app.main(args)

        # The plate is registered now.

        def raise_exception(self, *args):
            raise Exception("test exception")

        original = self.dataset.create_well  # save
        self.dataset.create_well = raise_exception  # patch
        try:
            # Add more sample to plate well
            with redirect_stdout(StringIO()) as fp:
                args = 'add_to_plate 1 DN12345 A2'.split()
                with self.assertLogs() as ex:
                    code = self.app.main(args)
        finally:
            self.dataset.create_well = original  # restore

        """
        Unexpected error
        An error was logged. Please contact support.
        """

        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.UNEXPECTED_ERROR_TEMP
        data = dict(plate_barcode='DN12345', plate_grid='8x12',
                    well_position='A2')
        expected = self._render(temp, data)
        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_existing_plate_added_another_sample(self):
        # Record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            self.app.main(args)
        # Add sample1 to plate
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DN12345 A1'.split()
            code = self.app.main(args)
        # Record another sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer2-sample2 NT00002'.split()
            self.app.main(args)
        # Add sample2 to plate
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 2 DN12345 A2'.split()
            code = self.app.main(args)
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        """
        Added sample to plate successfully
        Plate: Barcode: DN12345
        Well: Label: A2, Sample Id: 2, Customer sample name: customer2-sample2
        """
        temp = shell.ADDED_SAMPLE_TO_PLATE_TEMP
        sample = Sample('customer2', 'sample2', 2)
        well = Well('A2', sample)
        data = dict(plate_barcode='DN12345', well=well)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_SUCCESS)
        self.assertMultiLineEqual(expected, actual)

    def test_new_plate_well_out_of_range(self):
        # First record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            self.app.main(args)
        # Add sample to plate
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DN12345 A13'.split()
            code = self.app.main(args)
        """
        Plate well out of range: A13
        Plate: Barcode: DN12345, Grid: 8x12
        Please check well position.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.WELL_OUT_OF_RANGE_TEMP
        data = dict(plate_barcode='DN12345', plate_grid='8x12',
                    well_position='A13')
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_new_plate_unexpected_error(self):
        # First record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            self.app.main(args)

        def raise_exception(self, *args):
            raise Exception("test exception")

        original = self.dataset.create_plate  # save
        self.dataset.create_plate = raise_exception  # patch
        try:
            # Add more sample to plate well
            with redirect_stdout(StringIO()) as fp:
                args = 'add_to_plate 1 DN12345 A2'.split()
                with self.assertLogs() as ex:
                    code = self.app.main(args)
        finally:
            self.dataset.create_plate = original  # restore

        """
        Unexpected error
        An error was logged. Please contact support.
        """

        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.UNEXPECTED_ERROR_TEMP
        data = dict(plate_barcode='DN12345', plate_grid='8x12',
                    well_position='A2')
        expected = self._render(temp, data)
        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_new_plate_added_sample_successfully(self):
        # First record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            self.app.main(args)
        # Add sample to plate
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DN12345 A1'.split()
            code = self.app.main(args)
        """
        Added sample to plate successfully
        Plate: Barcode: DN12345
        Well: Label: A1, Sample Id: 1, Customer sample name: customer1-sample1
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.ADDED_SAMPLE_TO_PLATE_TEMP
        sample = Sample('customer1', 'sample1', 1)
        well = Well('A1', sample)
        data = dict(plate_barcode='DN12345', well=well)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_SUCCESS)
        self.assertMultiLineEqual(expected, actual)

    def test_plate_is_full(self):
        # Record sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            self.app.main(args)
        # Add to plate until full (assume default grid: 8x12)
        for row in ascii_uppercase[:8]:
            for column in range(1, 13):
                label = '%s%s' % (row, column)
                with redirect_stdout(StringIO()) as fp:
                    cmd = 'add_to_plate 1 DN12345 %s' % label
                    args = cmd.split()
                    self.app.main(args)
        # Now try adding one more.
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DN12345 A1'.split()
            code = self.app.main(args)
        """
        Plate is full
        Plate: Barcode: DN12345, Grid: 8x12
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)

        temp = shell.PLATE_IS_FULL_TEMP
        data = dict(plate_barcode='DN12345', plate_grid='8x12')
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def _render(self, temp, data):
        return Template(temp).safe_substitute(data).strip()
