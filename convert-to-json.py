#!/usr/bin/env python
import json
import os
import sys
from compute.phononweb.qephonon_qetools import QePhononQetools

try:
    folder_name = sys.argv[1]
    # system_name = sys.argv[2]
except IndexError:
    print(
        "Pass as argument the folder in which the QE files reside (they must be called scf.in, scf.out, matdyn.modes)."
    )
    sys.exit(1)

system_name = os.path.basename(os.path.realpath(folder_name))

with open(os.path.join(folder_name, "GaAs.scf.in")) as fhandle:
    scf_input = fhandle.read()
with open(os.path.join(folder_name, "GaAs.scf.out")) as fhandle:
    scf_output = fhandle.read()
with open(os.path.join(folder_name, "GaAs.modes")) as fhandle:
    matdyn_modes = fhandle.read()

pretty_name_dict = {"GaAs": "GaAs"}

highsym_qpts_default = [[0, "L"], [40, "Γ"], [80, "K"], [100, "X"], [140, "Γ"]]
highsym_qpts_dict = {
    "GaAs": [[0, "L"], [40, "Γ"], [80, "K"], [100, "X"], [140, "Γ"]],
}

#supercell.
starting_reps_default = (3,3,3)
starting_reps_dict = {"GaAs": (3, 3, 3)}


phonons = QePhononQetools(
    scf_input=scf_input,
    scf_output=scf_output,
    matdyn_modes=matdyn_modes,
    highsym_qpts=highsym_qpts_dict.get(system_name, highsym_qpts_default),
    starting_reps=starting_reps_dict.get(system_name, starting_reps_default),
    reorder=True,
    name=pretty_name_dict.get(system_name, system_name),
)

print(phonons)

with open("{}.json".format(system_name), "w") as fhandle:
    data = phonons.get_dict()
    # Remove alat if defined (so there is no message about Quantum ESPRESSO when the JSON file is loaded)
    try:
        data.pop("alat")
    except KeyError:
        pass

    json.dump(data, fhandle)
