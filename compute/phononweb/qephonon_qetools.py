# Copyright (c) 2019, Giovanni Pizzi
# All rights reserved.

""" Read phonon dispersion from quantum espresso """
import io
import re
import numpy as np

from tools_barebone.structure_importers import get_structure_tuple
from .phononweb import Phonon
from .lattice import car_red, rec_lat
from .units import atomic_numbers, bohr_in_angstrom

class QePhononQetools(Phonon):
    """
    Class to read phonons from Quantum ESPRESSO.
    """
    def __init__(self,scf_input,scf_output,matdyn_modes,
                 highsym_qpts=None,reorder=True):
        self.name="PW"
        self.highsym_qpts = highsym_qpts

        # PBC repetitions used as a starting value in the visualizer
        self.reps = (3, 3, 3)

        #read atoms
        self.read_atoms(io.StringIO(scf_input))
        # read alat (from output)
        self.read_alat(io.StringIO(scf_output))
        #read modes
        self.read_modes(io.StringIO(matdyn_modes))
        #reorder eigenvalues
        if reorder:
            self.reorder_eigenvalues()
        self.get_distances_qpts()
        self.labels_qpts = None

    def read_modes(self,fileobject):
        """
        Function to read the eigenvalues and eigenvectors from Quantum ESPRESSO
        """
        file_list = fileobject.readlines()
        file_str  = "".join(file_list)

        #determine the numer of atoms
        lines_with_freq = [int(x) for x in re.findall(r'(?:freq|omega) \((.+)\)', file_str )]
        if not lines_with_freq:
            raise ValueError("Unable to find the lines with the frequencies in the matdyn.modes file. "
            "Please check that you uploaded the correct file!")
        nphons = max(lines_with_freq)
        atoms = int(nphons/3)

        #check if the number fo atoms is the same
        if atoms != self.natoms:
            print("The number of atoms in the <>.scf file is not the same as in the <>.modes file")
            exit(1)

        #determine the number of qpoints
        self.nqpoints = len( re.findall('q = ', file_str ) )
        nqpoints = self.nqpoints

        eig = np.zeros([nqpoints,nphons])
        vec = np.zeros([nqpoints,nphons,atoms,3],dtype=complex)
        qpt = np.zeros([nqpoints,3])
        for k in range(nqpoints):
            #iterate over qpoints
            k_idx = 2 + k*((atoms+1)*nphons + 5)
            #read qpoint
            qpt[k] = list(map(float, file_list[k_idx].split()[2:]))
            for n in range(nphons):
                #read eigenvalues
                eig_idx = k_idx+2+n*(atoms+1)
                reig = re.findall(r'=\s+([+-]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)',file_list[eig_idx])[1]
                eig[k][n] = float(reig)
                for i in range(atoms):
                    #read eigenvectors
                    svec = re.findall(r'([+-]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)',file_list[eig_idx+1+i])
                    z = list(map(float,svec))
                    cvec = [complex(z[0],z[1]),complex(z[2],z[3]),complex(z[4],z[5])]
                    vec[k][n][i] = np.array(cvec, dtype=complex)

        #the quantum espresso eigenvectors are already scaled with the atomic masses
        #Note that if the file comes from dynmat.eig they are not scaled with the atomic masses
        #here we scale then with sqrt(m) so that we recover the correct scalling on the website
        #we check if the eigenvectors are orthogonal or not
        #for na in xrange(self.natoms):
        #    atomic_specie = self.atypes[na]-1
        #    atomic_number = self.atomic_numbers[atomic_specie]
        #    vectors[:,:,na,:,:] *= sqrt(atomic_mass[atomic_number])

        self.nqpoints     = len(qpt)
        self.nphons       = nphons
        self.eigenvalues  = eig#*eV/hartree_cm1
        self.eigenvectors = vec.view(dtype=float).reshape([self.nqpoints,nphons,nphons,2])
        self.qpoints      = qpt

        # convert from cartesian coordinates (units of 2pi/alat, alat is the alat of the code)
        # to reduced coordinates
        # First, I need to convert from 2pi/alat units (as written in the matdyn.modes file) to 
        # 1/angstrom (as self.rec is)
        self.qpoints = np.array(self.qpoints) * 2 * np.pi / self.alat

        # now that I have self.qpoints in 1/agstrom, I can just use self.rec to convert to reduced
        # coordinates since self.rec is in units of 1/angstrom
        self.qpoints = car_red(self.qpoints,self.rec)
        return self.eigenvalues, self.eigenvectors, self.qpoints

    def read_atoms(self,fileobject):
        """ 
        read the data from a quantum espresso input file
        """
        fileformat = "qeinp-qetools"
        (cell, rel_positions, numbers) = get_structure_tuple(fileobject, fileformat)

        self.pos = rel_positions # reduced coords
        self.cell = np.array(cell)
        self.rec = rec_lat(self.cell)* 2 * np.pi

        self.natoms = len(rel_positions) # number of atoms
        self.atom_numbers = numbers  # atom number for each atom (integer)

        atom_names = []
        for n in numbers:
            for atom_name, atom_number in atomic_numbers.items():
                if atom_number == n:
                    atom_names.append(atom_name)

        self.atom_types = atom_names # atom type for each atom (string)

        self.chemical_formula = self.get_chemical_formula()


    def read_alat(self,fileobject):
        """ 
        Read the data from a quantum espresso output file.

        At the moment, it's used only to read `alat` since it's not univocally defined from
        the crystal structure in the input (ibrav=0 uses the length of the first vector, but this behavior
        changes between 5.0 and 6.0 in QE, or it's manually specified).
        Better to parse it from the output.
        """
        matching_lines = [l for l in fileobject.readlines() if 'lattice parameter (alat)' in l and 'a.u.' in l]
        if not matching_lines:
            raise ValueError("No lines with alat found in QE output file")
        if len(matching_lines) > 1:
            raise ValueError("Multiple lines with alat found in QE output file...")
        alat_line = matching_lines[0]
        alat_bohr = float(alat_line.split()[4])
        # Convert to angstrom from Bohr (a.u.)
        self.alat = alat_bohr * bohr_in_angstrom
