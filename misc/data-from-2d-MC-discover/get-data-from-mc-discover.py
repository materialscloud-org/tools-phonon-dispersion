#!/usr/bin/env python
import io
import json
import os
import subprocess
import sys
import urllib
import urllib.request

import numpy as np

sys.path.append("../..")
from compute.phononweb.qephonon_qetools import (  # pylint: disable=wrong-import-position
    QePhononQetools,
)

MATDYN_EXECUTABLE = os.path.expanduser("~/git/q-e/bin/matdyn.x")


class MissingPhononsError(Exception):
    """Exception raised if no phonons exist for a given compound."""


def _prettify_string(name):
    pretty_chars = []
    for char in name:
        if char in "0123456789":
            pretty_chars.append(f"<sub>{char}</sub>")
        else:
            pretty_chars.append(char)
    return "".join(pretty_chars)


def prettify_formula(formula, prototype):
    ret_string = _prettify_string(formula)
    if prototype:
        ret_string += f" [{_prettify_string(prototype)}]"
    return ret_string


def check_matdyn():
    process = subprocess.run(
        [MATDYN_EXECUTABLE],
        input="",
        check=False,
        capture_output=True,
        encoding="ascii",
    )
    # matdyn.x could create a CRASH file
    try:
        os.remove("CRASH")
    except FileNotFoundError:
        pass

    header_lines = [
        line.strip()
        for line in process.stdout.splitlines()
        if line.strip().startswith("Program MATDYN")
    ]
    if not header_lines:
        raise AssertionError("Could not find the expected header line in matdyn run...")
    header_line = header_lines[0]
    version = header_line.split()[2]
    # print("Matdyn version:", version, "NOTE: you need a recent 6.x version to support the 2D cutoff!")
    # For now I just do a stupid check, this would need to be improved.
    # I am not really sure in which version it the 2D cutoff was implemented - probably
    # in 6.1, while in 6.0 it's not there. Feel free to add more versions if you know it's working
    # (or more recent versions)
    assert version in [
        "v.6.8",
        "v.6.7.0",
        "v.6.7MaX",
    ], f"Version '{version}' not supported, if you know it works add it to the list of supported versions"


def get_files_from_materials_cloud(
    discover_data, compound
):  # pylint: disable=too-many-locals, too-many-statements
    """Given a compound name, return the content of some relevant files (as a dictionary)."""
    compounds = discover_data["data"]["compounds"]
    material = compounds[compound]
    try:
        phonons_uuid = material["phonons_2D"]
    except KeyError:
        raise MissingPhononsError(f"No phonons for {compound}")

    # Retrieve Phonon bands input (matdyn.x)

    ## This allows to list files in the node
    # api_list_url = 'https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/repo/list'.format(
    #    phonons_uuid
    # )
    # inputs = json.loads(urllib.request.urlopen(api_list_url).read())['data']['repo_list']
    # print(inputs)

    api_content_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/repo/contents?filename=%22kpoints.npy%22".format(
        phonons_uuid
    )
    bands_kpts_npy = io.BytesIO(urllib.request.urlopen(api_content_url).read())
    bands_kpts_array = np.load(bands_kpts_npy)

    api_attributes_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}?attributes=true".format(
        phonons_uuid
    )
    attributes = json.loads(urllib.request.urlopen(api_attributes_url).read())["data"][
        "nodes"
    ][0]["attributes"]
    high_symmetry_points = list(zip(attributes["label_numbers"], attributes["labels"]))
    high_symmetry_points_coordinates = [
        bands_kpts_array[sym_kpt[0]] for sym_kpt in high_symmetry_points
    ]
    # [((0, u'G'), array([ 0.,  0.,  0.])), ((49, u'M'), array([ 0.5,  0. ,  0. ])),
    #  ((85, u'K'), array([ 0.33333333,  0.33333333,  0.        ])), ((131, u'G'), array([ 0.,  0.,  0.]))]

    api_inputs_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/links/incoming".format(
        phonons_uuid
    )
    inputs = json.loads(urllib.request.urlopen(api_inputs_url).read())["data"][
        "incoming"
    ]
    matdyn_uuid = inputs[0]["uuid"]  # There is a single creator

    api_inputs_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/links/incoming".format(
        matdyn_uuid
    )
    inputs = json.loads(urllib.request.urlopen(api_inputs_url).read())["data"][
        "incoming"
    ]
    inputs_dict = {inp["link_label"]: inp["uuid"] for inp in inputs}
    force_constants_uuid = inputs_dict["parent_calc_folder"]

    api_content_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/repo/contents?filename=%22real_space_force_constants.dat%22".format(
        force_constants_uuid
    )
    real_force_constants = urllib.request.urlopen(api_content_url).read()

    matdyn_input_file = """&INPUT
  asr = 'simple'
  !do_cutoff_2d = .true.
  fldos = ''
  flfrc = 'real_space_force_constants.dat'
  flfrq = ''
  flvec = 'matdyn.modes'
  q_in_cryst_coord = .true.
  q_in_band_form = .true.
/
"""
    # For now I recompute also lines that should be 'skipped' (e.g. if the band has Y|A, I also compute the
    # Y-A segment). Currently the point is skipped (I could do it) but the phonon visualizer will still display
    # a line (with straight segments) of the length of the Y-A segment, with no selectable points, that is worse
    # (as people might think that there are 'straight' phonon bands).
    # I also hardcode the length of the paths to be 20 points as a compromise between smoothness and file size.
    new_matdyn_lines = []
    current_point_cnt = 0
    final_high_sym_kpts = []
    for (_, kpt_label), kpt_coords in zip(
        high_symmetry_points, high_symmetry_points_coordinates
    ):
        num_points_this_segment = 20
        new_matdyn_lines.append(
            f"{kpt_coords[0]:18.10f} {kpt_coords[1]:18.10f} {kpt_coords[2]:18.10f} {num_points_this_segment}"
        )
        if kpt_label == "G":
            kpt_label = "Γ"
        final_high_sym_kpts.append([current_point_cnt, kpt_label])
        current_point_cnt += num_points_this_segment

    matdyn_input_file += f"{len(new_matdyn_lines)}\n"
    matdyn_input_file += "\n".join(new_matdyn_lines)
    matdyn_input_file += "\n"

    # Retrieve PW inputs and outputs
    api_inputs_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/links/incoming".format(
        force_constants_uuid
    )
    inputs = json.loads(urllib.request.urlopen(api_inputs_url).read())["data"][
        "incoming"
    ]
    q2r_uuid = inputs[0]["uuid"]  # There is a single creator

    api_inputs_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/links/incoming".format(
        q2r_uuid
    )
    inputs = json.loads(urllib.request.urlopen(api_inputs_url).read())["data"][
        "incoming"
    ]
    inputs_dict = {inp["link_label"]: inp["uuid"] for inp in inputs}
    remote_data_uuid = inputs_dict["parent_calc_folder"]

    ##
    api_inputs_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/links/incoming".format(
        remote_data_uuid
    )
    inputs = json.loads(urllib.request.urlopen(api_inputs_url).read())["data"][
        "incoming"
    ]
    calcf_uuid = inputs[0]["uuid"]  # There is a single creator

    api_inputs_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/links/incoming".format(
        calcf_uuid
    )
    inputs = json.loads(urllib.request.urlopen(api_inputs_url).read())["data"][
        "incoming"
    ]
    inputs_dict = {inp["link_label"]: inp["uuid"] for inp in inputs}
    # print(compound, inputs_dict.keys())
    try:
        remote_data_uuid = inputs_dict[
            "retrieved_1"
        ]  # Go to the ph.x of the first q-point
    except KeyError:
        # Some materials follow a different path via a different calcfunction, but
        # the parent of it is still a ph.x so I can just switch which input to follow
        remote_data_uuid = inputs_dict["ph_folder_with_eps"]

    ##
    api_inputs_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/links/incoming".format(
        remote_data_uuid
    )
    inputs = json.loads(urllib.request.urlopen(api_inputs_url).read())["data"][
        "incoming"
    ]
    ph_uuid = inputs[0]["uuid"]  # There is a single creator

    is_still_ph = True
    while is_still_ph:
        api_inputs_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/links/incoming".format(
            ph_uuid
        )
        inputs = json.loads(urllib.request.urlopen(api_inputs_url).read())["data"][
            "incoming"
        ]
        inputs_dict = {inp["link_label"]: inp["uuid"] for inp in inputs}
        remote_data_uuid = inputs_dict["parent_calc_folder"]

        ##
        api_inputs_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/links/incoming".format(
            remote_data_uuid
        )
        inputs = json.loads(urllib.request.urlopen(api_inputs_url).read())["data"][
            "incoming"
        ]
        scf_pw_uuid = inputs[0]["uuid"]  # There is a single creator

        ## We finally got to the SCF!!
        ## Let's now extract the data.

        api_content_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/repo/contents?filename=%22aiida.in%22".format(
            scf_pw_uuid
        )
        scf_input_file = urllib.request.urlopen(api_content_url).read()

        if b"&inputph" in scf_input_file.lower():
            # This is still a PH.x calcualtion - probably there were multiple restarts
            # I mark this as such (and not a SCF pw) and iterate once more in the while loop
            ph_uuid = scf_pw_uuid
        else:
            # I found a non-ph calculation (should be hopefully a PW). I go out of the loop.
            is_still_ph = False

    assert (
        b"calculation = 'scf'" in scf_input_file
    ), f"The parent calculation does not seem to be a SCF for '{compound}', UUID={scf_pw_uuid}"

    api_outputs_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/links/outgoing".format(
        scf_pw_uuid
    )
    outputs = json.loads(urllib.request.urlopen(api_outputs_url).read())["data"][
        "outgoing"
    ]
    outputs_dict = {out["link_label"]: out["uuid"] for out in outputs}
    folder_data_uuid = outputs_dict["retrieved"]

    api_content_url = "https://aiida.materialscloud.org/2dstructures/api/v4/nodes/{}/repo/contents?filename=%22aiida.out%22".format(
        folder_data_uuid
    )
    scf_output_file = urllib.request.urlopen(api_content_url).read()

    return {
        "files": {
            "scf.in": scf_input_file,
            "scf.out": scf_output_file,
            "real_space_force_constants.dat": real_force_constants,
            "matdyn.in": matdyn_input_file.encode("ascii"),
        },
        "uuids": {
            "scf": scf_pw_uuid,
            "matdyn": matdyn_uuid,
            "phonon_bands": phonons_uuid,
            "force_constants": force_constants_uuid,
        },
        "high_symmetry_points": final_high_sym_kpts,
    }


if __name__ == "__main__":

    check_matdyn()

    discover_url = (
        "https://www.materialscloud.org/mcloud/api/v2/discover/2dstructures/compounds"
    )
    discover_data = json.loads(urllib.request.urlopen(discover_url).read())

    # ["AgNO2", "Bi", "BN", "C", "PbI2", "MoS2-MoS2", "P", "PbTe"]:
    for compound in sorted(discover_data["data"]["compounds"].keys()):

        # Problematic cases:
        if compound in [
            # MISSING PHONONS
            "CeSiI",
            "DySBr",
            "DySI",
            "ErHCl",
            "ErSCl",
            "ErSeI",
            "NdOBr",
            "SmOBr",
            "SmSI",
            "TbBr",
            "TbCl",
            "TmOI",
            "YbOBr",
        ]:
            continue

        dest_folder = os.path.join("out-phonons", compound)

        ## Now I have all data, I create a folder and store all files
        ## Skip this material if the destination folder exists
        try:
            os.makedirs(dest_folder, exist_ok=False)
        except FileExistsError:
            if os.path.exists(os.path.join(dest_folder, os.pardir, f"{compound}.json")):
                print(
                    f"> Skipping '{compound}' as destination folder '{dest_folder}' exists."
                )
                continue
            print(
                f"ERROR: Stopping: folder '{dest_folder}' exists but ther is no JSON inside. Remove it to regenerate it."
            )
            sys.exit(1)

        compound_info = get_files_from_materials_cloud(discover_data, compound)

        # I write the content to files
        for filename, content in compound_info["files"].items():
            with open(os.path.join(dest_folder, filename), "wb") as fhandle:
                fhandle.write(content)
        with open(os.path.join(dest_folder, "uuids.json"), "w") as fhandle:
            json.dump(compound_info["uuids"], fhandle)
        print(f"Files written to folder '{dest_folder}'")

        current_dir = os.path.realpath(os.curdir)
        try:
            os.chdir(dest_folder)
            process = subprocess.run(
                [MATDYN_EXECUTABLE, "-in", "matdyn.in"],
                check=False,
                capture_output=True,
                encoding="ascii",
            )
            assert (
                "JOB DONE." in process.stdout
            ), f"matdyn.x mode did not finish correctly... Ouput:\n{process.stdout}"
            assert os.path.exists(
                "matdyn.modes"
            ), f"matdyn.x mode did not generate the matdyn.modes file... Ouput:\n{process.stdout}"
            with open("matdyn.modes") as fhandle:
                matdyn_modes = fhandle.read()
        finally:
            os.chdir(current_dir)

        print("matdyn.x run successfully, matdyn.modes generated.")

        phonons = QePhononQetools(
            scf_input=compound_info["files"]["scf.in"].decode("ascii"),
            scf_output=compound_info["files"]["scf.out"].decode("ascii"),
            matdyn_modes=matdyn_modes,
            highsym_qpts=compound_info["high_symmetry_points"],
            starting_reps=(5, 5, 1),
            reorder=True,
            name=prettify_formula(
                formula=discover_data["data"]["compounds"][compound]["formula"],
                prototype=discover_data["data"]["compounds"][compound]["prototype"],
            ),
        )

        # print(phonons)

        json_fname = os.path.realpath(
            os.path.join(dest_folder, os.pardir, "{}.json".format(compound))
        )
        with open(json_fname, "w") as fhandle:
            data = phonons.get_dict()
            # Remove alat if defined (so there is no message about Quantum ESPRESSO when the JSON file is loaded)
            try:
                data.pop("alat")
            except KeyError:
                pass

            json.dump(data, fhandle)

        print(f"'{json_fname}' file written.")
