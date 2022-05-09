import unittest

from string import ascii_uppercase

from pylims.lab import Sample, Container, Tube, SampleTube, LabTube, Plate, Well


class LabTest(unittest.TestCase):

    def test_sample_init(self):
        customer = 'customer1'
        name = 'sample1'
        sample_id = 1
        tag = 'CAT'
        concentration = 50  # 50 <= x <=200
        sample = Sample(customer, name, sample_id, tag, concentration)

        self.assertEqual(customer, sample.get_customer())
        self.assertEqual(name, sample.get_name())
        self.assertEqual(sample_id, sample.get_sample_id())
        self.assertEqual(tag, sample.get_tag())
        self.assertEqual(concentration, sample.get_concentration())

    def test_customer_sample_name(self):
        sample = Sample()
        unique = 'customer1' + Sample.name_delimiter + 'sample1'
        customer, name = unique.split('-')
        sample.set_customer_sample_name(unique)

        self.assertEqual(customer, sample.get_customer())
        self.assertEqual(name, sample.get_name())
        self.assertEqual(unique, sample.get_customer_sample_name())

    def test_sample_tag(self):
        tag = 'CAT'
        sample = Sample()
        sample.set_tag(tag)

        self.assertEqual(tag, sample.get_tag())

    def test_sample_id(self):
        sample_id = 1
        sample = Sample()
        sample.set_sample_id(sample_id)

        self.assertEqual(sample_id, sample.get_sample_id())

    def test_sample_validate_tag_format(self):
        tag = 'CAT'  # DNA
        self.assertTrue(Sample.validate_tag_format(tag))

        tag = 'DOG'  # not DNA
        self.assertFalse(Sample.validate_tag_format(tag))

        tag = 'ATGC ATGC'  # space in middle
        self.assertFalse(Sample.validate_tag_format(tag))

        tag = ' ATGC'  # preceding space
        self.assertFalse(Sample.validate_tag_format(tag))

        tag = 'ATGC '  # following space
        self.assertFalse(Sample.validate_tag_format(tag))

    def test_validate_concentration(self):
        value = 0
        self.assertFalse(Sample.validate_concentration(value))

        value = 50
        self.assertTrue(Sample.validate_concentration(value))

        value = 200
        self.assertTrue(Sample.validate_concentration(value))

        value = -1
        self.assertFalse(Sample.validate_concentration(value))

        value = 201
        self.assertFalse(Sample.validate_concentration(value))

        value = 'NOT A NUMBER'
        self.assertFalse(Sample.validate_concentration(value))

    def test_sample_validate_customer_sample_name_format(self):
        name = 'customer1' + Sample.name_delimiter + ' sample1'  # complete
        self.assertTrue(Sample.validate_customer_sample_name_format(name))

        name = 'customer1'  # partial
        self.assertFalse(Sample.validate_customer_sample_name_format(name))

        name = 'sample1'  # partial
        self.assertFalse(Sample.validate_customer_sample_name_format(name))

        name = 'customer sample'  # no delimiter
        self.assertFalse(Sample.validate_customer_sample_name_format(name))

    def test_sample_split_customer_sample_name(self):
        name = 'customer1' + Sample.name_delimiter + 'sample1'
        expected = name.split(Sample.name_delimiter, 1)
        Sample.split_customer_sample_name(name)

        self.assertEqual(expected, Sample.split_customer_sample_name(name))

    def test_container_init(self):
        barcode = 'DN00001'
        base = Container(barcode)

        self.assertEqual(barcode, base.get_barcode())

    def test_tube_init(self):
        barcode = 'NT000001'
        sample = Sample('customer1', 'sample1', 1, 'ATTGGCAT')
        tube = Tube(barcode, sample)

        self.assertEqual(barcode, tube.get_barcode())
        self.assertEqual(sample, tube.get_sample())

    def test_tube_validate_barcode_format(self):
        self.assertEqual('NT', Tube.barcode_prefix)

        barcode = 'NT00001'  # OK
        self.assertTrue(Tube.validate_barcode_format(barcode))

    def test_tube_validate_barcode_format_overflow(self):
        barcode = 'NT99999'  # format max barcode places
        self.assertTrue(Tube.validate_barcode_format(barcode))

        barcode = 'NT123456'  # overflow; 6 places
        self.assertTrue(Tube.validate_barcode_format(barcode))

    def test_tube_validate_barcode_format_bad_prefix(self):
        barcode = '00001'  # no prefix
        self.assertFalse(Tube.validate_barcode_format(barcode))

        barcode = 'XX00001'  # bad prefix
        self.assertFalse(Tube.validate_barcode_format(barcode))

    def test_tube_validate_barcode_format_bad_number(self):
        barcode = 'NT000X1'  # bad number
        self.assertFalse(Tube.validate_barcode_format(barcode))

        barcode = 'NT00000'  # zero
        self.assertFalse(Tube.validate_barcode_format(barcode))

        barcode = 'NT1'  # no zero-padding
        self.assertFalse(Tube.validate_barcode_format(barcode))

    def test_tube_validate_barcode_format_spaces(self):
        barcode = 'NT12 345'  # space in middle
        self.assertFalse(Tube.validate_barcode_format(barcode))

        barcode = ' NT12345'  # preceding space
        self.assertFalse(Tube.validate_barcode_format(barcode))

        barcode = ' NT12345 '  # following space
        self.assertFalse(Tube.validate_barcode_format(barcode))

    def test_sample_tube_init(self):
        barcode = 'NT00001'
        sample = Sample('customer1', 'sample1', 1, 'ATTGGCAT')
        tube = SampleTube(barcode, sample)

        self.assertEqual(barcode, tube.get_barcode())
        self.assertEqual(sample, tube.get_sample())

    def test_sample_tube_moved(self):
        barcode = 'NT00001'
        sample = Sample('customer1', 'sample1', 1, 'ATTGGCAT')
        source = SampleTube(barcode, sample)

        target_barcode = 'NT00002'
        source.set_sample(None)
        source.set_moved_to(target_barcode)

        self.assertEqual(target_barcode, source.get_moved_to())
        self.assertTrue(source.is_discarded())

    def test_lab_tube_init(self):
        barcode = 'NT00001'
        sample = Sample('customer1', 'sample1', 1, 'ATTGGCAT')
        tube = LabTube(barcode, sample)

        self.assertEqual(barcode, tube.get_barcode())
        self.assertEqual(sample, tube.get_sample())

    def test_plate_init_barcode(self):
        barcode = 'DN12345'
        plate = Plate(barcode)

        self.assertEqual('8x12', Plate.default_grid)
        self.assertEqual(barcode, plate.get_barcode())
        self.assertEqual(Plate.default_grid, plate.get_grid())
        self.assertListEqual([], plate.get_wells())

    def test_plate_init_barcode_grid_96(self):
        barcode = 'DN12345'
        grid = '8x12'
        plate = Plate(barcode, grid)

        self.assertEqual(barcode, plate.get_barcode())
        self.assertEqual(grid, plate.get_grid())
        self.assertListEqual([], plate.get_wells())

    def test_plate_init_barcode_grid_384(self):
        barcode = 'DN12345'
        grid = '16x24'
        plate = Plate(barcode, grid)

        self.assertEqual(barcode, plate.get_barcode())
        self.assertEqual(grid, plate.get_grid())
        self.assertListEqual([], plate.get_wells())

    def test_plate_init_barcode_grid_wells(self):
        a1 = Well('A1', Sample('customer1', 'sample1', 1))
        a2 = Well('A2', Sample('customer1', 'sample2', 2))
        a3 = Well('A3', Sample('customer1', 'sample3', 3))
        wells = [a1, a3, a2]  # not sorted by label
        barcode = 'DN12345'
        grid = '8x12'
        plate = Plate(barcode, grid, wells)

        self.assertEqual(barcode, plate.get_barcode())
        self.assertEqual(grid, plate.get_grid())
        self.assertListEqual([a1, a2, a3], plate.get_wells())  # sorted

    def test_plate_add_well(self):
        a1 = Well('A1', Sample('customer1', 'sample1', 1))
        a3 = Well('A3', Sample('customer1', 'sample3', 3))
        wells = [a3, a1]
        barcode = 'DN12345'
        plate = Plate(barcode, wells=wells)

        self.assertEqual(barcode, plate.get_barcode())
        self.assertEqual(Plate.default_grid, plate.get_grid())
        self.assertListEqual([a1, a3], plate.get_wells())

        a2 = Well('A2', Sample('customer1', 'sample2', 2))
        plate.add_well(a2)

        self.assertListEqual([a1, a2, a3], plate.get_wells())

    def test_plate_well_in_range(self):
        barcode = 'DN12345'
        grid = '8x12'
        plate = Plate(barcode, grid)

        label = 'A1'
        self.assertTrue(plate.well_in_range(label))

        label = 'E6'
        self.assertTrue(plate.well_in_range(label))

        label = 'H12'
        self.assertTrue(plate.well_in_range(label))

    def test_plate_well_in_range_outside(self):
        barcode = 'DN12345'
        grid = '8x12'
        plate = Plate(barcode, grid)

        label = 'A0'
        self.assertFalse(plate.well_in_range(label))

        label = 'H13'
        self.assertFalse(plate.well_in_range(label))

    def test_well_is_empty(self):
        a1 = Well('A1', Sample('customer1', 'sample1', 1))
        a2 = Well('A2', Sample('customer1', 'sample2', 2))
        a3 = Well('A3', Sample('customer1', 'sample3', 3))
        wells = [a1, a3, a2]  # not sorted by label
        barcode = 'DN12345'
        grid = '8x12'
        plate = Plate(barcode, grid, wells)

        label = 'A3'
        self.assertFalse(plate.well_is_empty(label))

        label = 'B1'
        self.assertTrue(plate.well_is_empty(label))



    def test_validate_well_label_format(self):
        label = 'A1'
        self.assertTrue(Plate.validate_well_label_format(label))

        label = 'H12'
        self.assertTrue(Plate.validate_well_label_format(label))

        label = 'P24'  # 384-well, 16x24, A1 to P24
        self.assertTrue(Plate.validate_well_label_format(label))

    def test_validate_well_label_format_outside(self):
        label = 'Z1'
        self.assertFalse(Plate.validate_well_label_format(label))

        label = None
        self.assertFalse(Plate.validate_well_label_format(label))

    def test_validate_well_label_format_bad_letter(self):
        label = '_1'
        self.assertFalse(Plate.validate_well_label_format(label))

        label = ' 1'
        self.assertFalse(Plate.validate_well_label_format(label))

    def test_validate_well_label_format_bad_number(self):
        label = 'A '
        self.assertFalse(Plate.validate_well_label_format(label))

        label = 'A?'
        self.assertFalse(Plate.validate_well_label_format(label))

    def test_well_init(self):
        label = 'A1'
        sample = Sample('customer1', 'sample1', 1)
        well = Well(label, sample)

        self.assertEqual(label, well.get_label())
        self.assertEqual(sample, well.get_sample())

    def test_well_init_label(self):
        label = 'A1'
        well = Well(label)

        self.assertEqual(label, well.get_label())
        self.assertIsNone(well.get_sample())

    def test_well_sample(self):
        label = 'A1'
        sample = Sample('customer1', 'sample1', 1)
        well = Well(label)
        well.set_sample(sample)

        self.assertEqual(sample, well.get_sample())

    def test_get_split_label(self):
        label = 'A1'
        expected = label[0], int(label[1:])
        well = Well(label)
        self.assertEqual(expected, well.get_split_label())

    def test_well_less_than(self):
        a1 = Well('A1', Sample('customer1', 'sample1', 1))
        a2 = Well('A2', Sample('customer1', 'sample2', 2))

        self.assertLess(a1, a2)

    def test_sample_str(self):
        sample = Sample('customer1', 'sample1', '1')
        expected = ["Sample: Sample Id: %s" % sample.get_sample_id()]
        expected.append("Customer sample name: %s" %
                        sample.get_customer_sample_name())
        expected = ', '.join(expected)
        actual = str(sample)

        self.assertEqual(expected, actual)

    def test_sample_str_with_tag(self):
        sample = Sample('customer1', 'sample1', '1', 'ACTG')
        expected = ["Sample: Sample Id: %s" % sample.get_sample_id()]
        expected.append("Customer sample name: %s" %
                        sample.get_customer_sample_name())
        expected.append('Tag: %s' % sample.get_tag())
        expected = ', '.join(expected)
        actual = str(sample)
        self.assertEqual(expected, actual)

    def test_tube_str(self):
        tube = SampleTube('NT12345')
        expected = "Sample tube: Barcode: %s" % tube.get_barcode()

        self.assertEqual(expected, str(tube))

    def test_tube_str_with_sample(self):
        sample = Sample('customer1', 'sample1', '1')
        tube = SampleTube('NT12345', sample)
        expected = ["Sample tube: Barcode: %s" % tube.get_barcode()]
        expected.append("Sample Id: %s" % sample.get_sample_id())
        expected.append('Customer sample name: %s' %
                        sample.get_customer_sample_name())
        expected = ', '.join(expected)
        self.assertEqual(expected, str(tube))

    def test_tube_str_with_tag(self):
        sample = Sample('customer1', 'sample1', '1', 'ACGT')
        tube = SampleTube('NT12345', sample)
        expected = ["Sample tube: Barcode: %s" % tube.get_barcode()]
        expected.append("Sample Id: %s" % sample.get_sample_id())
        expected.append('Customer sample name: %s' %
                        sample.get_customer_sample_name())
        expected.append('Tag: %s' % sample.get_tag())
        expected = ', '.join(expected)
        self.assertEqual(expected, str(tube))

    def test_tube_str_moved(self):
        tube = SampleTube('NT12345')
        tube.set_moved_to('NT54321')
        expected = ["Sample tube: Barcode: %s" % tube.get_barcode()]
        expected.append('Sample moved to: %s' % tube.get_moved_to())
        expected = ', '.join(expected)
        self.assertEqual(expected, str(tube))

    def test_plate_str(self):
        sample = Sample('customer1', 'sample1', 1, 'CAT')
        well = Well('A1', sample)
        wells = [well]
        plate = Plate('DN12345', wells=wells)

        expected = ['Plate: Barcode: %s, Grid: %s' %
                 (plate.get_barcode(), plate.get_grid())]
        args = (well.get_label(), sample.get_sample_id(),
                sample.get_customer_sample_name(), sample.get_tag())
        expected.append(('Well: Label: %s, Sample Id: %s, '
                     'Customer sample name: %s, Tag: %s') % args)

        expected = '\n'.join(expected)
        self.assertEqual(expected, str(plate))

    def test_container_str(self):
        container = Container('XX12345')
        expected = "Container: Barcode: %s" % container.get_barcode()

        self.assertEqual(expected, str(container))

    def test_plate_is_full(self):
        plate = Plate('DN12345')
        sample = Sample('customer1', 'sample1', 1)

        self.assertFalse(plate.is_full())

        nrows, ncolumns = plate.get_grid_rows_columns()
        for i in range(nrows):
            for j in range(ncolumns):
                label = '%s%s' % (ascii_uppercase[i], j + 1)
                well = Well(label, sample)
                plate.add_well(well)

        self.assertTrue(plate.is_full())
