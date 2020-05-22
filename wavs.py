from scipy.io.wavfile import read
from os import listdir
from os.path import isfile, join, dirname, realpath, getsize, isdir
from os import replace, mkdir, symlink, remove, system
import ctypes
import queue
from shutil import copyfile

savings = 0.0
hashTable = {}
mapping = {}
listOfLists = []
listOfDuplicateLocations = []
listOfOriginalLocationsToUse = set()
q = queue.Queue()
dirsExplored = 0
filesChecked = 0

    
def hashImpl(str1):
    try:
        global savings
        global hashTable
        global listOfDuplicateLocations
        global listOfOriginalLocationsToUse
        global mapping
        
        print("working on... : " + str(str1[0]))
        a = read(str1[0])
        #skip longer than 15 seconds samples
        if ((1.0*len(a[1])) / (1.0*a[0])) > 15.0:
            return
        #print(str(a[1]))
        #print(a[1].tobytes().__class__.__name__)
        if a[1].tobytes()[0:1408000] in hashTable:
            listOfDuplicateLocations.append(str1[0])
            hold = hashTable[a[1].tobytes()[0:1408000]]
            listOfOriginalLocationsToUse.add(hold)
            print("duplicate found: " + hold + " is what was found for this one called " + str1[0])
            mapping[str1[0]] = hold
            savings += str1[1]
        else:
            hashTable[a[1].tobytes()[0:1408000]] = str1[0]
    except (UnboundLocalError, ValueError) as e:
        1 + 1

def main():
    global q
    global filesChecked
    global dirsExplored
    global listOfDuplicateLocations
    global listOfOriginalLocationsToUse
    

    dirsExplored = dirsExplored + 1 
     
    dir_path = dirname(realpath(__file__))
    print(dir_path)

    onlyfiles = [(f, getsize(join(dir_path, f))) for f in listdir(dir_path) if isfile(join(dir_path, f)) and f[len(f) - 4:len(f)] == ".wav"]
    for strx in onlyfiles:
        filesChecked = filesChecked + 1
        hashImpl(strx)
    onlyDirs = [join(dir_path, f) for f in listdir(dir_path) if not isfile(join(dir_path, f))]
    for dir in onlyDirs:
        q.put(dir)
    while (q.empty() is False):
        handleThisDir(q.get())
    #print(onlyDirs)
    
    print("You can save " + '{:.10f}'.format(savings/1073741824) + " gigabytes of space if you delete the duplicates!")
    print("Files checked: " + str(filesChecked))
    print("Directories explored: " + str(dirsExplored))
    response = input("Would you like to delete "  +  '{:.10f}'.format(savings/1073741824) + " worth of redundant wav files and move a single copy of each to a new folder? [Y/N]: ")
    if response == 'Y':
        handleMigration()
    
def handleMigration():
    global listOfDuplicateLocations
    global listOfOriginalLocationsToUse
    global mapping
    
    dir_path = dirname(realpath(__file__))
    #mkdir("duplicate drums")
    """for orig in listOfOriginalLocationsToUse:
        newPath = dir_path+"\\duplicate drums\\" + orig.split("\\")[len(orig.split("\\")) - 1]
        copyfile(orig, newPath)"""
       
    #move the designated unique ones to a new folder and make symbolic links for them
    #dir_path = dirname(realpath(__file__))
    if isdir(dir_path+"\\duplicate drums"):
        raise OSError("directory " + dir_path + "\\duplicate drums" + " already exists, so rename this directory so name can be used")
        return
    else:
        mkdir("duplicate drums")
        for orig in listOfOriginalLocationsToUse:
            newPath = dir_path+"\\duplicate drums\\" + orig.split("\\")[len(orig.split("\\")) - 1]
            replace(orig, newPath)
              
            # Create a symbolic link 
            # pointing to src named dst 
            # using os.symlink() method 
            symlink(newPath, orig) 
            system("attrib /L +h \"" + orig + "\"")              
            #print("Symbolic link created successfully for " + orig) 

    #deletes the copies and makes symbolic links for them
    for dup in listOfDuplicateLocations:
        mapped = mapping[dup]
        newPath = dir_path+"\\duplicate drums\\" + mapped.split("\\")[len(mapped.split("\\")) - 1]
        remove(dup)
        symlink(newPath, dup) 
        system("attrib /L +h \"" + dup + "\"")
        #print("Symbolic link created successfully for " + dup)
    
    organizeFiles()    
#organizes all the files in the duplicate drums folder into 808s, claps, kicks, snares, percs, fx, etc
def organizeFiles():
    dir_path = dirname(realpath(__file__))+"\\duplicate drums\\"
    mkdir("duplicate drums\\808s")
    mkdir("duplicate drums\\claps")
    mkdir("duplicate drums\\kicks")
    mkdir("duplicate drums\\hi hats")
    mkdir("duplicate drums\\crashes cymbals rides")
    mkdir("duplicate drums\\open hats")
    mkdir("duplicate drums\\transitions")
    mkdir("duplicate drums\\snares")
    mkdir("duplicate drums\\percs")
    mkdir("duplicate drums\\hits")
    mkdir("duplicate drums\\fx")
    mkdir("duplicate drums\\vox")
    mkdir("duplicate drums\\random")
    onlyfiles = [f for f in listdir(dir_path) if isfile(join(dir_path, f)) and f[len(f) - 4:len(f)] == ".wav"]
    #copy all the files into one of the new folders, and hide copied files so the symbolic links can still find them
    for f in onlyfiles:
        copyfile(dir_path + f, dir_path + filterName(f) + "\\" + f)

    for f in onlyfiles:
        system("attrib +h \"" + dir_path + f + "\"") 

def filterName(wavName):
    wavName = wavName.lower()
    if "crash" in wavName or "cym" in wavName or "cymbol" in wavName or "ride" in wavName:
        return "crashes cymbals rides"
    elif "trans" in wavName or "rise" in wavName or "splash" in wavName or "fall" in wavName or "down" in wavName:
        return "transitions"
    elif "clap" in wavName:
        return "claps"
    elif "snare" in wavName or "sn" in wavName:
        return "snares"
    elif "open" in wavName or "oh" in wavName:
        return "open hats"
    elif "hat" in wavName or "hh" in wavName:
        return "hi hats"
    elif "808" in wavName or "sub" in wavName:
        return "808s"
    elif "kic" in wavName:
        return "kicks"
    elif "vox" in wavName or "chant" in wavName: 
        return "vox"
    elif "fx" in wavName or "effect" in wavName:
        return "fx"
    elif "hit" in wavName or "stab" in wavName:
        return "hits"
    elif "shot" in wavName or "rim" in wavName or "snap" in wavName or "perc" in wavName or "tri" in wavName or "sound" in wavName or "tap" in wavName or "pop" in wavName or "drum" in wavName or "stick" in wavName or "shake" in wavName or "bongo" in wavName or "tom" in wavName:
        return "percs"
        
    return "random"
    
def handleThisDir(dirName):
    global dirsExplored
    global filesChecked
    global q
    
    dirsExplored = dirsExplored + 1
    onlyfiles = [(join(dirName, f), getsize(join(dirName, f))) for f in listdir(dirName) if isfile(join(dirName, f)) and f[len(f) - 4:len(f)] == ".wav"]
    for strx in onlyfiles:
        filesChecked = filesChecked + 1
        hashImpl(strx)
    onlyDirs = [join(dirName, f) for f in listdir(dirName) if not isfile(join(dirName, f))]
    for dir in onlyDirs:
        q.put(dir)
    
main()
    
