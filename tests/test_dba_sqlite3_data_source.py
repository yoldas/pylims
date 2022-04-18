import os
import sqlite3
import unittest

from pylims import config
from pylims.lab import Sample, SampleTube, LabTube, Plate, Well
from pylims.dba import SQLite3DataSource

class DataSourceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conf = config.test_database
        cls.data_source = SQLite3DataSource(cls.conf)

    @classmethod
    def tearDownClass(cls):
        cls.data_source.close_connection()

    def setUp(self):
        conn = self.data_source.get_conn()
        tables = 'sample sample_tube lab_tube plate well'.split()
        for table in tables:
            cursor = conn.cursor()
            sql = "delete from %s" % table
            cursor.execute(sql)
        sql = "delete from sqlite_sequence where name='sample'"
        cursor.execute(sql)
        conn.commit()
        cursor.close()

    def tearDown(self):
        pass

    def test_init(self):
        self.assertDictEqual(self.conf, self.data_source.get_conf())
        self.assertIsInstance(self.data_source.get_conn(), sqlite3.Connection)

    def test_find_sample_by_customer_sample_name(self):
        conn = self.data_source.get_conn()
        sql = "insert into sample (customer, name, tag) values (?, ?, ?)"
        customer = 'customer1'
        name = 'sample1'
        tag = 'CAT'
        params = (customer, name, tag)
        conn.execute(sql, params)
        conn.commit()

        sample_id = 1  # first sample

        sample = self.data_source.find_sample_by_customer_sample_name(
            customer, name)

        self.assertEqual(customer, sample.get_customer())
        self.assertEqual(name, sample.get_name())
        self.assertEqual(sample_id, sample.get_sample_id())
        self.assertEqual(tag, sample.get_tag())

    def test_find_sample_tube_by_barcode(self):
        conn = self.data_source.get_conn()
        sql = "insert into sample (customer, name, tag) values (?, ?, ?)"
        customer = 'customer1'
        name = 'sample1'
        tag = 'CAT'
        params = (customer, name, tag)
        conn.execute(sql, params)

        barcode = 'NT00001'
        sample_id = 1  # first sample

        sql = "insert into sample_tube (barcode, sample_id) values (?, ?)"
        params = (barcode, sample_id)
        conn.execute(sql, params)

        tube = self.data_source.find_sample_tube_by_barcode(barcode)
        sample = tube.get_sample()
        self.assertEqual(barcode, tube.get_barcode())
        self.assertEqual(customer, sample.get_customer())
        self.assertEqual(name, sample.get_name())
        self.assertEqual(sample_id, sample.get_sample_id())
        self.assertEqual(tag, sample.get_tag())

    def test_find_lab_tube_by_barcode(self):
        conn = self.data_source.get_conn()
        sql = "insert into sample (customer, name, tag) values (?, ?, ?)"
        customer = 'customer1'
        name = 'sample1'
        tag = 'CAT'
        params = (customer, name, tag)
        conn.execute(sql, params)

        barcode = 'NT00001'
        sample_id = 1  # first record

        sql = "insert into lab_tube (barcode, sample_id) values (?, ?)"
        params = (barcode, sample_id)
        conn.execute(sql, params)

        tube = self.data_source.find_lab_tube_by_barcode(barcode)
        sample = tube.get_sample()
        self.assertEqual(barcode, tube.get_barcode())
        self.assertEqual(customer, sample.get_customer())
        self.assertEqual(name, sample.get_name())
        self.assertEqual(sample_id, sample.get_sample_id())
        self.assertEqual(tag, sample.get_tag())

    def test_create_sample_tube(self):
        sample = Sample('customer1', 'sample1')
        tube = SampleTube('NT12345', sample)
        sample_id = 1  # expected

        # The following sets sample_id on the Sample of the Tube we pass.
        self.data_source.begin_transaction()
        self.data_source.create_sample_tube(tube)
        self.data_source.commit_transaction()

        # Records were created together.
        sql = ("select customer, name, s.sample_id, tag, barcode "
               "from sample s, sample_tube t "
               "where s.sample_id = t.sample_id and barcode = ?")
        params = (tube.get_barcode(),)
        conn = self.data_source.get_conn()
        result = conn.execute(sql, params).fetchall()

        self.assertEqual(1, len(result))

        customer, name, sample_id, tag, barcode = result[0]

        self.assertEqual(customer, sample.get_customer())
        self.assertEqual(name, sample.get_name())
        self.assertEqual(sample_id, sample.get_sample_id())
        self.assertEqual(tag, sample.get_tag())
        self.assertEqual(barcode, tube.get_barcode())

    def test_create_lab_tube(self):
        # Receive sample from customer.
        sample = Sample('customer1', 'sample1')
        sample_tube = SampleTube('NT12345', sample)

        self.data_source.begin_transaction()
        self.data_source.create_sample_tube(sample_tube)
        self.data_source.commit_transaction()

        # Add sample to LabTube
        barcode = 'NT55555'
        lab_tube = LabTube(barcode, sample)

        self.data_source.begin_transaction()
        self.data_source.create_lab_tube(lab_tube)
        self.data_source.commit_transaction()

        # Look into the database.
        conn = self.data_source.get_conn()
        sql = """select barcode, sample_id from lab_tube where barcode = ?"""
        params = (barcode,)
        result = conn.execute(sql, params).fetchall()

        self.assertEqual(1, len(result))

        barcode, sample_id = result[0]

        self.assertEqual(barcode, lab_tube.get_barcode())
        self.assertEqual(sample_id, lab_tube.get_sample().get_sample_id())

    def test_move_sample_between_sample_tubes(self):
        # Receive sample from customer.
        sample = Sample('customer1', 'sample1')
        source = SampleTube('NT12345', sample)

        self.data_source.begin_transaction()
        self.data_source.create_sample_tube(source)
        self.data_source.commit_transaction()

        # Move sample to a new Sample tube.
        target = SampleTube('NT56789')

        self.data_source.begin_transaction()
        self.data_source.move_sample(source, target)
        self.data_source.commit_transaction()

        conn = self.data_source.get_conn()
        sql = "select barcode, sample_id from sample_tube where barcode = ?"

        params = (source.get_barcode(),)
        result = conn.execute(sql, params).fetchall()
        source_barcode, source_sample_id = result[0]

        params = (target.get_barcode(),)
        result = conn.execute(sql, params).fetchall()
        target_barcode, target_sample_id = result[0]

        self.assertEqual(source.get_moved_to(), target.get_barcode())
        self.assertEqual(source_barcode, source.get_barcode())
        self.assertEqual(target_barcode, target.get_barcode())
        self.assertIsNone(source_sample_id)
        self.assertEqual(target_sample_id, sample.get_sample_id())
        self.assertIsNone(source.get_sample())
        self.assertEqual(sample, target.get_sample())

    def test_move_sample_between_lab_tubes(self):
        sample = Sample('customer1', 'sample1')
        sample_tube = SampleTube('NT12345', sample)

        self.data_source.begin_transaction()
        self.data_source.create_sample_tube(sample_tube)
        self.data_source.commit_transaction()

        # Add sample to source LabTube
        barcode = 'NT55555'
        source = LabTube(barcode, sample)

        self.data_source.begin_transaction()
        self.data_source.create_lab_tube(source)
        self.data_source.commit_transaction()

        # Move sample from the source LabTube to a target LabTube
        target = SampleTube('NT56789')

        self.data_source.begin_transaction()
        self.data_source.move_sample(source, target)
        self.data_source.commit_transaction()

        conn = self.data_source.get_conn()

        sql = ("select barcode, sample_id, moved_to "
               "from lab_tube where barcode = ?")
        params = (source.get_barcode(),)
        result = conn.execute(sql, params).fetchall()
        source_barcode, source_sample_id, source_moved_to = result[0]

        sql = "select barcode, sample_id from lab_tube where barcode = ?"
        params = (target.get_barcode(),)
        result = conn.execute(sql, params).fetchall()
        target_barcode, target_sample_id = result[0]

        self.assertEqual(source_moved_to, target_barcode)
        self.assertEqual(source_barcode, source.get_barcode())
        self.assertEqual(target_barcode, target.get_barcode())
        self.assertIsNone(source_sample_id)
        self.assertEqual(target_sample_id, sample.get_sample_id())
        self.assertIsNone(source.get_sample())
        self.assertEqual(sample, target.get_sample())

    def test_find_plate_by_barcode(self):
        conn = self.data_source.get_conn()
        sql = "insert into sample (customer, name) values (?, ?)"
        customer = 'customer1'
        name = 'sample1'
        params = customer, name
        conn.execute(sql, params)

        sql = "insert into plate (barcode, grid) values (?, ?)"
        plate_barcode = 'DN12345'
        grid = '8x12'
        params = plate_barcode, grid
        conn.execute(sql, params)

        sql = ("insert into well(plate_barcode, label, sample_id) "
               "values (?, ?, ?)")
        label = 'A1'
        sample_id = 1
        params = plate_barcode, label, 1
        conn.execute(sql, params)

        conn.commit()

        plate = self.data_source.find_plate_by_barcode(plate_barcode)
        well = plate.get_wells()[0]
        sample = well.get_sample()

        self.assertEqual(plate_barcode, plate.get_barcode())
        self.assertEqual(grid, plate.get_grid())
        self.assertEqual(customer, sample.get_customer())
        self.assertEqual(name, sample.get_name())
        self.assertEqual(sample_id, sample.get_sample_id())

    def test_update_sample_tag(self):
        sample = Sample('customer1', 'sample1')
        tube = SampleTube('NT12345', sample)

        self.data_source.begin_transaction()
        self.data_source.create_sample_tube(tube)
        self.data_source.commit_transaction()

        tag = 'CAT'
        self.data_source.begin_transaction()
        self.data_source.update_sample_tag(sample, tag)
        self.data_source.commit_transaction()

        sql = ("select customer, name, sample_id, tag from sample "
               "where sample_id = ?")
        params = (sample.get_sample_id(),)
        conn = self.data_source.get_conn()
        result = conn.execute(sql, params).fetchall()
        customer, name, sample_id, tag2 = result[0]

        self.assertEqual(tag, sample.get_tag())
        self.assertEqual(tag2, sample.get_tag())

    def test_create_plate(self):
        a1 = Well('A1', Sample('customer1', 'sample1', 1))
        a2 = Well('A2', Sample('customer1', 'sample2', 2))
        a3 = Well('A3', Sample('customer1', 'sample3', 3))
        wells = [a1, a3, a2]  # not sorted by label
        barcode = 'DN12345'
        grid = '8x12'
        plate = Plate(barcode, grid, wells)

        self.data_source.begin_transaction()
        self.data_source.create_plate(plate)
        self.data_source.commit_transaction()

        conn = self.data_source.get_conn()
        sql = "select barcode, grid from plate where barcode = ?"
        params = (barcode,)
        result = conn.execute(sql, params).fetchall()
        a_barcode, a_grid = result[0]

        self.assertEqual(barcode, a_barcode)
        self.assertEqual(grid, a_grid)

        sql = ("select plate_barcode, label, sample_id from well "
               "where plate_barcode = ? order by sample_id")
        params = (barcode,)
        result = conn.execute(sql, params).fetchall()
        wells = plate.get_wells()
        for i in range(len(result)):
            row = result[i]
            well = wells[i]
            self.assertEqual(barcode, row[0])
            self.assertEqual(well.get_label(), row[1])
            self.assertEqual(well.get_sample().get_sample_id(), row[2])

    def test_create_well(self):
        conn = self.data_source.get_conn()
        sql = "insert into sample (customer, name) values (?, ?)"
        customer = 'customer1'
        name = 'sample1'
        params = customer, name
        sample_id = conn.execute(sql, params).lastrowid

        sql = "insert into plate (barcode, grid) values (?, ?)"
        params = barcode, grid = 'DN12345', '8x12'
        conn.execute(sql, params)
        conn.commit()

        sample = self.data_source.find_sample_by_sample_id(sample_id)
        plate = self.data_source.find_plate_by_barcode(barcode)
        label = 'A1'
        well = Well(label, sample)
        self.data_source.create_well(plate, well)

        sql = ("select plate_barcode, label, sample_id from well "
               "where plate_barcode = ?")
        params = (barcode,)
        result = conn.execute(sql, params).fetchall()
        a_barcode, a_label, a_sample_id = result[0]

        self.assertEqual(barcode, a_barcode)
        self.assertEqual(label, a_label)
        self.assertEqual(sample_id, a_sample_id)

    def test_find_tube_by_barcode_no_sample(self):
        kind = 'sample_tube'
        sql = "insert into %s (barcode, sample_id) values (?, ?)" % kind
        barcode, sample_id = 'NT12345', None
        params = (barcode, sample_id)
        conn = self.data_source.get_conn()
        conn.execute(sql, params)
        conn.commit()

        tube = self.data_source.find_tube_by_kind_barcode(kind, barcode)

        self.assertIsNone(tube.get_sample())

    def test_create_sample_tube_rollback(self):
        customer = 'customer1'
        name = None  # This causes exception and we rollback the transaction.
        barcode = 'NT12345'
        sample = Sample(customer, name)
        tube = SampleTube(barcode, sample)

        self.data_source.begin_transaction()
        try:
            self.data_source.create_sample_tube(tube)
        except Exception:
            self.data_source.rollback_transaction()  # Rollback!
        else:
            self.fail(
                "Expected an integrity error (sample name cannot be null).")

        self.assertIsNone(sample.get_sample_id())  # Not assigned.

        recorded = self.data_source.find_sample_by_customer_sample_name(
            customer, name)
        self.assertIsNone(recorded)  # Not recorded.

        recorded = self.data_source.find_sample_tube_by_barcode(barcode)
        self.assertIsNone(recorded)  # Not recorded.
