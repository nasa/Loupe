

class SoffClassTable():
    def __init__(self):
        self.filename = None
        self.lid = None
        self.byteOffset = None
        self.records = None
        self.fieldsMain = None
        self.groups = None
        self.groupsRepeititions = None
        self.groupsFields = None
        self.fieldNames = None
        self.dataType = None

    def table_define(self, filename = '', lid = '', byte_offset = 0, records = 0, fields_main = 0, groups = 0, groups_repetitions = 0, groups_fields = 0, groups_groups = 0, field_names = [], data_type = []):
        self.filename = filename
        self.lid = lid
        self.byteOffset = byte_offset
        self.records = records
        self.fieldsMain = fields_main
        self.groups = groups
        self.groupsRepititions = groups_repetitions
        self.groupsFields = groups_fields
        self.groupsGroups = groups_groups
        self.fieldNames = field_names
        self.dataType = data_type


class SoffClassDimension():
    def __init__(self):
        self.soff_class = None
        self.comment = None
        self.elements = None
        self.lid = None

    def dimension_define(self, soff_class='', comment='', elements='', lid=''):
        self.soffClass = soff_class
        self.comment = comment
        self.elements = elements
        self.lid = lid


class SoffClassSoffTable():
    def __init__(self):
        self.name = None
        self.dimensionLID = None
        self.tableLID = None
        self.description = None


    def dataTable_define(self, name = '', dimensionLID = [], tableLID = '', description = ''):
        self.name = name
        self.dimensionLID = dimensionLID
        self.tableLID = tableLID
        self.description = description
