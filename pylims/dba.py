"""Database Access."""

import logging
import sqlite3

from .config import database
from .lab import Sample, SampleTube, LabTube, Plate, Well

LOG = logging.getLogger(__name__)


class DataSet:
    """Provides access to DataSource using delegation."""

    def __init__(self, conf=None):
        """Initialises DataSet and creates underlying data source."""
        if conf is None:
            conf = database
        engine = conf['engine']
        if engine == 'sqlite3':
            self._data_source = SQLite3DataSource(conf)
        else:
            self._data_source = None
            raise NotImplementedError("DataSource not implemented: %s" % engine)

    def __getattr__(self, name):
        """Delegates calls to DataSource."""
        return getattr(self._data_source, name)

    def get_data_source(self):
        """Returns the configured DataSource."""
        return self._data_source


class DataSource:
    """Provides access to database."""

    def get_conf(self):
        """Returns database configuration."""
        raise NotImplementedError("Method not implemented.")

    def get_conn(self):
        """Returns database connection."""
        raise NotImplementedError("Method not implemented.")

    def start_connection(self):
        """Starts database connection."""
        raise NotImplementedError("Method not implemented.")

    def close_connection(self):
        """Closes database connection."""
        raise NotImplementedError("Method not implemented.")

    def find_sample_by_customer_sample_name(self, customer, name):
        """Finds Sample by customer and sample name used by customer."""
        raise NotImplementedError("Method not implemented.")

    def find_sample_tube_by_barcode(self, barcode):
        """Finds SampleTube by barcode."""
        raise NotImplementedError("Method not implemented.")

    def find_lab_tube_by_barcode(self, tube_barcode):
        """Finds LabTube by barcode."""
        raise NotImplementedError("Method not implemented.")

    def begin_transaction(self):
        """Begins database transaction."""
        raise NotImplementedError("Method not implemented.")

    def commit_transaction(self):
        """Commits the current transaction."""
        raise NotImplementedError("Method not implemented.")

    def rollback_transaction(self):
        """Roll backs any changes since the last commit."""
        raise NotImplementedError("Method not implemented.")

    def create_sample_tube(self, tube):
        """Creates Tube and its Sample in the database and
        assigns sample_id in Sample."""
        raise NotImplementedError("Method not implemented.")

    def create_lab_tube(self, tube):
        """Creates LabTube and its Sample in the database."""
        raise NotImplementedError("Method not implemented.")

    def move_sample(self, source, destination):
        """Transfers Sample from source Tube to destination Tube."""
        raise NotImplementedError("Method not implemented.")

    def find_plate_by_barcode(self, barcode):
        """Finds Plate by barcode."""
        raise NotImplementedError("Method not implemented.")

    def find_sample_by_sample_id(self, sample_id):
        """Finds Sample by sample_id."""
        raise NotImplementedError("Method not implemented.")

    def update_sample_tag(self, tag):
        """Updates tag of Sample in the database and
        assigns tag in Sample."""
        raise NotImplementedError("Method not implemented.")

    def create_plate(self, plate):
        """Creates Plate and its Wells in the database."""
        raise NotImplementedError("Method not implemented.")

    def create_well(self, plate, well):
        """Creates Well in the database and adds it to Plate."""
        raise NotImplementedError("Method not implemented.")


class SQLite3DataSource(DataSource):
    """DataSource that uses a SQLite database."""

    def __init__(self, conf):
        """Initialises DataSource using database config."""
        self._conf = conf
        self._conn = None
        self.start_connection()

    def start_connection(self):
        """Starts database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self._conf['name'])

    def close_connection(self):
        """Closes database connection."""
        if self._conn:
            self._conn.close()

    def get_conf(self):
        """Returns database configuration."""
        return self._conf

    def get_conn(self):
        """Returns database connection."""
        return self._conn

    def find_sample_by_customer_sample_name(self, customer, name):
        """Finds Sample by customer and sample name."""
        sql = ("select customer, name, sample_id, tag from sample "
               "where customer = ? and name = ?")
        params = (customer, name)
        cursor = self._conn.cursor()  # with statement does not work with this.
        try:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            if result:
                customer, name, sample_id, tag = result[0]
                sample = Sample(customer, name, sample_id, tag)
                return sample
        finally:
            cursor.close()

    def find_tube_by_barcode(self, barcode):
        """Finds Tube by barcode."""
        sample_tube = self.find_sample_tube_by_barcode(barcode)
        if sample_tube:
            return sample_tube
        lab_tube = self.find_lab_tube_by_barcode(barcode)
        return lab_tube

    def find_sample_tube_by_barcode(self, barcode):
        """Finds SampleTube by barcode."""
        return self.find_tube_by_kind_barcode('sample_tube', barcode)

    def find_lab_tube_by_barcode(self, barcode):
        """Finds LabTube by barcode"""
        return self.find_tube_by_kind_barcode('lab_tube', barcode)

    def find_tube_by_kind_barcode(self, kind, barcode):
        """Finds Tube by kind (sample_tube or lab_tube) and barcode."""
        sql = ("select barcode, sample_id, moved_to "
               "from %s where barcode = ?" % kind)
        params = (barcode,)
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            if result:
                barcode, sample_id, moved_to = result[0]
                if kind == 'sample_tube':
                    tube = SampleTube(barcode)
                else:
                    tube = LabTube(barcode)
                if moved_to is not None:
                    tube.set_moved_to(moved_to)
                if sample_id is None:
                    return tube
                else:
                    # eager fetch sample
                    sample = self.find_sample_by_sample_id(sample_id)
                    tube.set_sample(sample)
                    return tube
        finally:
            cursor.close()

    def begin_transaction(self):
        """Begins transaction on the database connection."""
        # Automatically starts at INSERT, UPDATE, or DELETE and finishes when
        # you call a commit or rollback.
        # Alternatively, we could set isolation_level = None to enable SQLite
        # library autocommit mode but is is disabled when you issue a BEGIN,
        # and enabled again when you issue a COMMIT or ROLLBACK.
        return

    def commit_transaction(self):
        """Commits transaction on the database connection."""
        return self._conn.commit()

    def rollback_transaction(self):
        """Rollbacks transaction on the database connection."""
        return self._conn.rollback()

    def create_sample_tube(self, tube):
        """Creates SampleTube and Sample, and assigns sample_id to Sample."""
        sql = "insert into sample (customer, name) values (?, ?)"
        sample = tube.get_sample()
        params = sample.get_customer(), sample.get_name()
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
            sample_id = cursor.lastrowid
            sample.set_sample_id(sample_id)
        finally:
            cursor.close()

        return self._create_tube('sample_tube', tube)

    def create_lab_tube(self, tube):
        """Creates LabTube."""
        return self._create_tube('lab_tube', tube)

    def _create_tube(self, kind, tube):
        """Creates Tube as either SampleTube or LabTube depending on the kind
        argument, which is either sample_tube or lab_tube."""
        sql = "insert into %s (barcode, sample_id) values (?, ?)" % kind
        params = tube.get_barcode(), tube.get_sample().get_sample_id()
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
        finally:
            cursor.close()

    def move_sample(self, source_tube, destination_tube):
        """Transfers Sample from source_tube to destination_tube. The moved_to
        field of the source_tube is set to destination_tube barcode as well.
        """
        if isinstance(source_tube, SampleTube):
            kind = 'sample_tube'
        else:
            kind = 'lab_tube'
        sample = source_tube.get_sample()

        sql = ("update %s set sample_id = ?, moved_to = ? "
               "where barcode = ?" % kind)
        params = (None, destination_tube.get_barcode(),
                  source_tube.get_barcode())
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
        finally:
            cursor.close()

        sql = "insert into %s (barcode, sample_id) values (?, ?)" % kind
        params = (destination_tube.get_barcode(), sample.get_sample_id())
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
        finally:
            cursor.close()

        source_tube.set_sample(None)
        source_tube.set_moved_to(destination_tube.get_barcode())
        destination_tube.set_sample(sample)

    def find_plate_by_barcode(self, barcode):
        """Finds Plate by barcode, together with all Plate wells."""
        sql = "select barcode, grid from plate where barcode = ?"
        params = (barcode,)
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            if result:
                barcode, grid = result[0]
                wells = self._find_wells_by_barcode(barcode)
                plate = Plate(barcode, grid, wells)
                return plate
        finally:
            cursor.close()

    def _find_wells_by_barcode(self, barcode):
        """Finds wells by plate barcode ordered by Well position."""
        sql = "select label, sample_id from well where plate_barcode = ?" \
              "order by substr(label, 1, 1), cast (substr(label, 2) as integer)"
        params = (barcode,)
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            wells = []
            for label, sample_id in result:
                sample = self.find_sample_by_sample_id(sample_id)
                well = Well(label, sample)
                wells.append(well)
            return wells
        finally:
            cursor.close()

    def update_sample_tag(self, sample, tag):
        """Updates tag of sample."""
        sql = "update sample set tag = ? where sample_id = ?"
        params = tag, sample.get_sample_id()
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
        finally:
            cursor.close()
        sample.set_tag(tag)

    def update_sample_concentration(self, sample, value):
        """Updates tag of sample."""
        sql = "update sample set concentration = ? where sample_id = ?"
        params = value, sample.get_sample_id()
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
        finally:
            cursor.close()
        sample.set_concentration(value)

    def create_plate(self, plate):
        """Creates a Plate and its wells."""
        sql = "insert into plate (barcode, grid) values (?, ?)"
        params = (plate.get_barcode(), plate.get_grid())
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
        finally:
            cursor.close()
        sql = ("insert into well (plate_barcode, label, sample_id) "
               "values (?, ?, ?)")
        plate_barcode = plate.get_barcode()
        wells = plate.get_wells()
        cursor = self._conn.cursor()
        try:
            for well in wells:
                params = (plate_barcode, well.get_label(),
                          well.get_sample().get_sample_id())
                cursor.execute(sql, params)
        finally:
            cursor.close()

    def create_well(self, plate, well):
        """Creates a Well and adds to plate."""
        sql = ("insert into well (plate_barcode, label, sample_id) "
               "values (?, ?, ?)")
        params = (plate.get_barcode(), well.get_label(),
                  well.get_sample().get_sample_id())
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
        finally:
            cursor.close()
        plate.add_well(well)

    def find_sample_by_sample_id(self, sample_id):
        """Finds Sample by sample_id."""
        sql = ("select customer, name, sample_id, tag from sample "
               "where sample_id = ?")
        params = (sample_id,)
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            if result:
                customer, name, sample_id, tag = result[0]
                sample = Sample(customer=customer, name=name,
                                sample_id=sample_id, tag=tag)
                return sample
        finally:
            cursor.close()

    def _reset_tables(self):
        """Truncates tables and resets sequences of the underlying database."""
        tables = 'sample sample_tube lab_tube plate well'.split()
        for table in tables:
            sql = "delete from %s" % table
            self._conn.execute(sql)
            sql = "delete from sqlite_sequence where name = ?"
            params = table,
            self._conn.execute(sql, params)
        self._conn.commit()
