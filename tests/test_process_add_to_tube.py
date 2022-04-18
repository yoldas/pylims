import unittest

from contextlib import redirect_stderr
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

    def test_discarded_sample_tube(self):
        sample = Sample('customer1', 'sample1', tag='ACGT')
        tube1 = SampleTube('NT00001', sample)
        tube2 = SampleTube('NT00002')

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube1)
        self.dataset.move_sample(tube1, tube2)
        self.dataset.commit_transaction()

        sample_id = sample.get_sample_id()
        tube_barcode = tube1.get_barcode()
        response = self.process.add_to_tube(sample_id, tube_barcode)
        self.assertEqual(Response.DISCARDED_SAMPLE_TUBE, response.get_status())

    def test_existing_sample_tube(self):
        sample = Sample('customer1', 'sample1', tag='ACGT')
        tube1 = SampleTube('NT00001', sample)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube1)
        self.dataset.commit_transaction()

        sample_id = sample.get_sample_id()
        tube_barcode = tube1.get_barcode()
        response = self.process.add_to_tube(sample_id, tube_barcode)
        self.assertEqual(Response.EXISTING_SAMPLE_TUBE, response.get_status())

    def test_discarded_lab_tube(self):
        sample = Sample('customer1', 'sample1', tag='ACGT')
        tube1 = SampleTube('NT00001', sample)
        tube2 = LabTube('NT00002', sample)
        tube3 = LabTube('NT00003')

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube1)  # record sample
        self.dataset.create_lab_tube(tube2)  # add to lab tube
        self.dataset.move_sample(tube2, tube3)  # tube2 is discarded
        self.dataset.commit_transaction()

        # User is trying to add sample to a discarded lab tube.
        sample_id = sample.get_sample_id()
        tube_barcode = tube2.get_barcode()
        response = self.process.add_to_tube(sample_id, tube_barcode)
        self.assertEqual(Response.DISCARDED_LAB_TUBE, response.get_status())

    def test_existing_lab_tube(self):
        sample = Sample('customer1', 'sample1', tag='ACGT')
        tube1 = SampleTube('NT00001', sample)
        tube2 = LabTube('NT00002', sample)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube1)  # record sample
        self.dataset.create_lab_tube(tube2)  # add to lab tube
        self.dataset.commit_transaction()

        # User is trying to add sample to an existing lab tube.
        sample_id = sample.get_sample_id()
        tube_barcode = tube2.get_barcode()
        response = self.process.add_to_tube(sample_id, tube_barcode)
        self.assertEqual(Response.EXISTING_LAB_TUBE, response.get_status())

    def test_unexpected_error(self):
        sample = Sample('customer1', 'sample1', tag='ACGT')
        tube1 = SampleTube('NT00001', sample)
        tube2 = LabTube('NT00002')

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube1)  # record sample
        self.dataset.commit_transaction()

        def raise_exception(self, *args):
            raise Exception("test exception")

        original = self.dataset.create_sample_tube  # save
        self.dataset.create_lab_tube = raise_exception  # patch

        try:
            sample_id = sample.get_sample_id()
            tube_barcode = tube2.get_barcode()
            # test that the sut logs the exception.
            with self.assertLogs() as ex:
                response = self.process.add_to_tube(sample_id, tube_barcode)
        finally:
            self.dataset.create_lab_tube = original  # restore

        self.assertEqual(Response.UNEXPECTED_ERROR, response.get_status())

    def test_sample_not_found(self):
        sample_id = 1
        tube_barcode = 'NT12345'
        response = self.process.add_to_tube(sample_id, tube_barcode)
        self.assertEqual(Response.SAMPLE_NOT_FOUND, response.get_status())

    def test_invalid_tube_barcode(self):
        sample_id = 1
        tube_barcode = 'NT0'
        response = self.process.add_to_tube(sample_id, tube_barcode)
        self.assertEqual(Response.INVALID_TUBE_BARCODE, response.get_status())

    def test_added_sample(self):
        sample = Sample('customer1', 'sample1', tag='ACGT')
        tube1 = SampleTube('NT00001', sample)
        tube2 = LabTube('NT00002')

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube1)  # record sample
        self.dataset.commit_transaction()

        sample_id = sample.get_sample_id()
        tube_barcode = tube2.get_barcode()

        response = self.process.add_to_tube(sample_id, tube_barcode)
        self.assertEqual(Response.ADDED_SAMPLE, response.get_status())
