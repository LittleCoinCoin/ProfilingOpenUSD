from pxr import Usd, UsdGeom
import random as rd
from time import perf_counter_ns
import numpy as np
from general_IO import writer
from os import remove

def FromNPArrayToCSV(_npArr2, _filePath, _fileName, _headers=""):
    lines=[_headers]
    lines+=[("{}"+",{}"*(_npArr2.shape[1]-1)).format(*_npArr2[i]) for i in range (_npArr2.shape[0])]
    writer(_filePath, _fileName, lines, True)

def RandomVec3(_scale = (1,1,1)):
    return (_scale[0]*rd.random(), _scale[1]*rd.random(), _scale[2]*rd.random())

def AddRandomPlaceReferencesInStage(_USDStage, _path, _baseName, _refUSDFilePath, _refCount=10):
    basStr=_path+"/"+_baseName
    for i in range(_refCount):
        refCube = _USDStage.OverridePrim(basStr+"_{:0=4}".format(i))
        refCube.GetReferences().AddReference(_refUSDFilePath)
        refXform = UsdGeom.Xformable(refCube)
        refXform.AddTranslateOp(UsdGeom.XformOp.PrecisionFloat).Set(RandomVec3((10,10,10)))
        refXform.AddRotateXYZOp(UsdGeom.XformOp.PrecisionFloat).Set(RandomVec3((180,180,180)))
        refXform.AddScaleOp(UsdGeom.XformOp.PrecisionFloat).Set(RandomVec3((2,2,2)))

def WriteUSDStage(_nbRefs, _nbBatch, _usdExtension, _nbRepeats=100):

    totalBytesWritten=3*3*4*_nbRefs # translation, rotation and scale are 3 vectors of 3 floats (32 bits = 4 bytes)
    timingsNames=["UsdCreate", "Define World", "Add {} Refs to {} File(s)".format(_nbRefs, _nbBatch), "Save {} File".format(_nbBatch)]
    timings=np.zeros((_nbRepeats, len(timingsNames)), np.int64)

    #Repeat the process nbRepeats times to get a good average
    for rep in range(_nbRepeats):
        for fileNumber in range(_nbBatch):
            start = perf_counter_ns()
            
            stage = Usd.Stage.CreateNew('./Python/Temp/Cubes_{}.{}'.format(fileNumber, _usdExtension))
            
            timings[rep][0] += (perf_counter_ns()-start) #UsdCreate
            
            UsdGeom.Xform.Define(stage, "/World")

            timings[rep][1] += (perf_counter_ns()-start) #DefineWorld

            AddRandomPlaceReferencesInStage(stage, "/World", "Cube", "../Assets/SimpleTransform."+_usdExtension, int(_nbRefs/_nbBatch))
            
            timings[rep][2] += (perf_counter_ns()-start) #AddRandomPlaceReferencesInStage (nbRefs)

            stage.GetRootLayer().Save()

            timings[rep][3] += (perf_counter_ns()-start) #Save

            del stage
        
        #Delete the files created
        for fileNumber in range(_nbBatch):
            remove("./Python/Temp/Cubes_{}.".format(fileNumber)+_usdExtension)

        if (rep%10==0):
            print("Rep: {}%".format((rep/_nbRepeats)*100), sep=" ", end="\r", flush=True)
    
    #write the timing results in a csv file
    #FromNPArrayToCSV(timings, "./RuntimeResults", "{}_bytes__for_{}_objects_in_{}_{}_files.csv".format(totalBytesWritten, _nbRefs, _nbBatch, _usdExtension), ",".join(timingsNames))

    return timings

if (__name__=="__main__"):

    rd.seed(123)
    
    nbRepeats=100 #Number of time we run the writing process
    
    nbRefs=[10]#, 100, 1000, 10000, 100000] #Number of objects for which we will override the translation, rotation, and scale.
    nbBatch=[1, 2, 5, 10] #number of files in which the objects are going to be dispatched.
    usdExtension = ["usda", "usdc"] #whether we use usda or usdc

    for refs in nbRefs:
        for batch in nbBatch:
            for ext in usdExtension:
                print("refs: {}, batch: {}, ext: {}".format(refs, batch, ext))
                WriteUSDStage(refs, batch, ext, nbRepeats)
                print()
