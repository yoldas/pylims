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

    def test_invalid_customer_sample_name(self):
        customer_sample_name = 'customer1'
        tube_barcode = 'NT12345'
        response = self.process.record_receipt(
            customer_sample_name, tube_barcode)

        self.assertEqual(Response.INVALID_CUSTOMER_SAMPLE_NAME,
                         response.get_status())

    def test_invalid_tube_barcode(self):
        customer_sample_name = 'customer1-sample1'
        tube_barcode = 'XX12345'
        response = self.process.record_receipt(
            customer_sample_name, tube_barcode)

        self.assertEqual(Response.INVALID_TUBE_BARCODE, response.get_status())

    def test_existing_customer_sample_name(self):
        sample = Sample('customer1', 'sample1', tag='ACGT')
        tube1 = SampleTube('NT12345', sample)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube1)
        self.dataset.commit_transaction()

        customer_sample_name = sample.get_customer_sample_name()
        tube_barcode = tube1.get_barcode()
        response = self.process.record_receipt(
            customer_sample_name, tube_barcode)

        self.assertEqual(Response.EXISTING_CUSTOMER_SAMPLE_NAME,
                         response.get_status())

    def test_discarded_sample_tube(self):
        sample = Sample('customer1', 'sample1', tag='ACGT')
        tube1 = SampleTube('NT12345', sample)
        tube2 = SampleTube('NT54321')

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube1)
        self.dataset.move_sample(tube1, tube2)
        self.dataset.commit_transaction()

        customer_sample_name = 'customer1-sample2'
        tube_barcode = tube1.get_barcode()
        response = self.process.record_receipt(
            customer_sample_name, tube_barcode)

        self.assertEqual(Response.DISCARDED_SAMPLE_TUBE, response.get_status())

    def test_existing_sample_tube(self):
        sample = Sample('customer1', 'sample1', tag='ACGT')
        tube = SampleTube('NT12345', sample)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube)
        self.dataset.commit_transaction()

        customer_sample_name = 'customer1-sample2'
        tube_barcode = tube.get_barcode()
        response = self.process.record_receipt(
            customer_sample_name, tube_barcode)

        self.assertEqual(Response.EXISTING_SAMPLE_TUBE, response.get_status())

    def test_discarded_lab_tube(self):
        sample = Sample('customer1', 'sample1')
        sample_tube = SampleTube('NT00001', sample)
        tube_barcode = 'NT00002'
        source = LabTube(tube_barcode, sample)
        target = LabTube('NT00003')

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(sample_tube)
        self.dataset.create_lab_tube(source)
        self.dataset.move_sample(source, target)
        self.dataset.commit_transaction()

        customer_sample_name = 'customer1-sample2'

        response = self.process.record_receipt(
            customer_sample_name, tube_barcode)

        self.assertEqual(Response.DISCARDED_LAB_TUBE, response.get_status())

    def test_existing_lab_tube(self):
        sample = Sample('customer1', 'sample1', tag='ACGT')
        sample_tube = SampleTube('NT12345', sample)

        tube_barcode = 'NT54321'
        lab_tube = LabTube(tube_barcode, sample)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(sample_tube)
        self.dataset.create_lab_tube(lab_tube)
        self.dataset.commit_transaction()

        customer_sample_name = 'customer1-sample2'
        response = self.process.record_receipt(
            customer_sample_name, tube_barcode)

        self.assertEqual(Response.EXISTING_LAB_TUBE, response.get_status())

    def test_unexpected_error(self):
        customer_sample_name = 'customer1-sample1'
        tube_barcode = 'NT12345'

        def raise_exception(self, *args):
            raise Exception("test exception")

        original = self.dataset.create_sample_tube
        self.dataset.create_sample_tube = raise_exception
        try:
            with self.assertLogs() as ex:
                response = self.process.record_receipt(
                    customer_sample_name, tube_barcode)
        finally:
            self.dataset.create_sample_tube = original

        self.assertEqual(Response.UNEXPECTED_ERROR, response.get_status())

    def test_recorded_sample(self):
        customer_sample_name = 'customer1-sample1'
        tube_barcode = 'NT12345'
        response = self.process.record_receipt(
            customer_sample_name, tube_barcode)

        self.assertEqual(Response.RECORDED_SAMPLE, response.get_status())
        self.assertIsNotNone(response.get_data())
        tube = response.get_data().get('tube')
        sample_id = tube.get_sample().get_sample_id()

        self.assertIsNotNone(sample_id)
        self.assertEqual(1, sample_id)
