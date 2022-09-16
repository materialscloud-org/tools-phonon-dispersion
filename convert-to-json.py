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

with open(os.path.join(folder_name, "scf.in")) as fhandle:
    scf_input = fhandle.read()
with open(os.path.join(folder_name, "scf.out")) as fhandle:
    scf_output = fhandle.read()
with open(os.path.join(folder_name, "matdyn.modes")) as fhandle:
    matdyn_modes = fhandle.read()

pretty_name_dict = {"BaTiO_3": "BaTiO<sub>3</sub>"}

highsym_qpts_default = [[0, "Γ"], [20, "M"], [40, "K"], [60, "Γ"]]
highsym_qpts_dict = {
    "BaTiO_3": [[0, "X"], [20, "Γ"], [40, "M"], [60, "Γ"], [100, "R"]],
}

starting_reps_default = (5, 5, 1)
starting_reps_dict = {"BaTiO_3": (3, 3, 3)}


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
