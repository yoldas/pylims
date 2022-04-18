import unittest
from io import StringIO

from pylims import config
from pylims.dba import DataSet
from pylims.lab import Sample, SampleTube, LabTube, Plate, Well
from pylims.process import Process, Response


class ProcessTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dataset = DataSet(config.test_database)
        cls.process = Process(cls.dataset)

    def setUp(self):
        self.dataset._reset_tables()

    def test_invalid_tag(self):
        response = self.process.tag(1, 'XXX')
        self.assertEqual(Response.INVALID_TAG, response.get_status())

    def test_sample_already_tagged(self):
        sample = Sample('customer1', 'sample1')
        tube = SampleTube('NT12345', sample)
        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube)  # creates sample and assigns id
        self.dataset.update_sample_tag(sample, 'CAT')
        self.dataset.commit_transaction()

        sample_id = sample.get_sample_id()
        response = self.process.tag(sample_id, 'AACCGGTT')
        self.assertEqual(Response.ALREADY_TAGGED, response.get_status())

    def test_unexpected_error(self):
        sample = Sample('customer1', 'sample1')  # without tag
        tube = SampleTube('NT12345', sample)
        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube)  # creates sample and assigns id
        self.dataset.commit_transaction()
        sample_id = sample.get_sample_id()

        def raise_exception(*args):
            raise Exception("test exception")

        original = self.dataset.update_sample_tag
        self.dataset.update_sample_tag = raise_exception
        try:
            with self.assertLogs() as ex:
                response = self.process.tag(sample_id, 'CAT')
        finally:
            self.dataset.update_sample_tag = original

        self.assertEqual(Response.UNEXPECTED_ERROR, response.get_status())

    def test_tagged_sample(self):
        sample = Sample('customer1', 'sample1')  # without tag
        tube = SampleTube('NT12345', sample)
        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube)  # creates sample and assigns id
        self.dataset.commit_transaction()

        sample_id = sample.get_sample_id()
        response = self.process.tag(sample_id, 'ACGT')
        self.assertEqual(Response.TAGGED_SAMPLE, response.get_status())
