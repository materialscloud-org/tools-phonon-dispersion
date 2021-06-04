# Copyright (c) 2019, Giovanni Pizzi
# All rights reserved.

""" Read phonon dispersion from quantum espresso """

import re
from math import pi
import numpy as np

from tools_barebone.structure_importers import get_structure_tuple
from .phononweb import Phonon, bohr_angstroem, atomic_numbers
from .lattice import car_red, rec_lat

atoms_num_dict = {
    "H": 1,
    "He": 2,
    "Li": 3,
    "Be": 4,
    "B": 5,
    "C": 6,
    "N": 7,
    "O": 8,
    "F": 9,
    "Ne": 10,
    "Na": 11,
    "Mg": 12,
    "Al": 13,
    "Si": 14,
    "P": 15,
    "S": 16,
    "Cl": 17,
    "Ar": 18,
    "K": 19,
    "Ca": 20,
    "Sc": 21,
    "Ti": 22,
    "V": 23,
    "Cr": 24,
    "Mn": 25,
    "Fe": 26,
    "Co": 27,
    "Ni": 28,
    "Cu": 29,
    "Zn": 30,
    "Ga": 31,
    "Ge": 32,
    "As": 33,
    "Se": 34,
    "Br": 35,
    "Kr": 36,
    "Rb": 37,
    "Sr": 38,
    "Y": 39,
    "Zr": 40,
    "Nb": 41,
    "Mo": 42,
    "Tc": 43,
    "Ru": 44,
    "Rh": 45,
    "Pd": 46,
    "Ag": 47,
    "Cd": 48,
    "In": 49,
    "Sn": 50,
    "Sb": 51,
    "Te": 52,
    "I": 53,
    "Xe": 54,
    "Cs": 55,
    "Ba": 56,
    "La": 57,
    "Ce": 58,
    "Pr": 59,
    "Nd": 60,
    "Pm": 61,
    "Sm": 62,
    "Eu": 63,
    "Gd": 64,
    "Tb": 65,
    "Dy": 66,
    "Ho": 67,
    "Er": 68,
    "Tm": 69,
    "Yb": 70,
    "Lu": 71,
    "Hf": 72,
    "Ta": 73,
    "W": 74,
    "Re": 75,
    "Os": 76,
    "Ir": 77,
    "Pt": 78,
    "Au": 79,
    "Hg": 80,
    "Tl": 81,
    "Pb": 82,
    "Bi": 83,
    "Po": 84,
    "At": 85,
    "Rn": 86,
    "Fr": 87,
    "Ra": 88,
    "Ac": 89,
    "Th": 90,
    "Pa": 91,
    "U": 92,
    "Np": 93,
    "Pu": 94,
    "Am": 95,
    "Cm": 96,
    "Bk": 97,
    "Cf": 98,
    "Es": 99,
    "Fm": 100,
    "Md": 101,
    "No": 102,
    "Lr": 103,
    "Rf": 104,
    "Db": 105,
    "Sg": 106,
    "Bh": 107,
    "Hs": 108,
    "Mt": 109,
    "Ds": 110,
    "Rg": 111,
    "Cn": 112,
}

class QePhononQetools(Phonon):
    """
    Class to read phonons from Quantum Espresso

    Input:
        prefix: <prefix>.scf file where the structure is stored
                <prefix>.modes file that is the output of the matdyn.x or dynmat.x programs
    """
    def __init__(self,prefix,name,reps=(3,3,3),folder='.',
                 highsym_qpts=None,reorder=True,scf=None,modes=None):
        self.prefix = prefix
        self.name = name
        self.reps = reps
        self.folder = folder
        self.highsym_qpts = highsym_qpts

        #read atoms
        if scf:   filename = "%s/%s"%(self.folder,scf)
        else :    filename = "%s/%s.scf"%(self.folder,self.prefix)
        self.read_atoms(filename)
        
        #read modes
        if modes: filename = "%s/%s"%(self.folder,modes)
        else :    filename = "%s/%s.modes"%(self.folder,self.prefix)
        self.read_modes(filename)
        

        #reorder eigenvalues
        if reorder:
            self.reorder_eigenvalues()
        self.get_distances_qpts()
        self.labels_qpts = None

    def read_modes(self,filename):
        """
        Function to read the eigenvalues and eigenvectors from Quantum Expresso
        """
        with open(filename,'r') as f:
            file_list = f.readlines()
            file_str  = "".join(file_list)

        #determine the numer of atoms
        nphons = max([int(x) for x in re.findall( '(?:freq|omega) \((.+)\)', file_str )])
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
                reig = re.findall('=\s+([+-]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)',file_list[eig_idx])[1]
                eig[k][n] = float(reig)
                for i in range(atoms):
                    #read eigenvectors
                    svec = re.findall('([+-]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)',file_list[eig_idx+1+i])
                    z = list(map(float,svec))
                    cvec = [complex(z[0],z[1]),complex(z[2],z[3]),complex(z[4],z[5])]
                    vec[k][n][i] = np.array(cvec, dtype=complex)

        #the quantum espresso eigenvectors are already scaled with the atomic masses
        #if the file comes from dynmat.eig they are not scaled with the atomic masses
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

        #convert to cartesian coordinates
        self.qpoints = car_red(self.qpoints,self.rec)
        return self.eigenvalues, self.eigenvectors, self.qpoints

    def read_atoms(self,filename):
        """ 
        read the data from a quantum espresso input file
        """
        fileformat = "qeinp-qetools"
        with open(filename) as f:
            (cell, rel_positions, numbers) = get_structure_tuple(f, fileformat)

        self.pos = rel_positions # reduced coords
        self.cell = np.array(cell)
        self.rec = rec_lat(self.cell)*2*pi

        self.natoms = len(rel_positions) # number of atoms
        self.atom_numbers = numbers  # atom number for each atom (integer)

        atom_names = []
        for n in numbers:
            for atom_name, atom_number in atoms_num_dict.items():
                if atom_number == n:
                    atom_names.append(atom_name)

        self.atom_types = atom_names # atom type for each atom (string)

        self.chemical_formula = self.get_chemical_formula()
