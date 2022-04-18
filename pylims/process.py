"""Processing"""

import logging

from .dba import DataSet
from .lab import Tube, Plate, Sample, SampleTube, LabTube, Well

LOG = logging.getLogger(__name__)


class Methods:
    """Provides method signatures. """

    def record_receipt(self, customer_sample_name, tube_barcode):
        """Records a Sample."""
        raise NotImplementedError("Method not implemented.")

    def add_to_tube(self, sample_id, tube_barcode):
        """Adds a Sample to a Tube."""
        raise NotImplementedError("Method not implemented.")

    def add_to_plate(self, sample_id, plate_barcode, well_position):
        """Adds a Sample to a Plate Well."""
        raise NotImplementedError("Method not implemented.")

    def tube_transfer(self, source_tube_barcode, destination_tube_barcode):
        """Moves Sample from a source Tube to a destination Tube."""
        raise NotImplementedError("Method not implemented.")

    def list_samples_in(self, container_barcode):
        """Lists Samples in a Container."""
        raise NotImplementedError("Method not implemented.")

    def tag(self, sample_id, tag):
        """Applies a tag to a Sample."""
        raise NotImplementedError("Method not implemented.")


class Response:
    """Result of Methods."""

    # Status constants
    INVALID_CUSTOMER_SAMPLE_NAME = 'Invalid customer sample name'
    INVALID_TUBE_BARCODE = 'Invalid tube barcode'
    EXISTING_CUSTOMER_SAMPLE_NAME = 'Existing customer sample name'
    DISCARDED_SAMPLE_TUBE = 'Discarded sample tube'
    EXISTING_SAMPLE_TUBE = 'Existing sample tube'
    DISCARDED_LAB_TUBE = 'Discarded lab tube'
    EXISTING_LAB_TUBE = 'Existing lab tube'
    UNEXPECTED_ERROR = 'Unexpected Error'
    RECORDED_SAMPLE = 'Recorded sample'  # OK
    SAMPLE_NOT_FOUND = 'Sample not found'
    ADDED_SAMPLE = 'Added sample'  # OK
    INVALID_SOURCE_TUBE_BARCODE = 'Invalid source tube barcode'
    INVALID_DESTINATION_TUBE_BARCODE = 'Invalid destination tube barcode'
    SOURCE_TUBE_NOT_FOUND = 'Source tube not found'
    DISCARDED_SOURCE_TUBE = 'Discarded source tube'
    DISCARDED_DESTINATION_TUBE = 'Discarded destination tube'
    DESTINATION_TUBE_NOT_EMPTY = 'Destination tube not empty'
    MOVED_SAMPLE = 'Moved sample'  # success
    INVALID_PLATE_BARCODE = 'Invalid plate barcode'
    INVALID_WELL_POSITION = 'Invalid well position'
    WELL_OUT_OF_RANGE = 'Well out of range'
    WELL_NOT_EMPTY = 'Well not empty'
    ADDED_SAMPLE_TO_PLATE = 'Added sample to plate'  # OK
    PLATE_IS_FULL = 'Plate is full'
    INVALID_TAG = 'Invalid tag'
    ALREADY_TAGGED = 'Already tagged'
    TAGGED_SAMPLE = 'Tagged sample'  # OK
    FOUND_DISCARDED_SAMPLE_TUBE = 'Found discarded sample tube' # OK
    FOUND_SAMPLE_TUBE = 'Found sample tube'  # OK
    FOUND_DISCARDED_LAB_TUBE = 'Found discarded lab tube'  # OK
    FOUND_LAB_TUBE = 'Found lab tube'  # OK
    TUBE_NOT_FOUND = 'Tube not found'
    FOUND_PLATE = 'Found plate' # OK
    PLATE_NOT_FOUND = 'Plate not found'
    INVALID_BARCODE_PREFIX = 'Invalid barcode prefix'

    def __init__(self, status, data=None):
        """Initialises Response with status and data."""
        self._status = status
        self._data = data or dict()

    def get_status(self):
        """Returns status."""
        return self._status

    def get_data(self):
        """Returns a dictionary that contains result of Methods."""
        return self._data


class Process(Methods):
    """Receives user input and returns Responses."""

    def __init__(self, dataset=None):
        """Initialises a Process using DataSet."""
        if dataset is None:
            dataset = DataSet() # default
        self._dataset = dataset

    def get_dataset(self):
        """Returns DataSet of this Process."""
        return self._dataset

    def record_receipt(self, customer_sample_name, tube_barcode):
        """Records Sample and SampleTube."""
        data = dict(customer_sample_name=customer_sample_name,
                    barcode=tube_barcode)
        if not Sample.validate_customer_sample_name_format(
                customer_sample_name):
            data['name_delimiter'] = Sample.name_delimiter
            return Response(Response.INVALID_CUSTOMER_SAMPLE_NAME, data)

        if not Tube.validate_barcode_format(tube_barcode):
            return Response(Response.INVALID_TUBE_BARCODE, data)

        customer, sample_name = Sample.split_customer_sample_name(
            customer_sample_name)
        sample = self._dataset.find_sample_by_customer_sample_name(
            customer, sample_name)
        if sample:
            data['sample'] = sample
            return Response(Response.EXISTING_CUSTOMER_SAMPLE_NAME, data)

        sample_tube = self._dataset.find_sample_tube_by_barcode(tube_barcode)
        if sample_tube:
            data['tube'] = sample_tube
            if sample_tube.is_discarded():
                return Response(Response.DISCARDED_SAMPLE_TUBE, data)
            else:
                return Response(Response.EXISTING_SAMPLE_TUBE, data)

        lab_tube = self._dataset.find_lab_tube_by_barcode(tube_barcode)
        if lab_tube:
            data['tube'] = lab_tube
            if lab_tube.is_discarded():
                return Response(Response.DISCARDED_LAB_TUBE, data)
            else:
                return Response(Response.EXISTING_LAB_TUBE, data)

        sample = Sample(customer, sample_name)
        tube = SampleTube(tube_barcode, sample)
        self._dataset.begin_transaction()
        try:
            self._dataset.create_sample_tube(tube)
        except Exception:
            self._dataset.rollback_transaction()
            LOG.exception("record_receipt('%s', '%s')",
                          customer_sample_name, tube_barcode)
            return Response(Response.UNEXPECTED_ERROR, data)
        self._dataset.commit_transaction()

        data = dict(tube=tube)
        return Response(Response.RECORDED_SAMPLE, data)

    def add_to_tube(self, sample_id, tube_barcode):
        """Adds Sample to a Tube."""
        data = dict(barcode=tube_barcode, sample_id=sample_id)
        if not Tube.validate_barcode_format(tube_barcode):
            return Response(Response.INVALID_TUBE_BARCODE, data)

        sample = self._dataset.find_sample_by_sample_id(sample_id)
        if not sample:
            return Response(Response.SAMPLE_NOT_FOUND, data)

        sample_tube = self._dataset.find_sample_tube_by_barcode(tube_barcode)
        if sample_tube:
            data['tube'] = sample_tube
            if sample_tube.is_discarded():
                return Response(Response.DISCARDED_SAMPLE_TUBE, data)
            else:
                return Response(Response.EXISTING_SAMPLE_TUBE, data)

        lab_tube = self._dataset.find_lab_tube_by_barcode(tube_barcode)
        if lab_tube:
            data['tube'] = lab_tube
            if lab_tube.is_discarded():
                return Response(Response.DISCARDED_LAB_TUBE, data)
            else:
                return Response(Response.EXISTING_LAB_TUBE, data)

        tube = LabTube(tube_barcode, sample)
        self._dataset.begin_transaction()
        try:
            self._dataset.create_lab_tube(tube)
        except Exception:
            self._dataset.rollback_transaction()
            LOG.exception("add_to_tube(%s, '%s')", sample_id, tube_barcode)
            return Response(Response.UNEXPECTED_ERROR)
        self._dataset.commit_transaction()

        data['tube'] = tube
        return Response(Response.ADDED_SAMPLE, data)

    def add_to_plate(self, sample_id, plate_barcode, well_position):
        """Adds Sample to a Plate Well."""
        data = dict(sample_id=sample_id, plate_barcode=plate_barcode,
                    well_position=well_position)
        if not Plate.validate_barcode_format(plate_barcode):
            return Response(Response.INVALID_PLATE_BARCODE, data)

        if not Plate.validate_well_label_format(well_position):
            return Response(Response.INVALID_WELL_POSITION, data)

        sample = self._dataset.find_sample_by_sample_id(sample_id)
        if not sample:
            return Response(Response.SAMPLE_NOT_FOUND, data)

        plate = self._dataset.find_plate_by_barcode(plate_barcode)
        if plate:
            data['plate_grid'] = plate.get_grid()
            if plate.is_full():
                return Response(Response.PLATE_IS_FULL, data)
            if not plate.well_in_range(well_position):
                return Response(Response.WELL_OUT_OF_RANGE, data)
            if not plate.well_is_empty(well_position):
                return Response(Response.WELL_NOT_EMPTY, data)

            well = Well(well_position, sample)
            self._dataset.begin_transaction()
            try:
                self._dataset.create_well(plate, well)
            except Exception:
                self._dataset.rollback_transaction()
                LOG.exception("add_to_plate(%s, '%s', '%s')", sample_id,
                              plate_barcode, well_position)
                return Response(Response.UNEXPECTED_ERROR)
            self._dataset.commit_transaction()

            data['well'] = well
            return Response(Response.ADDED_SAMPLE_TO_PLATE, data)

        plate = Plate(plate_barcode)
        data['plate_grid'] = plate.get_grid()
        if not plate.well_in_range(well_position):
            return Response(Response.WELL_OUT_OF_RANGE, data)

        well = Well(well_position, sample)
        plate.add_well(well)
        self._dataset.begin_transaction()
        try:
            self._dataset.create_plate(plate)
        except:
            self._dataset.rollback_transaction()
            LOG.exception("add_to_plate(%s, '%s', '%s')", sample_id,
                          plate_barcode, well_position)
            return Response(Response.UNEXPECTED_ERROR, data)
        self._dataset.commit_transaction()

        data['well'] = well
        return Response(Response.ADDED_SAMPLE_TO_PLATE, data)

    def tube_transfer(self, source_tube_barcode, destination_tube_barcode):
        """Moves Sample from source Tube to destination Tube."""
        data = dict(source_tube_barcode=source_tube_barcode,
                    destination_tube_barcode=destination_tube_barcode)
        if not Tube.validate_barcode_format(source_tube_barcode):
            return Response(Response.INVALID_SOURCE_TUBE_BARCODE, data)
        if not Tube.validate_barcode_format(destination_tube_barcode):
            return Response(Response.INVALID_DESTINATION_TUBE_BARCODE, data)

        source = self._dataset.find_tube_by_barcode(source_tube_barcode)
        if not source:
            return Response(Response.SOURCE_TUBE_NOT_FOUND, data)
        data['source_tube'] = source
        if source.is_discarded():
            return Response(Response.DISCARDED_SOURCE_TUBE, data)

        destination = self._dataset.find_tube_by_barcode(
            destination_tube_barcode)
        if destination:
            data['destination_tube'] = destination
            if destination.is_discarded():
                return Response(Response.DISCARDED_DESTINATION_TUBE, data)
            else:
                return Response(Response.DESTINATION_TUBE_NOT_EMPTY, data)

        if isinstance(source, SampleTube):
            destination = SampleTube(destination_tube_barcode)
        else:
            destination = LabTube(destination_tube_barcode)
        self._dataset.begin_transaction()
        try:
            self._dataset.move_sample(source, destination)
        except Exception:
            self._dataset.rollback_transaction()
            LOG.exception("tube_transfer('%s', '%s')", source_tube_barcode,
                          destination_tube_barcode)
            return Response(Response.UNEXPECTED_ERROR, data)
        self._dataset.commit_transaction()

        data['destination_tube'] = destination
        return Response(Response.MOVED_SAMPLE, data)

    def list_samples_in(self, container_barcode):
        """Lists Samples in Container."""
        data = dict(barcode=container_barcode)
        if container_barcode.startswith(Tube.barcode_prefix):
            data['tube_barcode'] = container_barcode
            if not Tube.validate_barcode_format(container_barcode):
                return Response(Response.INVALID_TUBE_BARCODE, data)

            tube = self._dataset.find_sample_tube_by_barcode(container_barcode)
            if tube:
                data['result'] = tube
                if tube.is_discarded():
                    return Response(Response.FOUND_DISCARDED_SAMPLE_TUBE, data)
                else:
                    return Response(Response.FOUND_SAMPLE_TUBE, data)
            else:
                tube = self._dataset.find_lab_tube_by_barcode(container_barcode)
                if tube:
                    data['result'] = tube
                    if tube.is_discarded():
                        return Response(Response.FOUND_DISCARDED_LAB_TUBE, data)
                    else:
                        return Response(Response.FOUND_LAB_TUBE, data)
                else:
                    return Response(Response.TUBE_NOT_FOUND, data)

        elif container_barcode.startswith(Plate.barcode_prefix):
            data['plate_barcode'] = container_barcode
            if not Plate.validate_barcode_format(container_barcode):
                return Response(Response.INVALID_PLATE_BARCODE, data)

            plate = self._dataset.find_plate_by_barcode(container_barcode)
            if plate:
                data['result'] = plate
                return Response(Response.FOUND_PLATE, data)
            else:
                return Response(Response.PLATE_NOT_FOUND, data)
        else:
            data['prefix'] = container_barcode[:2]
            return Response(Response.INVALID_BARCODE_PREFIX, data)

    def tag(self, sample_id, tag):
        """Applies tag to Sample."""
        data = dict(sample_id=sample_id, tag=tag)
        if not Sample.validate_tag_format(tag):
            return Response(Response.INVALID_TAG, data)
        sample = self._dataset.find_sample_by_sample_id(sample_id)
        if not sample:
            return Response(Response.SAMPLE_NOT_FOUND, data)
        data['sample'] = sample
        if sample.get_tag() is not None:
            return Response(Response.ALREADY_TAGGED, data)
        self._dataset.begin_transaction()
        try:
            self._dataset.update_sample_tag(sample, tag)
        except Exception:
            self._dataset.rollback_transaction()
            LOG.exception("tag(%s, '%s')", sample_id, tag)
            return Response(Response.UNEXPECTED_ERROR, data)
        self._dataset.commit_transaction()
        return Response(Response.TAGGED_SAMPLE, data)
