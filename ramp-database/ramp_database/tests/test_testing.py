import os
import shutil

import pytest
from git.exc import GitCommandError

from ramp_utils import read_config
from ramp_utils import generate_ramp_config

from ramp_utils.testing import database_config_template
from ramp_utils.testing import ramp_config_template

from ramp_database.utils import setup_db
from ramp_database.utils import session_scope

from ramp_database.model import Model

from ramp_database.exceptions import NameClashError

from ramp_database.tools.user import get_user_by_name
from ramp_database.tools.event import get_problem

from ramp_database.testing import create_test_db
from ramp_database.testing import add_events
from ramp_database.testing import add_users
from ramp_database.testing import add_problems
from ramp_database.testing import setup_ramp_kits_ramp_data
from ramp_database.testing import sign_up_teams_to_events
from ramp_database.testing import submit_all_starting_kits


@pytest.fixture(scope='module')
def database_config():
    return read_config(database_config_template())


@pytest.fixture(scope='module')
def ramp_config():
    return read_config(ramp_config_template())


@pytest.fixture
def session_scope_function(database_config, ramp_config):
    try:
        create_test_db(database_config, ramp_config)
        with session_scope(database_config['sqlalchemy']) as session:
            yield session
    finally:
        shutil.rmtree(
            ramp_config['ramp']['deployment_dir'], ignore_errors=True
        )
        db, _ = setup_db(database_config['sqlalchemy'])
        Model.metadata.drop_all(db)


def test_ramp_kits_ramp_data(session_scope_function, ramp_config):
    setup_ramp_kits_ramp_data(ramp_config, 'iris')
    msg_err = 'The RAMP kit repository was previously cloned.'
    with pytest.raises(ValueError, match=msg_err):
        setup_ramp_kits_ramp_data(ramp_config, 'iris')

    # retrieve the path to the ramp kit to remove it
    internal_ramp_config = generate_ramp_config(ramp_config)
    shutil.rmtree(os.path.join(internal_ramp_config['ramp_kits_dir'], 'iris'))
    msg_err = 'The RAMP data repository was previously cloned.'
    with pytest.raises(ValueError, match=msg_err):
        setup_ramp_kits_ramp_data(ramp_config, 'iris')
    setup_ramp_kits_ramp_data(ramp_config, 'iris', force=True)


def test_add_users(session_scope_function):
    add_users(session_scope_function)
    users = get_user_by_name(session_scope_function, None)
    for user in users:
        assert user.name in ('test_user', 'test_user_2', 'test_iris_admin')
    err_msg = 'username is already in use'
    with pytest.raises(NameClashError, match=err_msg):
        add_users(session_scope_function)


def test_add_problems(session_scope_function, ramp_config):
    add_problems(session_scope_function, ramp_config)
    problems = get_problem(session_scope_function, None)
    for problem in problems:
        assert problem.name in ('iris', 'boston_housing')
    # trying to add twice the same problem will raise a git error since the
    # repositories already exist.
    msg_err = 'The RAMP kit repository was previously cloned.'
    with pytest.raises(ValueError, match=msg_err):
        add_problems(session_scope_function, ramp_config)


def test_add_events(session_scope_function, ramp_config):
    add_problems(session_scope_function, ramp_config)
    add_events(session_scope_function, ramp_config)
    with pytest.raises(ValueError):
        add_events(session_scope_function, ramp_config)


def test_sign_up_team_to_events(session_scope_function, ramp_config):
    add_users(session_scope_function)
    add_problems(session_scope_function, ramp_config)
    add_events(session_scope_function, ramp_config)
    sign_up_teams_to_events(session_scope_function)


def test_submit_all_starting_kits(session_scope_function, ramp_config):
    add_users(session_scope_function)
    add_problems(session_scope_function, ramp_config)
    add_events(session_scope_function, ramp_config)
    sign_up_teams_to_events(session_scope_function)
    submit_all_starting_kits(session_scope_function, ramp_config)
