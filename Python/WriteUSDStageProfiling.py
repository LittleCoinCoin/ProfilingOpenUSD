from pxr import Usd, UsdGeom
import random as rd
from time import perf_counter_ns
import numpy as np
from general_IO import writer, check_make_directory
from os import remove, listdir
from concurrent.futures import ProcessPoolExecutor

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
        refXform.AddTranslateOp(UsdGeom.XformOp.PrecisionFloat).Set(RandomVec3((10, 10, 10)))
        refXform.AddRotateXYZOp(UsdGeom.XformOp.PrecisionFloat).Set(RandomVec3((180,180,180)))
        refXform.AddScaleOp(UsdGeom.XformOp.PrecisionFloat).Set(RandomVec3((2,2,2)))


def process_file(_rep, _nbBatch, _nbRefs, _usdExtension):
    timings=np.zeros((4), np.int64)
    for fileNumber in range(_nbBatch):
        start = perf_counter_ns()
        stage = Usd.Stage.CreateNew('./Temp/Cubes_{}_{}.'.format(_rep, fileNumber)+_usdExtension)
        timings[0] += (perf_counter_ns()-start) #UsdCreate - Part 1

        start = perf_counter_ns()
        UsdGeom.Xform.Define(stage, "/World")
        timings[1] += (perf_counter_ns()-start) #DefineWorld - Part 2

        start = perf_counter_ns()
        AddRandomPlaceReferencesInStage(stage, "/World", "Cube", "../../Assets/SimpleTransform."+_usdExtension, int(_nbRefs/_nbBatch))
        timings[2] += (perf_counter_ns()-start) #AddRandomPlaceReferencesInStage (nbRefs) - Part 3

        start = perf_counter_ns()
        stage.GetRootLayer().Save()
        timings[3] += (perf_counter_ns()-start) #Save - Part 4

    del stage

    return timings

def WriteUSDStage(_nbRefs, _nbBatch, _usdExtension, _nbRepeats=100, _numWorkers=1):

    # Determine the number of processes to use
    numWorkers = min(_nbRepeats, _numWorkers)  # Use _numWorkers if it is smaller than _nbRepeats
    
    totalBytesWritten=3*3*4*_nbRefs # translation, rotation and scale are 3 vectors of 3 floats (32 bits = 4 bytes)
    timingsNames=["UsdCreate", "Define World", "Add {} Refs to {} File(s)".format(_nbRefs, _nbBatch), "Save {} File".format(_nbBatch)]
    #timings=np.zeros((numWorkers, _nbRepeats, len(timingsNames)), np.int64)
    timings=np.zeros((_nbRepeats, len(timingsNames)), np.int64)

    # Create the directory to store the temporary files if it does not exist
    check_make_directory("./Temp/")
    # Create and start the processes using ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=numWorkers) as executor:
        futures = [executor.submit(process_file, rep, _nbBatch, _nbRefs, _usdExtension) for rep in range(_nbRepeats)]
    
    for _rep, future in enumerate(futures):
        timings[_rep] = future.result()[:]

    # Delete the files created
    for file in listdir("./Temp/"):
        remove("./Temp/"+file)

    # write the detail timing results in a csv file
    check_make_directory("./RuntimeResults_{}-Processes".format(numWorkers))
    FromNPArrayToCSV(timings, "./RuntimeResults_{}-Processes".format(numWorkers), "{}_bytes_for_{}_objects_in_{}_{}_files.csv".format(totalBytesWritten, _nbRefs, _nbBatch, _usdExtension), ",".join(timingsNames))
    return timings

if (__name__=="__main__"):

    rd.seed(123)
    
    nbRepeats=10 #Number of time we run the writing process
    numWorkers=4 #Number of processes we use to run the writing process
    nbRefs=[10, 100, 1000]#, 10000, 100000] #Number of objects for which we will override the translation, rotation, and scale.
    nbBatch=[1, 2, 5, 10] #number of files in which the objects are going to be dispatched.
    usdExtension = ["usda", "usdc"] #whether we use usda or usdc

    for refs in nbRefs:
        for batch in nbBatch:
            for ext in usdExtension:
                print("refs: {}, batch: {}, ext: {}".format(refs, batch, ext))
                WriteUSDStage(refs, batch, ext, nbRepeats, numWorkers)
                print()
