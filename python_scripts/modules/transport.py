import os
import sys
import shutil

def create_dfnTrans_links():
    os.symlink('../params.txt', 'params.txt')
    os.symlink('../allboundaries.zone', 'allboundaries.zone')
    os.symlink('../tri_fracture.stor', 'tri_fracture.stor')
    os.symlink('../poly_info.dat','poly_info.dat')
    #os.symlink(self._jobname+'/*ex', './')

def copy_dfnTrans_files(self):

        # Create Path to DFNTrans   
        try:
            os.symlink(os.environ['DFNTRANS_PATH']+'DFNTrans', './DFNTrans')
        except OSError:
            os.remove('DFNTrans')   
            os.symlink(os.environ['DFNTRANS_PATH']+'DFNTrans', './DFNTrans')
        except:
            sys.exit("Cannot create link to DFNTrans. Exiting Program")
        
        # Copy DFNTrans input file
        print(os.getcwd())
 
        print("Attempting to Copy %s\n"%self._dfnTrans_file) 
        try:
            shutil.copy(self._dfnTrans_file, os.path.abspath(os.getcwd())) 
        except OSError:
            print("--> Problem copying %s file"%self._local_dfnTrans_file)
            print("--> Trying to delete and recopy") 
            os.remove(self._local_dfnTrans_file)
            shutil.copy(self._dfnTrans_file, os.path.abspath(os.getcwd())) 
        except:
            print("--> ERROR: Problem copying %s file"%self._dfnTrans_file)
            sys.exit("Unable to replace. Exiting Program")

def run_dfntrans(self):

        failure = os.system('./DFNTrans '+self._local_dfnTrans_file)
        if failure == 0:
            print('='*80)
            print("\ndfnTrans Complete\n")
            print('='*80)
        else:
            sys.exit("--> ERROR: dfnTrans did not complete\n")

