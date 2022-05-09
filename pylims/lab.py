"""Labware"""

import bisect
import string
import re


class Sample:
    """Sample DNA."""
    name_delimiter = '-'  # between customer and sample name used by customer
    tag_re = re.compile('^[ATGC]+$')  # DNA regex

    def __init__(self, customer=None, name=None, sample_id=None, tag=None,
                 concentration=None):
        """Initialises a Sample using sample attributes."""
        self._customer = customer
        self._name = name
        self._sample_id = sample_id
        self._tag = tag
        self._concentration = concentration

    def __str__(self):
        """Returns string representation of the Sample."""
        lines = ["Sample: Sample Id: %s" % self.get_sample_id(),
                 "Customer sample name: %s" % self.get_customer_sample_name()]
        tag = self.get_tag()
        if tag:
            lines.append('Tag: %s' % tag)
        value = self.get_concentration()
        if value is not None:
            lines.append('Concentration: %s' % value)
        return ', '.join(lines)

    def get_customer(self):
        """Returns customer name."""
        return self._customer

    def get_name(self):
        """Returns sample name used by customer."""
        return self._name

    def get_sample_id(self):
        """Returns unique Sanger Id."""
        return self._sample_id

    def set_sample_id(self, sample_id):
        """Sets the unique sample_id."""
        self._sample_id = sample_id

    def get_tag(self):
        """Returns tag"""
        return self._tag

    def set_tag(self, tag):
        """Sets tag sequence. """
        self._tag = tag

    def get_customer_sample_name(self):
        """Returns customer sample name"""
        return self._customer + self.name_delimiter + self._name

    def set_customer_sample_name(self, customer_sample_name):
        """Sets customer and sample name used by customer."""
        self._customer, self._name = customer_sample_name.split('-', 1)

    @classmethod
    def validate_tag_format(cls, tag):
        """Returns True if the format of tag is valid.
        The tag must be made of only the letters A, C, G and T.
        """
        if cls.tag_re.match(tag):
            return True
        return False

    @classmethod
    def validate_concentration(cls, value):
        """Returns True if concentration value is acceptable."""
        try:
            value = int(value)
        except ValueError:
            return False
        if 50 <= value <= 200:
            return True
        return False


    @classmethod
    def validate_customer_sample_name_format(cls, name):
        """Returns True of the format of customer sample name is valid.
        The name must be composed of customer and sample name used by customer
        delimited by name delimiter.
        """
        parts = name.split('-', 1)
        if len(parts) == 2:
            return True
        return False

    @classmethod
    def split_customer_sample_name(cls, name):
        """Splits name into customer and sample name used by customer."""
        return name.split('-', 1)

    def get_concentration(self):
        return self._concentration

    def set_concentration(self, value):
        self._concentration = value


class Container:
    """Represents a unique container for Sample."""
    barcode_prefix = None  # Must be set in child.
    barcode_places = 5  # For number formatting in barcode.

    def __init__(self, barcode):
        """Initialises Container with barcode."""
        self._barcode = barcode

    def __str__(self):
        """Returns string representation of this Container."""
        return "%s: Barcode: %s" % (self.__class__.__name__, self.get_barcode())

    def get_barcode(self):
        """Returns the barcode of this Container."""
        return self._barcode

    @classmethod
    def validate_barcode_format(cls, barcode):
        """Returns True if the format of barcode is valid."""
        if barcode.startswith(cls.barcode_prefix):  # Starts with correct prefix
            sequence = barcode[len(cls.barcode_prefix):]
            if sequence.isdigit():  # Followed by digits
                number = int(sequence)  # Evaluates into a number
                if number > 0:  # Greater than zero
                    temp = cls.barcode_prefix + '%0' + str(
                        cls.barcode_places) + 'd'
                    formatted = temp % number
                    # Padded with zeros in barcode places
                    if formatted == barcode:
                        return True
        return False


class Tube(Container):
    """Represents a tube."""
    barcode_prefix = 'NT'

    def __init__(self, barcode, sample=None):
        """Initialises the Tube with barcode and Sample."""
        super().__init__(barcode)
        self._sample = sample  # contains a sample
        self._moved_to = None  # sample moved to new barcode

    def __str__(self):
        """Returns string representation of the Tube."""
        parts = []

        name = self.__class__.__name__
        i = name.find('Tube')
        name = name[:i] + ' ' + name[i:].lower()

        part = "%s: Barcode: %s" % (name, self.get_barcode())
        parts.append(part)
        sample = self.get_sample()
        if sample:
            parts.append('Sample Id: %s' % sample.get_sample_id())
            parts.append('Customer sample name: %s' %
                         sample.get_customer_sample_name())
            tag = sample.get_tag()
            if tag:
                parts.append('Tag: %s' % tag)
        if self.get_moved_to():
            parts.append('Sample moved to: %s' % self.get_moved_to())
        return ', '.join(parts)

    def get_sample(self):
        """Returns the Sample of this Tube."""
        return self._sample

    def set_sample(self, sample):
        """Sets the Sample of this Tube."""
        self._sample = sample

    def is_discarded(self):
        """Returns True if the Sample was transferred to another Tube."""
        return self.get_moved_to() and not self.get_sample()

    def set_moved_to(self, barcode):
        """Sets barcode of the Tube where the Sample was transferred to."""
        self._moved_to = barcode

    def get_moved_to(self):
        """Returns the barcode of the Tube where the Sample was transferred to.
        """
        return self._moved_to


class SampleTube(Tube):
    """Represents a tube that holds customer Sample."""
    pass


class LabTube(Tube):
    """Represents a tube where Sample is added."""
    pass


class Plate(Container):
    """Represents a plate, which has wells where samples are added."""
    barcode_prefix = 'DN'
    default_grid = "8x12"  # default is 96 wells; 8 rows and 12 columns.

    def __init__(self, barcode, grid=None, wells=None):
        """Initialises a Plate using the barcode, grid size, and wells that
        contain Samples."""
        super().__init__(barcode)
        if grid is None:
            grid = self.default_grid
        self._grid = grid
        wells = wells or []
        # Sort wells by label; rows and then columns
        wells.sort(key=lambda x: x.get_split_label())
        self._wells = wells  # Wells that contain Samples

    def __str__(self):
        """Returns string representation of this Plate and its Wells."""
        lines = []
        line = "%s: Barcode: %s, Grid: %s" % (
            self.__class__.__name__, self.get_barcode(), self.get_grid())
        lines.append(line)
        for well in self.get_wells():
            line = '%s' % well
            lines.append(line)
        return '\n'.join(lines)

    def get_wells(self):
        """Returns Wells of this Plate."""
        return self._wells

    def add_well(self, well):
        """Adds a Well that contains Sample to this Plate."""
        # Python < 3.10 does not support key argument to bisect.insort
        bisect.insort(self._wells, well)  # uses Well.__lt__

    def well_in_range(self, label):
        """Returns True if the Well position on the Plate."""
        rows, columns = self.get_grid_rows_columns()
        min_pos = 'A', 1
        max_pos = string.ascii_uppercase[rows - 1], columns

        pos = self.split_well_label(label)

        if (min_pos[0] <= pos[0] <= max_pos[0] and
                min_pos[1] <= pos[1] <= max_pos[1]):
            return True

        return False

    def well_is_empty(self, label):
        """Returns True if the Well specified by label has Sample."""
        for well in self.get_wells():
            if well.get_label() == label:
                return False
        return True

    def get_grid(self):
        """Returns grid size."""
        return self._grid

    def get_grid_rows_columns(self):
        """Returns a tuple of number of rows and number columns."""
        rows, columns = self.get_grid().split('x')
        return int(rows), int(columns)

    def is_full(self):
        """Returns True if all Plate Wells contain Samples."""
        capacity = self.get_capacity()
        if len(self.get_wells()) >= capacity:
            return True
        return False

    def get_capacity(self):
        """Returns the maximum number of Wells (rows x columns)"""
        nrows, ncolumns = self.get_grid_rows_columns()
        return nrows * ncolumns

    @classmethod
    def validate_well_label_format(cls, label):
        """Returns True if the Well label format is valid. Label must start
        with a letter for the row, followed by a number for the column to
        specify the position on the Plate."""
        if label:
            letter, number = label[0], label[1:]
            if letter.isalpha() and number.isdigit():
                if 'A' <= letter <= 'P' and 1 <= int(number) <= 24:
                    return True  # 384-well, 16x24, A1 to P24
        return False

    @classmethod
    def split_well_label(cls, label):
        """Splits label into row letter and column number."""
        return label[0], int(label[1:])


class Well:
    """Represents a location on a Plate to add Sample."""

    def __init__(self, label, sample=None):
        """Initialises Well using label and Sample."""
        self._label = label
        self._sample = sample

    def __lt__(self, other):
        """Returns True if the position of this Well is smaller than the other.
        This operator is used for sorting the Wells, rows and then columns.
        """
        return self.get_split_label() < other.get_split_label()

    def __str__(self):
        """Returns string representation of this Well."""
        parts = []
        part = "%s: Label: %s" % (self.__class__.__name__, self.get_label())
        parts.append(part)
        sample = self.get_sample()
        if sample:
            part = 'Sample Id: %s' % sample.get_sample_id()
            parts.append(part)
            part = ('Customer sample name: %s' %
                    sample.get_customer_sample_name())
            parts.append(part)
            if sample.get_tag():
                part = 'Tag: %s' % sample.get_tag()
                parts.append(part)
        return ', '.join(parts)

    def get_label(self):
        """Returns the label of this Well."""
        return self._label

    def set_sample(self, sample):
        """Sets the Sample of this Well."""
        self._sample = sample

    def get_sample(self):
        """Returns the Sample of this Well."""
        return self._sample

    def get_split_label(self):
        """Splits the Well label into row letter and column number."""
        return self._label[0], int(self._label[1:])
