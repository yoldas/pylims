import os
import unittest

from pylims import config
from pylims.dba import DataSet


class DataSetTest(unittest.TestCase):

    def test_delegate(self):
        conf = config.test_database

        dataset = DataSet(conf)
        data_source = dataset.get_data_source()

        # Test delegation: dataset.method -> data_source.method
        source = dataset.find_sample_by_customer_sample_name
        target = data_source.find_sample_by_customer_sample_name

        self.assertEqual(source, target)

    def test_data_source_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            conf = dict(engine='X')  # engine not supported; no DataSource impl.
            dataset = DataSet(conf)  # throws exception

    def test_default_conf(self):
        dataset = DataSet()  # default connection to app database.
        self.assertDictEqual(dataset.get_conf(), config.database)
