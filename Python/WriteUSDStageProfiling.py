from pxr import Usd, UsdGeom
import random as rd
from time import perf_counter_ns
import numpy as np
from general_IO import writer, check_make_directory
from os import remove, listdir
import threading

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

# Define a function to be executed by each thread
def process_files(_startRep, _endRep, nbBatch, nbRefs, _timings, usdExtension):
    print("Function process_file called by thread {}".format(threading.current_thread().name))
    for rep in range(_startRep, _endRep):
        for fileNumber in range(nbBatch):

            start = perf_counter_ns()
            stage = Usd.Stage.CreateNew('./Temp/Cubes_{}_{}.'.format(rep, fileNumber)+usdExtension)
            _timings[rep][0] += (perf_counter_ns()-start) #UsdCreate - Part 1

            start = perf_counter_ns()
            UsdGeom.Xform.Define(stage, "/World")
            _timings[rep][1] += (perf_counter_ns()-start) #DefineWorld - Part 2

            start = perf_counter_ns()
            AddRandomPlaceReferencesInStage(stage, "/World", "Cube", "../../Assets/SimpleTransform."+usdExtension, int(nbRefs/nbBatch))
            _timings[rep][2] += (perf_counter_ns()-start) #AddRandomPlaceReferencesInStage (nbRefs) - Part 3

            start = perf_counter_ns()
            stage.GetRootLayer().Save()
            _timings[rep][3] += (perf_counter_ns()-start) #Save - Part 4

    del stage

def WriteUSDStage(_nbRefs, _nbBatch, _usdExtension, _nbRepeats=100, _numThreads=1):
    # Create a list to store the threads
    threads = []

    # Determine the number of threads to use
    numThreads = min(_nbRepeats, _numThreads)  # Use _numThreads if it is smaller than _nbRepeats

    # Calculate the number of repetitions per thread
    repsPerThread = _nbRepeats // numThreads
    repsPerThreadReal = {} # Store the real number of repetitions per thread (e.g. if _nbRepeats is not a multiple of numThreads)
    
    totalBytesWritten=3*3*4*_nbRefs # translation, rotation and scale are 3 vectors of 3 floats (32 bits = 4 bytes)
    timingsNames=["UsdCreate", "Define World", "Add {} Refs to {} File(s)".format(_nbRefs, _nbBatch), "Save {} File".format(_nbBatch)]
    #timings=np.zeros((numThreads, _nbRepeats, len(timingsNames)), np.int64)
    timings=np.zeros((_nbRepeats, len(timingsNames)), np.int64)

    # Create the directory to store the temporary files if it does not exist
    check_make_directory("./Temp/")

    # Create and start the threads
    for i in range(numThreads):
        start_rep = i * repsPerThread
        end_rep = start_rep + repsPerThread if i < numThreads - 1 else _nbRepeats
        thread = threading.Thread(target=process_files, args=(start_rep, end_rep, _nbBatch, _nbRefs, timings, _usdExtension))
        thread.start()
        repsPerThreadReal[thread.ident] = (thread.name, end_rep-start_rep)
        print("Thread '{}' ({}) started with {} repetitions".format(thread.name, thread.ident, end_rep-start_rep))
        threads.append(thread)

    # Wait for all threads to finish
    for i in range(numThreads):
        threads[i].join()
        print("Thread '{}' finished with {} repetitions".format(repsPerThreadReal[thread.ident][0], repsPerThreadReal[thread.ident][1]))

    # Delete the files created
    for file in listdir("./Temp/"):
        remove("./Temp/"+file)

    # write the detail timing results in a csv file
    check_make_directory("./RuntimeResults_{}-Threads".format(numThreads))
    FromNPArrayToCSV(timings, "./RuntimeResults_{}-Threads".format(numThreads), "{}_bytes_for_{}_objects_in_{}_{}_files.csv".format(totalBytesWritten, _nbRefs, _nbBatch, _usdExtension), ",".join(timingsNames))
    return timings

if (__name__=="__main__"):

    rd.seed(123)
    
    nbRepeats=100 #Number of time we run the writing process
    numThreads=2 #Number of threads we use to run the writing process
    nbRefs=[10, 100, 1000]#, 10000, 100000] #Number of objects for which we will override the translation, rotation, and scale.
    nbBatch=[1, 2, 5, 10] #number of files in which the objects are going to be dispatched.
    usdExtension = ["usda", "usdc"] #whether we use usda or usdc

    for refs in nbRefs:
        for batch in nbBatch:
            for ext in usdExtension:
                print("refs: {}, batch: {}, ext: {}".format(refs, batch, ext))
                WriteUSDStage(refs, batch, ext, nbRepeats, numThreads)
                print()
