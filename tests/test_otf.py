import pytest
import os

import glob
import re
import shutil
import numpy as np

from flare.otf import OTF
from flare.otf_parser import OtfAnalysis
from flare.gp import GaussianProcess
from flare.struc import Structure


cmd = {"cp2k": "CP2K_COMMAND", "qe": "PWSCF_COMMAND"}
software_list = ["cp2k", "qe"]
example_list = [1, 2]
name_list = {1: "h2", 2: "al"}

dt = 0.0001
number_of_steps = 3

print("running test_otf.py")
print("current working directory:")
print(os.getcwd())


def get_gp(par=False, per_atom_par=False, n_cpus=1):
    hyps = np.array([1, 1, 1, 1, 1])
    hyp_labels = [
        "Signal Std 2b",
        "Length Scale 2b",
        "Signal Std 3b",
        "Length Scale 3b",
        "Noise Std",
    ]
    cutoffs = {"twobody": 4, "threebody": 4}
    return GaussianProcess(
        kernel_name="23mc",
        hyps=hyps,
        cutoffs=cutoffs,
        hyp_labels=hyp_labels,
        maxiter=50,
        par=par,
        per_atom_par=per_atom_par,
        n_cpus=n_cpus,
    )


def cleanup(software="qe", casename="h2_otf_cp2k"):

    for f in glob.glob(f"{casename}*"):
        os.remove(f)
    for f in glob.glob(f"*{software}.in"):
        os.remove(f)
    for f in glob.glob(f"*{software}.out"):
        os.remove(f)

    if software == "qe":
        for f in glob.glob(f"pwscf.wfc*"):
            os.remove(f)
        for f in glob.glob(f"*pwscf.out"):
            os.remove(f)
        for f in os.listdir("./"):
            if f in ["pwscf.save"]:
                shutil.rmtree(f)
    else:
        for f in os.listdir("./"):
            for f in glob.glob(f"{software}*"):
                os.remove(f)


@pytest.mark.parametrize("software", software_list)
@pytest.mark.parametrize("example", example_list)
def test_otf(software, example):
    """
    Test that an otf run can survive going for more steps
    :return:
    """

    print("running test_otf.py")
    print("current working directory:")
    print(os.getcwd())

    outdir = f"test_outputs_{software}"
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)

    if not os.environ.get(cmd[software], False):
        pytest.skip(
            f"{cmd[software]} not found in environment:"
            " Please install the code "
            f" and set the {cmd[software]} env. "
            "variable to point to the executable."
        )

    dft_input = f"{software}.in"
    dft_output = f"{software}.out"
    shutil.copy(f"./test_files/{software}_input_{example}.in", dft_input)

    dft_loc = os.environ.get(cmd[software])
    std_tolerance_factor = 0.5

    casename = name_list[example]

    gp = get_gp()

    otf = OTF(
        dt=dt,
        number_of_steps=number_of_steps,
        gp=gp,
        write_model=3,
        std_tolerance_factor=std_tolerance_factor,
        init_atoms=[0],
        calculate_energy=True,
        max_atoms_added=1,
        freeze_hyps=1,
        skip=1,
        force_source=software,
        dft_input=dft_input,
        dft_loc=dft_loc,
        dft_output=dft_output,
        output_name=f"{casename}_otf_{software}",
        store_dft_output=([dft_output, dft_input], "."),
    )

    otf.run()


@pytest.mark.parametrize("software", software_list)
@pytest.mark.parametrize("per_atom_par", [True, False])
@pytest.mark.parametrize("n_cpus", [2])
def test_otf_par(software, per_atom_par, n_cpus):
    """
    Test that an otf run can survive going for more steps
    :return:
    """

    example = 1
    outdir = f"test_outputs_{software}"
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)

    print("running test_otf.py")
    print("current working directory:")
    print(os.getcwd())

    if not os.environ.get(cmd[software], False):
        pytest.skip(
            f"{cmd[software]} not found in environment:"
            " Please install the code "
            f" and set the {cmd[software]} env. "
            "variable to point to the executable."
        )
    if software == "cp2k":
        if "popt" not in os.environ.get(cmd[software]):
            pytest.skip(f"cp2k is serial version skipping the parallel test")

    dft_input = f"{software}.in"
    dft_output = f"{software}.out"
    shutil.copy(f"./test_files/{software}_input_{example}.in", dft_input)

    dft_loc = os.environ.get(cmd[software])
    std_tolerance_factor = -0.1

    casename = name_list[example]

    gp = get_gp(par=True, n_cpus=n_cpus, per_atom_par=per_atom_par)

    otf = OTF(
        dt=dt,
        number_of_steps=number_of_steps,
        gp=gp,
        write_model=3,
        std_tolerance_factor=std_tolerance_factor,
        init_atoms=[0],
        calculate_energy=True,
        max_atoms_added=1,
        n_cpus=n_cpus,
        freeze_hyps=1,
        skip=1,
        mpi="mpi",
        force_source=software,
        dft_input=dft_input,
        dft_loc=dft_loc,
        dft_output=dft_output,
        output_name=f"{casename}_otf_{software}",
        store_dft_output=([dft_output, dft_input], "."),
    )

    otf.run()
    pytest.my_otf = otf


@pytest.mark.parametrize("software", software_list)
def test_otf_parser(software):

    if not os.environ.get(cmd[software], False):
        pytest.skip(
            f"{cmd[software]} not found in environment:"
            " Please install the code "
            f" and set the {cmd[software]} env. "
            "variable to point to the executable."
        )

    example = 1
    casename = name_list[example]
    output_name = f"{casename}_otf_{software}.out"
    otf_traj = OtfAnalysis(output_name)
    replicated_gp = otf_traj.make_gp()

    # TODO: debug cp2k
    if software == "cp2k":
        pytest.skip()

    otf = pytest.my_otf
    assert otf.dft_count == len(otf_traj.gp_position_list)
    assert otf.curr_step == len(otf_traj.position_list) + 1
    assert otf.dft_count == len(otf_traj.gp_thermostat["temperature"])
    assert otf.curr_step == len(otf_traj.thermostat["temperature"]) + 1

    if otf_traj.gp_cell_list:
        assert otf.dft_count == len(otf_traj.gp_cell_list)


@pytest.mark.parametrize("software", software_list)
def test_load_checkpoint(software):

    if not os.environ.get(cmd[software], False):
        pytest.skip(
            f"{cmd[software]} not found in environment:"
            " Please install the code "
            f" and set the {cmd[software]} env. "
            "variable to point to the executable."
        )

    if software == "cp2k":
        pytest.skip()

    example = 1
    casename = name_list[example]
    log_name = f"{casename}_otf_{software}"
    new_otf = OTF.from_checkpoint(log_name + "_checkpt.json")
    print("loaded from checkpoint", log_name)
    assert new_otf.curr_step == number_of_steps
    new_otf.number_of_steps = new_otf.number_of_steps + 2
    new_otf.run()


@pytest.mark.parametrize("software", software_list)
def test_otf_parser_from_checkpt(software):

    if not os.environ.get(cmd[software], False):
        pytest.skip(
            f"{cmd[software]} not found in environment:"
            " Please install the code "
            f" and set the {cmd[software]} env. "
            "variable to point to the executable."
        )

    if software == "cp2k":
        pytest.skip()

    example = 1
    casename = name_list[example]
    log_name = f"{casename}_otf_{software}"
    output_name = f"{log_name}.out"
    otf_traj = OtfAnalysis(output_name)
    try:
        replicated_gp = otf_traj.make_gp()
    except Exception:
        init_gp = GaussianProcess.from_file(log_name + "_gp.json")
        replicated_gp = otf_traj.make_gp(init_gp=init_gp)

    outdir = f"test_outputs_{software}"
    if not os.path.isdir(outdir):
        os.mkdir(outdir)
    for f in os.listdir("./"):
        if f"{casename}_otf_{software}" in f:
            shutil.move(f, outdir)
    cleanup(software, f"{casename}_otf_{software}")
