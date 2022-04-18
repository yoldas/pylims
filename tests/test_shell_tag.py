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

    def test_invalid_tag(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'tag 1 XXXX'.split()
            code = self.app.main(args)
        """
        Invalid tag: XXXX
        Tag can contain only the letters A, G, C and T. Please check sequence.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.INVALID_TAG_TEMP
        data = dict(tag='XXXX')
        expected = self._render(temp, data)
        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_sample_not_found(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'tag 1 CAT'.split()
            code = self.app.main(args)
        """
        Sample not found: 1
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.SAMPLE_NOT_FOUND_TEMP
        data = dict(tag='CAT', sample_id=1)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_already_tagged(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'tag 1 CAT'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'tag 1 AAA'.split()
            code = self.app.main(args)
        """
        Sample already tagged
        Sample: Sample Id: 1, Customer sample name: customer1-sample1, Tag: CAT
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.ALREADY_TAGGED_TEMP
        sample = Sample('customer1', 'sample1', 1, 'CAT')
        data = dict(sample=sample)
        expected = self._render(temp, data)

        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)

    def test_unexpected_error(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            self.app.main(args)

        def raise_exception(self, *args):
            raise Exception("test exception")

        original = self.dataset.update_sample_tag  # save
        self.dataset.update_sample_tag = raise_exception  # patch
        try:
            # Add more sample to plate well
            with redirect_stdout(StringIO()) as fp:
                args = 'tag 1 CAT'.split()
                with self.assertLogs() as ex:
                    code = self.app.main(args)
        finally:
            self.dataset.update_sample_tag = original  # restore

        """
        Unexpected error
        An error was logged. Please contact support.
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)
        temp = shell.UNEXPECTED_ERROR_TEMP
        data = dict()
        expected = self._render(temp, data)
        self.assertEqual(code, self.app.EXIT_FAILURE)
        self.assertMultiLineEqual(expected, actual)


    def test_tagged_sample_successfully(self):
        with redirect_stdout(StringIO()) as fp:
            args = 'record_receipt customer1-sample1 NT00001'.split()
            code = self.app.main(args)
        with redirect_stdout(StringIO()) as fp:
            args = 'tag 1 CAT'.split()
            code = self.app.main(args)
        """
        Tagged sample successfully
        Sample: Sample Id: 1, Customer sample name: customer1-sample1, Tag: CAT
        """
        actual = fp.getvalue().strip()
        # print('\n' + actual)

    def _render(self, temp, data):
        return Template(temp).safe_substitute(data).strip()
