import unittest
from contextlib import redirect_stdout
from io import StringIO
from string import Template

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

    def test_invalid_tube_barcode(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'list_samples_in NT0'.split()
            code = self.app.main(args)
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        """
        Invalid tube barcode: NT0
        Tube barcode must be in NT<number> format where <number> is padded with zeros.
        """
        temp = shell.INVALID_TUBE_BARCODE_TEMP
        data = dict(barcode=args[1])
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_found_discarded_sample_tube(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'tube_transfer NT00001 NT00002'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'list_samples_in NT00001'.split()
            code = self.app.main(args)
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        """
        Found discarded sample tube
        Sample tube: Barcode: NT00001, Sample moved to: NT00002
        """
        tube = SampleTube('NT00001')
        tube.set_moved_to('NT00002')
        temp = shell.FOUND_DISCARDED_SAMPLE_TUBE_TEMP
        data = dict(barcode=args[1], result=tube)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_SUCCESS)
        self.assertMultiLineEqual(expected, actual)

    def test_found_sample_tube(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'tag 1 CAT'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'list_samples_in NT00001'.split()
            code = self.app.main(args)

        actual = fp.getvalue().strip()
        # print('\n' + actual)
        """
        Found sample tube
        Sample tube: Barcode: NT00001, Sample Id: 1, Customer sample name: customer1-sample1, Tag: CAT
        """
        temp = shell.FOUND_SAMPLE_TUBE_TEMP
        tube = SampleTube('NT00001', Sample('customer1', 'sample1', 1, 'CAT'))
        data = dict(barcode=args[1], result=tube)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_SUCCESS)
        self.assertMultiLineEqual(expected, actual)

    def test_found_discarded_lab_tube(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_tube 1 NT00002'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'tube_transfer NT00002 NT00003'.split()
            code = self.app.main(args)
        # Now NT00002 is empty and discarded lab tube.
        with redirect_stdout(StringIO()) as fp:
            args = 'list_samples_in NT00002'.split()
            code = self.app.main(args)
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        """
        Found discarded lab tube
        Lab tube: Barcode: NT00002, Sample moved to: NT00003
        """
        temp = shell.FOUND_DISCARDED_LAB_TUBE_TEMP
        tube = LabTube('NT00002')
        tube.set_moved_to('NT00003')
        data = dict(barcode=args[1], result=tube)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_SUCCESS)
        self.assertMultiLineEqual(expected, actual)

    def test_found_lab_tube(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_tube 1 NT00002'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'list_samples_in NT00002'.split()
            code = self.app.main(args)
        """
        Found lab tube
        Lab tube: Barcode: NT00002, Sample Id: 1, Customer sample name: customer1-sample1
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.FOUND_LAB_TUBE_TEMP
        tube = LabTube('NT00002', Sample('customer1', 'sample1', 1))
        data = dict(barcode=args[1], result=tube)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_SUCCESS)
        self.assertMultiLineEqual(expected, actual)

    def test_tube_not_found(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'list_samples_in NT00002'.split()
            code = self.app.main(args)
        actual = fp.getvalue().strip()
        """
        Tube not found: NT00002
        """
        # print('\n' + actual)
        temp = shell.TUBE_NOT_FOUND_TEMP
        tube = LabTube('NT00002', Sample('customer1', 'sample1', 2))
        data = dict(barcode=args[1], result=tube)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_invalid_plate_barcode(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'list_samples_in DN0'.split()
            code = self.app.main(args)
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        """
        Invalid plate barcode: NT0
        Tube barcode must be in DN<number> format where <number> is padded with zeros.
        """
        temp = shell.INVALID_PLATE_BARCODE_TEMP
        data = dict(plate_barcode=args[1])
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_found_plate(self):
        # Record sample from first customer
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)

        # Add sample to three wells on the plate DN12345
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DN12345 A1'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DN12345 A2'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 1 DN12345 A3'.split()
            code = self.app.main(args)

        # Tag first customer sample with TAGC
        with redirect_stdout(StringIO()) as fp:
            args = 'tag 1 TAGC'.split()
            code = self.app.main(args)

        # Record sample from second customer with the same sample name part.
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer2-sample1 NT00002'.split()
            code = self.app.main(args)

        # Add sample to two wells on the plate DN12345
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 2 DN12345 B1'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 2 DN12345 B2'.split()
            code = self.app.main(args)

        # Record sample from third customer
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer3-sample3 NT00003'.split()
            code = self.app.main(args)

        # Add sample to a well on the plate DN12345
        with redirect_stdout(StringIO()) as fp:
            args = 'add_to_plate 3 DN12345 H12'.split()
            code = self.app.main(args)

        # Tag third customer sample with CAT
        with redirect_stdout(StringIO()) as fp:
            args = 'tag 3 CAT'.split()
            code = self.app.main(args)

        # List samples in plate DN12345
        with redirect_stdout(StringIO()) as fp:
            args = 'list_samples_in DN12345'.split()
            code = self.app.main(args)
        """
        Found plate
        Plate: Barcode: DN12345, Grid: 8x12
        Well: Label: A1, Sample Id: 1, Customer sample name: customer1-sample1, Tag: TAGC
        Well: Label: A2, Sample Id: 1, Customer sample name: customer1-sample1, Tag: TAGC
        Well: Label: A3, Sample Id: 1, Customer sample name: customer1-sample1, Tag: TAGC
        Well: Label: B1, Sample Id: 2, Customer sample name: customer2-sample1
        Well: Label: B2, Sample Id: 2, Customer sample name: customer2-sample1
        Well: Label: H12, Sample Id: 3, Customer sample name: customer3-sample3, Tag: CAT
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)

        sample1 = Sample('customer1', 'sample1', 1, 'TAGC')
        sample2 = Sample('customer2', 'sample1', 2)
        sample3 = Sample('customer3', 'sample3', 3, 'CAT')
        wells = [Well('A1', sample1), Well('A2', sample1), Well('A3', sample1),
                 Well('B1', sample2), Well('B2', sample2),
                 Well('H12', sample3)]
        plate = Plate('DN12345', '8x12', wells)

        temp = shell.FOUND_PLATE_TEMP
        data = dict(plate_barcode=args[1], result=plate, grid='8x12')
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_SUCCESS)
        self.assertMultiLineEqual(expected, actual)

    def test_invalid_barcode_prefix(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'list_samples_in XX'.split()
            code = self.app.main(args)
        """
        Invalid barcode prefix XX
        Barcode prefixes are NT for tubes and DN for plates.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.INVALID_BARCODE_PREFIX_TEMP
        data = dict(prefix='XX')
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def _render(self, temp, data):
        return Template(temp).safe_substitute(data).strip()
