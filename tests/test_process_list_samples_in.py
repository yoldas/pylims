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

    def test_invalid_barcode_prefix(self):
        barcode = 'XX12345'
        response = self.process.list_samples_in(barcode)
        self.assertEqual(Response.INVALID_BARCODE_PREFIX, response.get_status())

    def test_invalid_tube_barcode(self):
        barcode = 'NT0'
        response = self.process.list_samples_in(barcode)
        self.assertEqual(Response.INVALID_TUBE_BARCODE, response.get_status())

    def test_invalid_plate_barcode(self):
        barcode = 'DN0'
        response = self.process.list_samples_in(barcode)
        self.assertEqual(Response.INVALID_PLATE_BARCODE, response.get_status())

    def test_found_discarded_sample_tube(self):
        source_barcode = 'NT12345'
        sample = Sample('customer1', 'sample1')
        source = SampleTube(source_barcode, sample)
        target = SampleTube('NT56789')

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(source)
        self.dataset.move_sample(source, target)
        self.dataset.commit_transaction()

        response = self.process.list_samples_in(source_barcode)
        self.assertEqual(Response.FOUND_DISCARDED_SAMPLE_TUBE,
                         response.get_status())

    def test_found_discarded_lab_tube(self):
        sample = Sample('customer1', 'sample1')
        sample_tube = SampleTube('NT00001', sample)
        barcode = 'NT00002'
        source = LabTube(barcode, sample)
        target = LabTube('NT00003')

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(sample_tube)
        self.dataset.create_lab_tube(source)
        self.dataset.move_sample(source, target)
        self.dataset.commit_transaction()

        response = self.process.list_samples_in(barcode)
        self.assertEqual(Response.FOUND_DISCARDED_LAB_TUBE,
                         response.get_status())

    def test_found_sample_tube(self):
        barcode = 'NT12345'
        customer = 'customer1'
        name = 'sample1'
        tag = 'ACGT'
        tube = SampleTube(barcode, Sample(customer, name, tag=tag))

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(tube)
        self.dataset.commit_transaction()

        response = self.process.list_samples_in(barcode)
        self.assertEqual(Response.FOUND_SAMPLE_TUBE, response.get_status())

    def test_found_lab_tube(self):
        sample = Sample('customer1', 'sample1', tag='ACGT')
        sample_tube = SampleTube('NT12345', sample)

        lab_barcode = 'NT54321'
        lab_tube = LabTube(lab_barcode, sample)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(sample_tube)
        self.dataset.create_lab_tube(lab_tube)
        self.dataset.commit_transaction()

        response = self.process.list_samples_in(lab_barcode)
        self.assertEqual(Response.FOUND_LAB_TUBE, response.get_status())

    def test_found_plate(self):
        sample1 = Sample('customer1', 'sample1', tag='AAAA')
        sample_tube1 = SampleTube('NT00001', sample1)

        sample2 = Sample('customer1', 'sample11', tag='CCCC')
        sample_tube2 = SampleTube('NT00002', sample2)

        sample3 = Sample('customer2', 'sample2', tag='GGGG')
        sample_tube3 = SampleTube('NT00003', sample3)

        barcode = 'DN54321'
        wells = [Well('A1', sample1), Well('A2', sample1), Well('B1', sample2)]
        plate = Plate(barcode, wells=wells)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(sample_tube1)
        self.dataset.create_sample_tube(sample_tube2)
        self.dataset.create_sample_tube(sample_tube3)
        self.dataset.create_plate(plate)
        self.dataset.commit_transaction()

        response = self.process.list_samples_in(barcode)
        self.assertEqual(Response.FOUND_PLATE, response.get_status())

    def test_plate_not_found(self):
        barcode = 'DN12345'
        response = self.process.list_samples_in(barcode)
        self.assertEqual(Response.PLATE_NOT_FOUND, response.get_status())

    def test_tube_not_found(self):
        barcode = 'NT12345'
        response = self.process.list_samples_in(barcode)
        self.assertEqual(Response.TUBE_NOT_FOUND, response.get_status())
