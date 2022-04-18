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

    def test_invalid_source_tube_barcode(self):
        source_tube_barcode = 'NT0'
        destination_tube_barcode = 'NT12345'
        response = self.process.tube_transfer(source_tube_barcode,
                                              destination_tube_barcode)
        self.assertEqual(Response.INVALID_SOURCE_TUBE_BARCODE,
                         response.get_status())

    def test_invalid_destination_tube_barcode(self):
        source_tube_barcode = 'NT12345'
        destination_tube_barcode = 'NT1'
        response = self.process.tube_transfer(source_tube_barcode,
                                              destination_tube_barcode)
        self.assertEqual(Response.INVALID_DESTINATION_TUBE_BARCODE,
                         response.get_status())

    def test_source_tube_not_found(self):
        source_tube_barcode = 'NT12345'
        destination_tube_barcode = 'NT23456'
        response = self.process.tube_transfer(source_tube_barcode,
                                              destination_tube_barcode)
        self.assertEqual(Response.SOURCE_TUBE_NOT_FOUND, response.get_status())

    def test_discarded_source_sample_tube(self):
        sample = Sample('customer1', 'sample1')
        tube1 = SampleTube('NT12345', sample)
        tube2 = SampleTube('NT56789')

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube1)
        self.dataset.move_sample(tube1, tube2)
        self.dataset.commit_transaction()

        source_tube_barcode = tube1.get_barcode()
        destination_tube_barcode = 'NT99999'
        response = self.process.tube_transfer(source_tube_barcode,
                                              destination_tube_barcode)
        self.assertEqual(Response.DISCARDED_SOURCE_TUBE, response.get_status())

    def test_discarded_destination_sample_tube(self):
        sample = Sample('customer0', 'sample0')
        tube0 = SampleTube('NT10000', sample)

        sample = Sample('customer1', 'sample1')
        tube1 = SampleTube('NT10001', sample)
        tube2 = SampleTube('NT10002')

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube0)
        self.dataset.create_sample_tube(tube1)
        self.dataset.move_sample(tube1, tube2)
        self.dataset.commit_transaction()

        destination_tube_barcode = tube1.get_barcode()
        source_tube_barcode = tube0.get_barcode()
        response = self.process.tube_transfer(source_tube_barcode,
                                              destination_tube_barcode)
        self.assertEqual(Response.DISCARDED_DESTINATION_TUBE,
                         response.get_status())

    def test_discarded_source_lab_tube(self):
        sample = Sample('customer0', 'sample0')
        tube0 = SampleTube('NT10000', sample)
        tube1 = LabTube('NT10001', sample)
        tube2 = LabTube('NT10002')

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube0)
        self.dataset.create_lab_tube(tube1)
        self.dataset.move_sample(tube1, tube2)
        self.dataset.commit_transaction()

        source_tube_barcode = tube1.get_barcode()
        destination_tube_barcode = 'NT12345'
        response = self.process.tube_transfer(source_tube_barcode,
                                              destination_tube_barcode)
        self.assertEqual(Response.DISCARDED_SOURCE_TUBE, response.get_status())

    def test_discarded_destination_lab_tube(self):
        sample = Sample('customer0', 'sample0')
        tube0 = SampleTube('NT10000', sample)
        tube1 = LabTube('NT10001', sample)
        tube2 = LabTube('NT10002')
        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube0)
        self.dataset.create_lab_tube(tube1)
        self.dataset.move_sample(tube1, tube2)
        self.dataset.commit_transaction()

        source_tube_barcode = tube2.get_barcode()
        destination_tube_barcode = tube1.get_barcode()
        response = self.process.tube_transfer(source_tube_barcode,
                                              destination_tube_barcode)
        self.assertEqual(Response.DISCARDED_DESTINATION_TUBE,
                         response.get_status())

    def test_existing_destination_sample_tube(self):
        sample = Sample('customer0', 'sample0')
        tube0 = SampleTube('NT10000', sample)

        sample = Sample('customer1', 'sample1')
        tube1 = SampleTube('NT10001', sample)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube0)
        self.dataset.create_sample_tube(tube1)
        self.dataset.commit_transaction()

        source_tube_barcode = tube0.get_barcode()
        destination_tube_barcode = tube1.get_barcode()
        response = self.process.tube_transfer(source_tube_barcode,
                                              destination_tube_barcode)
        self.assertEqual(Response.DESTINATION_TUBE_NOT_EMPTY,
                         response.get_status())

    def test_existing_destination_lab_tube(self):
        sample = Sample('customer1', 'sample1')
        tube1 = SampleTube('NT0001', sample)
        tube2 = LabTube('NT00002', sample)
        tube3 = LabTube('NT00003', sample)
        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube1)
        self.dataset.create_lab_tube(tube2)
        self.dataset.create_lab_tube(tube3)
        self.dataset.commit_transaction()

        source_tube_barcode = tube2.get_barcode()
        destination_tube_barcode = tube3.get_barcode()
        response = self.process.tube_transfer(source_tube_barcode,
                                              destination_tube_barcode)
        self.assertEqual(Response.DESTINATION_TUBE_NOT_EMPTY,
                         response.get_status())

    def test_sample_tube_unexpected_error(self):
        sample = Sample('customer0', 'sample0')
        tube0 = SampleTube('NT10000', sample)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube0)
        self.dataset.commit_transaction()

        def raise_exception(*args):
            raise Exception('test exception')

        original = self.dataset.move_sample
        self.dataset.move_sample = raise_exception
        try:
            source_tube_barcode = tube0.get_barcode()
            destination_tube_barcode = 'NT12345'
            # test that the sut logs the exception.
            with self.assertLogs() as ex:
                response = self.process.tube_transfer(source_tube_barcode,
                                                  destination_tube_barcode)
        finally:
            self.dataset.move_sample = original

        self.assertEqual(Response.UNEXPECTED_ERROR, response.get_status())

    def test_moved_sample_tube(self):
        sample = Sample('customer0', 'sample0')
        tube0 = SampleTube('NT10000', sample)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube0)
        self.dataset.commit_transaction()

        source_tube_barcode = tube0.get_barcode()
        destination_tube_barcode = 'NT12345'
        response = self.process.tube_transfer(source_tube_barcode,
                                              destination_tube_barcode)
        self.assertEqual(Response.MOVED_SAMPLE, response.get_status())

    def test_moved_lab_tube(self):
        sample = Sample('customer1', 'sample1')
        tube1 = SampleTube('NT00001', sample)
        tube2 = LabTube('NT00002', sample)
        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube1)
        self.dataset.create_lab_tube(tube2)
        self.dataset.commit_transaction()

        source_tube_barcode = tube2.get_barcode()
        destination_tube_barcode = 'NT00003'
        response = self.process.tube_transfer(source_tube_barcode,
                                              destination_tube_barcode)
        self.assertEqual(Response.MOVED_SAMPLE, response.get_status())
