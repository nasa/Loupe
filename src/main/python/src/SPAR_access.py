from SPAR.build.python import Spar

# Model
# Create a Model to handle the SPAR operations and data access
def SPARaccess(tableFilename):
    SPARsys = Spar.SparSystem.create(Spar.PrintAndAbort)
    prod = Spar.SparProduct.createProduct(SPARsys, tableFilename)
    ret = prod.open()
    dimensionClassDict = {}
    dimensionDict = {}
    for i, dim in enumerate(prod.getDimensions()):
        d = dimensionProperties(dim)
        if d.dimClass not in dimensionClassDict.keys():
            dimensionClassDict[d.dimClass] = []
        dimensionClassDict[d.dimClass].append(d.dimID)
        dimensionDict[d.dimID] = {'class': d.dimClass, 'name': d.dimName, 'comment': d.dimComment, 'size': d.dimSize, 'index': i}

    tableDict = {}
    for i, tab in enumerate(prod.getTables()):
        t = tableProperties(tab)
        tableDict[t.tabName] = {'n_dimensions': t.tabNDim, 'dimensions': [dim for dim in t.tabDims], 'size': t.tabSize, 'index': i, 'dimension_ids': [ID for ID in t.tabDimIDs]}

    fileNames = []
    for i in range(prod.getNumLocalFiles()):
        fileNames.append(prod.getLocalFile(i).getFilename())

    return dimensionClassDict, dimensionDict, tableDict, fileNames, prod


# a class to hold all dimension property data
class dimensionProperties:
    def __init__(self, SparDim):
        self.dimClass = SparDim.getDimensionClass()
        self.dimName = SparDim.getName()
        self.dimComment = SparDim.getComment()
        self.dimSize = SparDim.getSize()
        self.dimID = SparDim.getID()

# a class to hold all table property data
class tableProperties:
    def __init__(self, SparTab):
        self.tabName = SparTab.getName()
        self.tabNDim = SparTab.getNumDimensions()
        self.tabDims = []
        self.tabDimIDs = []
        self.tabSize = []
        for i in range(self.tabNDim):
            self.tabDims.append(SparTab.getDimensions()[i].getName())
            self.tabDimIDs.append(SparTab.getDimensions()[i].getID())
            self.tabSize.append(SparTab.getSize(i+1))


