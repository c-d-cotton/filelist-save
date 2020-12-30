#!/usr/bin/env python3
import os
from pathlib import Path
import sys

__projectdir__ = Path(os.path.dirname(os.path.realpath(__file__)) + '/')

import copy
import datetime
import os
import shutil

# Preliminary Functions:{{{1
# import issubpath:{{{1
sys.path.append(str(__projectdir__ / Path('submodules/python-general-func/')))
from filename_func import issubpath
issubpath = issubpath

def convertabsolutetorelative(filelist, commonpath):
    relativefilelist = []
    for filename in filelist:
        if os.path.isabs(filename) is True:
            if issubpath(filename, commonpath) is True:
                relativefilelist.append(os.path.relpath(filename, commonpath))
            else:
                raise ValueError('Filename does not contain commonpath: Filename: ' + filename + '. Common path: ' + commonpath + '.')
        else:
            relativefilelist.append(filename)

    return(relativefilelist)

# Actual Backup:{{{1
def getorderedstringsubset(list1, list2):
    """
    Split items in list1 into items that are in list2 and those that are not
    list1 and list2 are ordered lists of strings which allows for speedier sorting
    """
    # special cases
    if len(list1) == 0:
        return([], [])
    if len(list2) == 0:
        return([], copy.deepcopy(list1))

    issubset = []
    isnotsubset = []
    list1 = copy.deepcopy(list1)
    list2 = copy.deepcopy(list2)

    item1 = list1.pop(0)
    item2 = list2.pop(0)
    while True:
        if item1 < item2:
            isnotsubset.append(item1)
            try:
                item1 = list1.pop(0)
            except Exception:
                # no more list1 to do so just stop
                break
        else:
            if item1 == item2:
                issubset.append(item1)
                try:
                    item1 = list1.pop(0)
                except Exception:
                    # no more list1 to do so just stop
                    break
            # take next list2 if item1 >= item2
            try:
                item2 = list2.pop(0)
            except Exception:
                # if not more list2 stop and add rest to isnotsubset
                isnotsubset = isnotsubset + [item1] + list1
                break

    return(issubset, isnotsubset)
            
            
def getorderedstringsubset_test():
    list1 = [1,2,3,4,5]
    list2 = [1.5, 2, 2.5, 2.75, 3.5, 4, 6]
    issubset, isnotsubset = getorderedstringsubset(list1, list2)
    print(issubset, isnotsubset)


def savefilelist(sourcefilelist, sourcefolder, destfolder, sourcedirlist = None, deleteold = True, donotdeletepaths = None, deletedfolder = None, donotmovetodeletedfolderlist = None):
    """
    destfolder are where I save the files to
    sourcefilelist is a list of full filenames which I want to back up
    sourcedirlist is a list of full dirnames which I want to back up (not needed)

    all paths should be inputted as absolute paths
    There should be a common rootpath for sourcefilelist, sourcedirlist (which could just be the root directory)
    If the the destfolder is /home/b then /home/a/1/2.txt would be saved as /home/b/home/a/1/2.txt if the commonpath is / and as /home/b/1/2.txt if the commonpath is /home/a.

    If deleteold is True then I delete the files from destfolder that are not in sourcefilelist.
    For folders, I delete empty folders in destfolder when sourcedirlist is not specified and delete any folder not in sourcedirlist if it is specified
    If donotdeletepaths is specified then I don't delete files in destfolder that are not in sourcefilelist/sourcedirlist (though I do replace them if there are newer versions)

    If deletedfolder is not None then rather than actually delete the files in destfolder that are not in sourcefilelist/sourcedirlist, I actually move them to deletedfolder
    If donotmovetodeletedfolderlist is specified then I do not move files to deletedfolder that contain these paths.

    Preliminary steps:
    - Get all files and directories in destfolder
    - Adjust files i.e. define relative paths and generate empty lists if None where relevant
    - Define copy to delete folder function if relevant

    Main steps:
    - Go through files in sourcefilelist and replace in destfolder (possibly copying old versions over to deletedfolder if specified)
    - If sourcedirlist is not None: Add in any other folders in sourcedirlist that have not been created
    - If deleteold is True I delete files that are not in sourcefilelist and folders not in sourcedirlist (or empty folders). If deletedfolder is not None then I actually move these files unless they're in donotmovetodeletedfolderlist

    """
    # adjust file paths:{{{
    if donotdeletepaths is None:
        donotdeletepaths = []
    if donotmovetodeletedfolderlist is None:
        donotmovetodeletedfolderlist = []
    # convert string to list if inputted wrong
    if isinstance(donotdeletepaths, str):
        donotdeletepaths = [donotdeletepaths]
    if isinstance(donotmovetodeletedfolderlist, str):
        donotmovetodeletedfolderlist = [donotmovetodeletedfolderlist]

    sourcefilelist = convertabsolutetorelative(sourcefilelist, sourcefolder)
    if sourcedirlist is not None:
        sourcedirlist = convertabsolutetorelative(sourcedirlist, sourcefolder)
    donotdeletepaths = convertabsolutetorelative(donotdeletepaths, sourcefolder)
    donotmovetodeletedfolderlist = convertabsolutetorelative(donotmovetodeletedfolderlist, sourcefolder)
    # adjust file paths:}}}

    # do this before adding files since otherwise I'll have to go through more files
    if deleteold is True:
        # get old paths for the destfolder
        oldfilelist = []
        olddirlist = []
        for root, dirs, files in os.walk(destfolder, topdown=False):
            for name in files:
                oldfilelist.append(os.path.relpath(os.path.join(root, name), destfolder))
            for name in dirs:
                olddirlist.append(os.path.relpath(os.path.join(root, name), destfolder))

    # move to deletedfolder function:{{{
    if deletedfolder is not None:
        timenow = datetime.datetime.now()
        deletedsuffix = '_' + str(timenow.year) + str(timenow.month).zfill(2) + str(timenow.day).zfill(2) + '_' + str(timenow.hour).zfill(2) + str(timenow.minute).zfill(2) + str(timenow.second).zfill(2)
        def movetodeletedfolder(relativefilename):
            tomovefilename = os.path.join(destfolder, relativefilename)
            movetofilename = os.path.join(deletedfolder, relativefilename + deletedsuffix)

            # if filename is in donotmovetodeletedfolderlist then delete the file rather than remove it
            if True in set([issubpath(relativefilename, donotmovefolder) for donotmovefolder in donotmovetodeletedfolderlist]):
                os.remove(tomovefilename)
            else:

                # if folder not exist then make in oldfolder
                folder = os.path.dirname(movetofilename)
                if os.path.isdir(folder) is False:
                    os.makedirs(folder)

                # move file
                if os.path.isfile(movetofilename):
                    raise ValueError('File already exists in deletedfolder: ' + movetofilename + '.')
                else:
                    shutil.move(tomovefilename, movetofilename)
    # move to deletedfolder function:}}}
            

    # add new files
    # replace changed files
    # make new folders at the start if necessary
    for filename in sourcefilelist:
        sourcefilename = os.path.join(sourcefolder, filename)
        destfilename = os.path.join(destfolder, filename)

        # skip if sourcefilename got deleted in between getting filelist and run
        if not os.path.isfile(sourcefilename) is True:
            print('Skipped file deleted during run: ' + sourcefilename + '.')
            continue

        # make folder if necessary
        folder = os.path.dirname(destfilename)
        if not os.path.isdir(folder):
            os.makedirs(folder)

        if os.path.isfile(destfilename):
            # replace if changes
            # function checks whether checksums are different
            sys.path.append(str(__projectdir__ / Path('submodules/python-general-func/')))
            from filename_func import twofilesaresame
            if twofilesaresame(sourcefilename, destfilename) is False:
                if deletedfolder is not None:
                    movetodeletedfolder(filename)
                else:
                    os.remove(destfilename)
                # copy over new version
                shutil.copy(sourcefilename, destfilename)
        else:
            # if the file does not exist in the backup, just copy over the file
            shutil.copyfile(sourcefilename, destfilename)

    # make new directory if not exist already
    if sourcedirlist is not None:
        for reldirname in sourcedirlist:
            folder = os.path.join(destfolder, reldirname)
            if not os.path.isdir(folder):
                os.makedirs(folder)
            
    # remove old files
    if deleteold is True:

        # list of files I could consider deleting (though I need to verify they're not in sourcefolder first)
        potentialdeletefilelist = [filename for filename in oldfilelist if True not in set([issubpath(filename, donotdeletepath) for donotdeletepath in donotdeletepaths])]
        if sourcedirlist is not None:
            potentialdeletedirlist = [filename for filename in olddirlist if True not in set([issubpath(filename, donotdeletepath) for donotdeletepath in donotdeletepaths])]

        # get which files I should delete
        # delete files
        deletefiles = getorderedstringsubset(sorted(potentialdeletefilelist), sorted(sourcefilelist))[1]
        for oldfile in deletefiles:
            if deletedfolder is not None:
                movetodeletedfolder(oldfile)
            else:
                os.remove(os.path.join(destfolder, oldfile))

        # advantage of specifying sourcedirlist is that I don't delete empty directories in sourcedirlist which don't contain any files
        # allows for perfect backup
        if sourcedirlist is not None:
            deletedirs = getorderedstringsubset(sorted(potentialdeletedirlist), sorted(sourcedirlist))[1]
            # go in reverse order so that I do /home/user/1 before /home/user otherwise:
            # 1. /home/user will not be empty when I try to delete it
            # 2. /home/user/1 will already be deleted when I try to delete it
            for olddir in reversed(deletedirs):
                os.rmdir(os.path.join(destfolder, olddir))
        else:
            for olddir in olddirlist:
                if os.path.isdir(os.path.join(destfolder, olddir)) is True:
                    if len(os.listdir(os.path.join(destfolder, olddir))) == 0:
                        os.rmdir(os.path.join(destfolder, olddir))

            
def savefilelist_test():
    if os.path.isdir(__projectdir__ / Path('test/temp/')):
        shutil.rmtree(__projectdir__ / Path('test/temp/'))
    shutil.copytree(__projectdir__ / Path('test/data/'), __projectdir__ / Path('test/temp/'))


    sourcefilelist = []
    sourcedirlist = []
    for root, dirs, files in os.walk(__projectdir__ / Path('test/temp/tocopy/'), topdown=False):
       for name in files:
          sourcefilelist.append(os.path.join(root, name))
       for name in dirs:
          sourcedirlist.append(os.path.join(root, name))

    sourcefolder = __projectdir__ / Path('test/temp/tocopy/')
    destfolder = __projectdir__ / Path('test/temp/copied/')


    # optiosn I can change
    sourcedirlist = sourcedirlist
    sourcedirlist = None

    deleteold = True
    # deleteold = False

    deletedfolder = __projectdir__ / Path('test/temp/deleted/')
    # deletedfolder = None

    savefilelist(sourcefilelist, sourcefolder, destfolder, sourcedirlist = sourcedirlist, deleteold = deleteold, deletedfolder = deletedfolder)
    

def savefolder(sourcefolder, destfolder, deleteold = True, ignorepaths = None, deletedfolder = None, donotmovetodeletedfolderlist = None):
    """
    The difference with savefilelist is that I just specify one folder to backup and include every file in this folder unless it is in ignorepaths.
    Files in ignorepaths are not backed up or deleted from the destination folder.
    """
    # get sourcefilelist, sourcedirlist
    sourcefilelist = []
    sourcedirlist = []
    for root, dirs, files in os.walk(sourcefolder, topdown=False):
       for name in files:
          sourcefilelist.append(os.path.join(root, name))
       for name in dirs:
          sourcedirlist.append(os.path.join(root, name))

    if ignorepaths is None:
        ignorepaths = []
    if isinstance(ignorepaths, str):
        ignorepaths = [ignorepaths]

    # convert sourcefilelist, sourcedirlist, ignorepaths to relative paths
    sourcefilelist = convertabsolutetorelative(sourcefilelist, sourcefolder)
    sourcedirlist = convertabsolutetorelative(sourcedirlist, sourcefolder)
    ignorepaths = convertabsolutetorelative(ignorepaths, sourcefolder)

    # remove files in sourcefilelist,sourcedirlist in ignorepaths so that I don't try to back them up
    sourcefilelist = [filename for filename in sourcefilelist if True not in set([issubpath(filename, ignorepath) for ignorepath in ignorepaths])]
    sourcedirlist = [dirname for dirname in sourcedirlist if True not in set([issubpath(dirname, ignorepath) for ignorepath in ignorepaths])]

    savefilelist(sourcefilelist, sourcefolder, destfolder, sourcedirlist = sourcedirlist, deleteold = deleteold, donotdeletepaths = ignorepaths, deletedfolder = deletedfolder, donotmovetodeletedfolderlist = donotmovetodeletedfolderlist)


def savefolder_test():
    if os.path.isdir(__projectdir__ / Path('test/temp/')):
        shutil.rmtree(__projectdir__ / Path('test/temp/'))
    shutil.copytree(__projectdir__ / Path('test/data/'), __projectdir__ / Path('test/temp/'))

    sourcefolder = __projectdir__ / Path('test/temp/tocopy/')
    destfolder = __projectdir__ / Path('test/temp/copied/')

    # options
    deletedfolder = __projectdir__ / Path('test/temp/deleted/')
    # deletedfolder = None

    ignorepaths = __projectdir__ / Path('test/temp/tocopy/ignored/')
    # ignorepaths = None
    
    donotmovetodeletedfolderlist = __projectdir__ / Path('test/temp/tocopy/deletedperm/')
    # donotmovetodeletedfolderlist = None
    
    savefolder(sourcefolder, destfolder, deleteold = True, ignorepaths = ignorepaths, deletedfolder = deletedfolder, donotmovetodeletedfolderlist = donotmovetodeletedfolderlist)

def savefolder_ap():
    #Argparse:{{{
    import argparse
    
    parser=argparse.ArgumentParser()
    parser.add_argument("sourcefolder")
    parser.add_argument("destfolder")
    parser.add_argument("--deletedfolder", default = None)
    
    args=parser.parse_args()
    #End argparse:}}}

    savefolder(args.sourcefolder, args.destfolder, deletedfolder = args.deletedfolder)
