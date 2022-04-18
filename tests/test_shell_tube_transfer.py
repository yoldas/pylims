import unittest
from contextlib import redirect_stdout, redirect_stderr
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

    def test_invalid_source_tube_barcode(self):
        with redirect_stdout(StringIO()) as fp:
            source_tube_barcode = 'NT0'  # bad barcode
            destination_tube_barcode = 'NT00002'
            cmd = 'tube_transfer %s %s' % (
                source_tube_barcode, destination_tube_barcode)
            args = cmd.split()
            code = self.app.main(args)
        """
        Invalid source tube barcode: NT0
        Tube barcode must be in NT<number> format where <number> is padded with zeros.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.INVALID_SOURCE_TUBE_BARCODE_TEMP
        data = dict(source_tube_barcode=source_tube_barcode,
                    destination_tube_barcode=destination_tube_barcode)
        expected = self._render(temp, data)
        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_invalid_destination_tube_barcode(self):
        with redirect_stdout(StringIO()) as fp:
            source_tube_barcode = 'NT00001'
            destination_tube_barcode = 'XX00002'  # bad barcode
            cmd = 'tube_transfer %s %s' % (
                source_tube_barcode, destination_tube_barcode)
            args = cmd.split()
            code = self.app.main(args)
        """
        Invalid destination tube barcode: XX00002
        Tube barcode must be in NT<number> format where <number> is padded with zeros.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.INVALID_DESTINATION_TUBE_BARCODE_TEMP
        data = dict(source_tube_barcode=source_tube_barcode,
                    destination_tube_barcode=destination_tube_barcode)
        expected = self._render(temp, data)
        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_source_tube_not_found(self):
        with redirect_stdout(StringIO()) as fp:
            source_tube_barcode = 'NT00001'
            destination_tube_barcode = 'NT00002'
            cmd = 'tube_transfer %s %s' % (
                source_tube_barcode, destination_tube_barcode)
            args = cmd.split()
            code = self.app.main(args)
        """
        Source tube not found: NT00001
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.SOURCE_TUBE_NOT_FOUND_TEMP
        data = dict(source_tube_barcode=source_tube_barcode,
                    destination_tube_barcode=destination_tube_barcode)
        expected = self._render(temp, data)
        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_discarded_source_tube(self):
        source_tube_barcode = 'NT00001'  # original
        other_barcode = 'NT00002'  # first transfer
        destination_tube_barcode = 'NT00003'  # second transfer: attempted

        # Record a sample first
        with redirect_stdout(StringIO()) as fp:
            cmd = 'record_receipt customer1-sample1 %s' % source_tube_barcode
            args = cmd.split()
            code = self.app.main(args)
        # Transfer tube
        with redirect_stdout(StringIO()) as fp:
            cmd = 'tube_transfer %s %s' % (source_tube_barcode, other_barcode)
            args = cmd.split()
            code = self.app.main(args)
        # Now try to transfer from source (empty, discarded) again to another
        with redirect_stdout(StringIO()) as fp:
            cmd = 'tube_transfer %s %s' % (
                source_tube_barcode, destination_tube_barcode)
            args = cmd.split()
            code = self.app.main(args)
        """
        Discarded source tube
        Sample tube: Barcode: NT00001, Sample moved to: NT00002
        The barcode entered for the source tube belongs to a discarded tube. Please check barcode.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.DISCARDED_SOURCE_TUBE_TEMP
        source_tube = SampleTube(source_tube_barcode)
        source_tube.set_moved_to(other_barcode)
        data = dict(source_tube_barcode=source_tube_barcode,
                    destination_tube_barcode=destination_tube_barcode,
                    source_tube=source_tube)
        expected = self._render(temp, data)
        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_discarded_destination_tube(self):
        first = 'NT00001'
        second = 'NT00002'
        # Record a sample first
        with redirect_stdout(StringIO()) as fp:
            cmd = 'record_receipt customer1-sample1 %s' % first
            args = cmd.split()
            code = self.app.main(args)
        # Transfer tube
        with redirect_stdout(StringIO()) as fp:
            cmd = 'tube_transfer %s %s' % (first, second)
            args = cmd.split()
            code = self.app.main(args)
        # Now try to transfer it back. It must be rejected because the original
        # tube was discarded, hence it cannot be a destination anymore.
        with redirect_stdout(StringIO()) as fp:
            cmd = 'tube_transfer %s %s' % (second, first)
            args = cmd.split()
            code = self.app.main(args)
        """
        Discarded destination tube
        Sample tube: Barcode: NT00001, Sample moved to: NT00002
        The barcode entered for the destination tube belongs to a discarded tube. Please check barcode.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.DISCARDED_DESTINATION_TUBE_TEMP
        first_tube = SampleTube(first)
        first_tube.set_moved_to(second)
        data = dict(source_tube_barcode=second,
                    destination_tube_barcode=first,
                    destination_tube=first_tube)
        expected = self._render(temp, data)
        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_destination_tube_not_empty(self):
        first = 'NT00001'
        second = 'NT00002'
        sample_id = 1
        # Record a sample first
        with redirect_stdout(StringIO()) as fp:
            cmd = 'record_receipt customer1-sample1 %s' % first
            args = cmd.split()
            code = self.app.main(args)
        # *Add* sample to second
        with redirect_stdout(StringIO()) as fp:
            cmd = 'add_to_tube %s %s' % (sample_id, second)
            args = cmd.split()
            code = self.app.main(args)
        # Now try to *transfer* from first to second. It must be rejected
        # because the destination is not empty.
        with redirect_stdout(StringIO()) as fp:
            cmd = 'tube_transfer %s %s' % (first, second)
            args = cmd.split()
            code = self.app.main(args)
        """
        Destination tube not empty
        Lab tube: Barcode: NT00002, Sample Id: 1, Customer sample name: customer1-sample1
        The barcode entered for the destination tube belongs to an existing tube (not empty). Please check barcode.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.DESTINATION_TUBE_NOT_EMPTY_TEMP
        sample = Sample('customer1', 'sample1', sample_id)
        second_tube = LabTube(second, sample)
        # response data
        data = dict(source_tube_barcode=second,
                    destination_tube_barcode=second,
                    destination_tube=second_tube)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_unexpected_error(self):
        # First record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)

        def raise_exception(self, *args):
            raise Exception("test exception")

        original = self.dataset.move_sample  # save
        self.dataset.move_sample = raise_exception  # patch
        try:
            # Now try to transfer. We will generate an error during transaction.
            with redirect_stdout(StringIO()) as fp:
                args = 'tube_transfer NT00001 NT00002'.split()
                with self.assertLogs() as ex:
                    code = self.app.main(args)
            """
            Unexpected Error
            An error was logged. Please contact support.
            """
        finally:
            self.dataset.move_sample = original  # restore

        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.UNEXPECTED_ERROR_TEMP
        data = dict()
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)


    def test_moved_sample_successfully(self):
        # First record a sample
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)
        # Now transfer sample to a new tube
        with redirect_stdout(StringIO()) as fp:
            args = 'tube_transfer NT00001 NT00002'.split()
            code = self.app.main(args)
        """
        Moved sample successfully
        Source: Sample tube: Barcode: NT00001, Sample moved to: NT00002
        Destination: Sample tube: Barcode: NT00002, Sample Id: 1, Customer sample name: customer1-sample1
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.MOVED_SAMPLE_TEMP
        sample = Sample('customer1', 'sample1', 1)
        source = SampleTube('NT00001')
        source.set_moved_to('NT00002')
        destination = SampleTube('NT00002', sample)

        data = dict(source_tube=source, destination_tube=destination)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_SUCCESS)
        self.assertMultiLineEqual(expected, actual)

    def _render(self, temp, data):
        return Template(temp).safe_substitute(data).strip()
