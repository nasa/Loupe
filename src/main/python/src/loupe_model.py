import os

from SPAR.build.python import Spar
from src import SPAR_access

# Model
# Create a Model to handle the SPAR operations and data access
def LoupeAccess(selectedSOFFFilename):
    SPARsys = Spar.SparSystem.create(Spar.PrintAndAbort)
    prod = Spar.SparProduct.createProduct(SPARsys, selectedSOFFFilename)
    ret = prod.open()
    dimensionClassDict = {}
    dimensionDict = {}
    for i, dim in enumerate(prod.getDimensions()):
        d = SPAR_access.dimensionProperties(dim)
        if d.dimClass not in dimensionClassDict.keys():
            dimensionClassDict[d.dimClass] = []
        dimensionClassDict[d.dimClass].append(d.dimID)
        dimensionDict[d.dimID] = {'class': d.dimClass, 'name': d.dimName, 'comment': d.dimComment, 'size': d.dimSize, 'index': i}

    tableDict = {}
    for i, tab in enumerate(prod.getTables()):
        t = SPAR_access.tableProperties(tab)
        tableDict[t.tabName] = {'n_dimensions': t.tabNDim, 'dimensions': [dim for dim in t.tabDims], 'size': t.tabSize, 'index': i, 'dimension_ids': [ID for ID in t.tabDimIDs]}

    fileNames = []
    for i in range(prod.getNumLocalFiles()):
        fileNames.append(prod.getLocalFile(i).getFilename())

    return dimensionClassDict, dimensionDict, tableDict, fileNames, prod
