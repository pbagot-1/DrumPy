from scipy.io.wavfile import read
import os
from shutil import copyfile
from numpy import ndarray
import stat
import queue

q = queue.Queue()
savings = 0.0
dirsExplored = 0
filesChecked = 0
hashTable = {}
mapping = {}
listOfLists = []
listOfDuplicateLocations = []
listOfOriginalLocationsToUse = set()
gaugeLoad = 0

def main():
    global q
    global filesChecked
    global dirsExplored
    global listOfDuplicateLocations
    global listOfOriginalLocationsToUse
    global savings
    
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    try:
        file = open("testPrivs.txt", "w") 
        file.close()
        os.symlink("testPrivs.txt", "testPrivs(sym).txt")
    except OSError:
        print("Please run program as administrator so it can make symbolic links")
        os.remove("testPrivs.txt")
        return
    os.remove("testPrivs.txt")
    os.remove("testPrivs(sym).txt")
    
    dirsExplored += 1

    onlyfiles = [(f, os.path.getsize(os.path.join(dir_path, f))) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)) and f[len(f) - 4:len(f)] == ".wav"]
    for strx in onlyfiles:
        filesChecked = filesChecked + 1
        hashImpl(strx)
    onlyDirs = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if not os.path.isfile(os.path.join(dir_path, f))]
    for dir in onlyDirs:
        q.put(dir)
    while (q.empty() is False):
        handleThisDir(q.get())
    
    for item in listOfOriginalLocationsToUse:
           savings = savings - os.path.getsize(item)
    print("You can save " + '{:.10f}'.format(savings/1073741824) + " gigabytes of space if you delete the duplicates!")
    print("Files checked: " + str(filesChecked))
    print("Directories explored: " + str(dirsExplored))
    print("Number of duplicates found: " + str(len(listOfDuplicateLocations)))
    print("Number of unique drums in the new combined kit: " + str(len(listOfOriginalLocationsToUse)))
    response = input("Would you like to delete "  +  '{:.10f}'.format(savings/1073741824) + " gigabytes worth of redundant wav files and move a single copy of each to a new folder? [Y/N]: ")
    if response == 'Y':
        handleMigration()
        
    print('[{0}]\r'.format(20*"#"), end="", flush=True)  
    print("Done.")
 

def hashImpl(str1):
    try:
        global savings
        global hashTable
        global listOfDuplicateLocations
        global listOfOriginalLocationsToUse
        global mapping

        print("working on... : " + str(str1[0]))
        a = read(str1[0])
        
        #skip longer than 10 seconds samples
        if ((1.0*len(a[1])) / (1.0*a[0])) > 10.0:
            return
            
        type = a[1].dtype
        index = 0
        sizeOf = len(a[1])
        
        if not isinstance(a[1][0], ndarray):
            while(index != sizeOf and a[1][index] == 0):
                index += 1
        elif len(a[1][0]) == 2:
            while(index != sizeOf and a[1][index][0] == 0 and a[1][index][1] == 0):
                index += 1
                
        if (index == sizeOf):
            return
            
        if a[1][index:index + 10000].tobytes() in hashTable:
            listOfDuplicateLocations.append(str1[0])
            hold = hashTable[a[1][index:index + 10000].tobytes()]
            listOfOriginalLocationsToUse.add(hold)
            print("duplicate found: " + hold + " is what was found for: " + str1[0])
            mapping[str1[0]] = hold
            savings += str1[1]
        else:
            hashTable[a[1][index:index + 10000].tobytes()] = str1[0]            
    except (UnboundLocalError, ValueError) as e:
        1 + 1

def printLoad(num):
    global gaugeLoad

    minDif = float('inf')
    index = 0
    for j in range (0, 20):
        if abs(float(num)/gaugeLoad - j/20) < minDif:
            minDif = abs(float(num)/gaugeLoad - j/20)
            index = j
            
    #print(f'[{index*"#"}{" "*(20-index)}]\r', end="", flush=True)        
    print('[{0}{1}]\r'.format(index*"#", " "*(20-index)), end="", flush=True)  
def handleMigration():
    global listOfDuplicateLocations
    global listOfOriginalLocationsToUse
    global mapping
    global gaugeLoad
    loader = 0
    dir_path = os.path.dirname(os.path.realpath(__file__))
    gaugeLoad = len(listOfDuplicateLocations) + len(listOfOriginalLocationsToUse)*2 
    #move the designated unique ones to a new folder and make symbolic links for them
    #dir_path = os.path.dirname(os.path.realpath(__file__))
    if os.path.isdir(dir_path+"\\duplicate drums"):
        raise OSError("directory " + dir_path + "\\duplicate drums" + " already exists, so rename this directory so name can be used")
        return
    else:
        print('[{0}]\r'.format(" "*(20)), end="", flush=True)  
        os.mkdir("duplicate drums")
        for orig in listOfOriginalLocationsToUse:
            newPath = dir_path+"\\duplicate drums\\" + orig.split("\\")[len(orig.split("\\")) - 1]
            os.replace(orig, newPath)
              
            # Create a symbolic link 
            # pointing to src named dst 
            # using os.os.symlink() method 
            os.symlink(newPath, orig) 
            os.system("attrib /L +h \"" + orig + "\"")
            loader += 1  
            if loader % 50 == 0:
                printLoad(loader)

    #deletes the copies and makes symbolic links for them
    for dup in listOfDuplicateLocations:
        mapped = mapping[dup]
        newPath = dir_path+"\\duplicate drums\\" + mapped.split("\\")[len(mapped.split("\\")) - 1]
        os.chmod(dup, stat.S_IWRITE)
        os.remove(dup)
        os.symlink(newPath, dup) 
        os.system("attrib /L +h \"" + dup + "\"")
        loader += 1            
        if loader % 50 == 0:
            printLoad(loader)     
        
    
    organizeFiles(loader)   
    
#organizes all the files in the duplicate drums folder into 808s, claps, kicks, snares, percs, fx, etc
def organizeFiles(loader):
    dir_path = os.path.dirname(os.path.realpath(__file__))+"\\duplicate drums\\"
    os.mkdir("duplicate drums\\808s")
    os.mkdir("duplicate drums\\claps")
    os.mkdir("duplicate drums\\kicks")
    os.mkdir("duplicate drums\\hi hats")
    os.mkdir("duplicate drums\\crashes cymbals rides")
    os.mkdir("duplicate drums\\open hats")
    os.mkdir("duplicate drums\\transitions")
    os.mkdir("duplicate drums\\snares")
    os.mkdir("duplicate drums\\percs")
    os.mkdir("duplicate drums\\hits")
    os.mkdir("duplicate drums\\fx")
    os.mkdir("duplicate drums\\vox")
    os.mkdir("duplicate drums\\random")
    onlyfiles = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)) and f[len(f) - 4:len(f)] == ".wav"]
    #copy all the files into one of the new folders, and hide copied files so the symbolic links can still find them
    for f in onlyfiles:
        copyfile(dir_path + f, dir_path + filterName(f) + "\\" + f)
        loader += 1            
        if loader % 50 == 0:
            printLoad(loader)
        
    for f in onlyfiles:
        os.system("attrib +h \"" + dir_path + f + "\"") 

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
    
def handleThisDir(dirname):
    global dirsExplored
    global filesChecked
    global q
    
    dirsExplored = dirsExplored + 1
    onlyfiles = [(os.path.join(dirname, f), os.path.getsize(os.path.join(dirname, f))) for f in os.listdir(dirname) if os.path.isfile(os.path.join(dirname, f)) and f[len(f) - 4:len(f)] == ".wav"]
    for strx in onlyfiles:
        filesChecked = filesChecked + 1
        hashImpl(strx)
    onlyDirs = [os.path.join(dirname, f) for f in os.listdir(dirname) if not os.path.isfile(os.path.join(dirname, f))]
    for dir in onlyDirs:
        q.put(dir)
    
main()
    
