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

    def test_invalid_plate_barcode(self):
        plate_barcode = 'DN0'
        sample_id = 1
        well_position = 'A1'

        response = self.process.add_to_plate(
            sample_id, plate_barcode, well_position)

        self.assertEqual(Response.INVALID_PLATE_BARCODE, response.get_status())

    def test_invalid_well_position(self):
        plate_barcode = 'DN12345'
        sample_id = 1
        well_position = 'X'

        response = self.process.add_to_plate(
            sample_id, plate_barcode, well_position)

        self.assertEqual(Response.INVALID_WELL_POSITION, response.get_status())

    def test_sample_not_found(self):
        plate_barcode = 'DN12345'
        sample_id = 1  # sample does not exist yet.
        well_position = 'A1'

        response = self.process.add_to_plate(
            sample_id, plate_barcode, well_position)

        self.assertEqual(Response.SAMPLE_NOT_FOUND, response.get_status())

    def test_existing_plate_well_out_of_range(self):
        sample = Sample('customer1', 'sample1')
        sample_tube = SampleTube('NT12345', sample)

        plate = Plate('DN12345')
        well = Well('A1', sample)
        plate.add_well(well)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(sample_tube)
        self.dataset.create_plate(plate)
        self.dataset.commit_transaction()

        sample_id = sample.get_sample_id()
        plate_barcode = plate.get_barcode()
        well_position = 'A13'  # out of range

        response = self.process.add_to_plate(
            sample_id, plate_barcode, well_position)

        self.assertEqual(Response.WELL_OUT_OF_RANGE, response.get_status())

    def test_existing_plate_well_not_empty(self):
        sample = Sample('customer1', 'sample1')
        sample_tube = SampleTube('NT12345', sample)

        plate = Plate('DN12345')
        well = Well('A1', sample)
        plate.add_well(well)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(sample_tube)
        self.dataset.create_plate(plate)
        self.dataset.commit_transaction()

        sample_id = sample.get_sample_id()
        plate_barcode = plate.get_barcode()
        well_position = 'A1'  # same well position

        response = self.process.add_to_plate(
            sample_id, plate_barcode, well_position)

        self.assertEqual(Response.WELL_NOT_EMPTY, response.get_status())

    def test_existing_plate_unexpected_error(self):
        sample = Sample('customer1', 'sample1')
        sample_tube = SampleTube('NT12345', sample)

        plate = Plate('DN12345')
        well = Well('A1', sample)
        plate.add_well(well)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(sample_tube)
        self.dataset.create_plate(plate)
        self.dataset.commit_transaction()

        sample_id = sample.get_sample_id()
        plate_barcode = plate.get_barcode()
        well_position = 'A2'

        def raise_exception(self, *args):
            raise Exception('test exception')

        original = self.dataset.create_well
        self.dataset.create_well = raise_exception
        try:
            # test that the sut logs the exception.
            with self.assertLogs() as ex:
                response = self.process.add_to_plate(
                    sample_id, plate_barcode, well_position)
        finally:
            self.dataset.create_well = original

        self.assertEqual(Response.UNEXPECTED_ERROR, response.get_status())

    def test_existing_plate_added_sample(self):
        sample = Sample('customer1', 'sample1')
        sample_tube = SampleTube('NT12345', sample)

        plate = Plate('DN12345')
        well = Well('A1', sample)
        plate.add_well(well)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(sample_tube)
        self.dataset.create_plate(plate)
        self.dataset.commit_transaction()

        sample_id = sample.get_sample_id()
        plate_barcode = plate.get_barcode()
        well_position = 'A2'

        response = self.process.add_to_plate(
            sample_id, plate_barcode, well_position)

        self.assertEqual(Response.ADDED_SAMPLE_TO_PLATE, response.get_status())

    def test_new_plate_well_out_of_range(self):
        sample = Sample('customer1', 'sample1')
        sample_tube = SampleTube('NT12345', sample)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(sample_tube)
        self.dataset.commit_transaction()

        sample_id = sample.get_sample_id()
        plate_barcode = 'DN12345'
        well_position = 'H13'  # out of range

        response = self.process.add_to_plate(
            sample_id, plate_barcode, well_position)

        self.assertEqual(Response.WELL_OUT_OF_RANGE, response.get_status())

    def test_new_plate_unexpected_error(self):
        sample = Sample('customer1', 'sample1')
        sample_tube = SampleTube('NT12345', sample)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(sample_tube)
        self.dataset.commit_transaction()

        def raise_exception(self, *args):
            raise Exception('test exception')

        sample_id = sample.get_sample_id()
        plate_barcode = 'DN12345'
        well_position = 'A1'

        original = self.dataset.create_plate
        self.dataset.create_plate = raise_exception
        try:
            with self.assertLogs() as ex:
                response = self.process.add_to_plate(
                    sample_id, plate_barcode, well_position)
        finally:
            self.dataset.create_plate = original

        self.assertEqual(Response.UNEXPECTED_ERROR, response.get_status())

    def test_new_plate_added_sample(self):
        sample = Sample('customer1', 'sample1')
        sample_tube = SampleTube('NT12345', sample)

        self.dataset.begin_transaction()
        self.dataset.create_sample_tube(sample_tube)
        self.dataset.commit_transaction()

        sample_id = sample.get_sample_id()
        plate_barcode = 'DN12345'
        well_position = 'A1'

        response = self.process.add_to_plate(
            sample_id, plate_barcode, well_position)

        self.assertEqual(Response.ADDED_SAMPLE_TO_PLATE, response.get_status())
