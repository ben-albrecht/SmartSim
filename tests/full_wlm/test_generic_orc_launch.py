import pytest

from smartsim import Experiment, status

# retrieved from pytest fixtures
if pytest.test_launcher not in pytest.wlm_options:
    pytestmark = pytest.mark.skip(reason="Not testing WLM integrations")

def test_launch_orc_auto(fileutils, wlmutils):
    """test single node orchestrator"""
    launcher = wlmutils.get_test_launcher()

    exp_name = "test-launch-auto-orc"
    exp = Experiment(exp_name, launcher=launcher)
    test_dir = fileutils.make_test_dir(exp_name)

    # batch = False to launch on existing allocation
    network_interface = wlmutils.get_test_interface()
    orc = exp.create_orchestrator(6780,
                                  batch=False, 
                                  interface=network_interface, 
                                  single_cmd=False)
    orc.set_path(test_dir)

    exp.start(orc, block=True)
    statuses = exp.get_status(orc)

    # don't use assert so that we don't leave an orphan process
    if status.STATUS_FAILED in statuses:
        exp.stop(orc)
        assert False

    exp.stop(orc)
    statuses = exp.get_status(orc)
    assert all([stat == status.STATUS_CANCELLED for stat in statuses])


def test_launch_slurm_cluster_orc(fileutils, wlmutils):
    """test clustered 3-node orchestrator"""
    # TODO detect number of nodes in allocation and skip if not sufficent
    launcher = wlmutils.get_test_launcher()

    exp_name = "test-launch-auto-cluster-orc"
    exp = Experiment(exp_name, launcher=launcher)
    test_dir = fileutils.make_test_dir(exp_name)

    # batch = False to launch on existing allocation
    network_interface = wlmutils.get_test_interface()
    orc = exp.create_orchestrator(6780, db_nodes=3, batch=False, interface=network_interface, single_cmd=True)
    orc.set_path(test_dir)

    exp.start(orc, block=True)
    statuses = exp.get_status(orc)

    # don't use assert so that orc we don't leave an orphan process
    if status.STATUS_FAILED in statuses:
        exp.stop(orc)
        assert False

    exp.stop(orc)
    statuses = exp.get_status(orc)
    assert all([stat == status.STATUS_CANCELLED for stat in statuses])