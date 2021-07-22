import os
import shutil

from openpype.lib import get_workdir
from openpype.settings import (
    get_project_settings,
    get_current_project_settings
)
from openpype import hosts
from avalon import io, api
from avalon.api import AvalonMongoDB

# path to openpype hosts
HOSTS_ROOT = os.path.dirname(hosts.__file__)


def get_workspace(host):
    """ Returns the requested workspace

    Searches the openpype hosts directory for the supplied host. If a 'workspace'
    subdirectory exists, it is returned.

    Arguments:
        host (str): the host name as it appears in the openpype host's directory

    Returns:
        workspace (str): the path to the workspace
    """
    workspace = os.path.join(HOSTS_ROOT, host, 'workspace')
    if not os.path.isdir(workspace):
        print('Could not find workspace for host: {}'.format(host))
        return None
    return workspace


def create_asset_workspaces(project_doc, asset_doc, settings):
    """ Creates all of the workspaces for an asset's tasks

    Operates only on the tasks defined in the project's settings

    Arguments:
        project_doc (dict): project doc that asset belongs to
        asset_doc (dict): asset's doc
        settings (dict): the project's workspace settings
    """
    task_defaults = settings.get('task_defaults')
    tasks = asset_doc.get('data', {}).get('tasks').keys()

    for task in tasks:
        hosts = task_defaults.get(task, [])

        for host in hosts:
            create_workspace(host, project_doc, asset_doc, task)


def create_workspace(host, project_doc, asset_doc, task):
    """ Creates a workspace

    Arguments:
        host (str): name of host as it appears in openpype hosts directory
        project_doc (dict): project doc that asset belongs to
        asset_doc (dict): asset's doc
        task (str): the task to make the workspace for
    """
    workdir_root = get_workdir(project_doc, asset_doc, task, host)
    workspace_src = get_workspace(host)
    if workspace_src:
        copytree(workspace_src, workdir_root)
        print('Asset {}: Created {} workspace for {} task.'.format(
            asset_doc.get('name'), host, task))


def copytree(src, dst, ignore='.gitkeep'):
    """ Recursively copy's directory tree

    Taken from: https://stackoverflow.com/questions/1868714/how-do-i-copy-an-entire-directory-of-files-into-an-existing-directory-using-pyth
    """
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        if item in ignore:
            continue
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, ignore)
        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)


def create_curr_project_workspaces():
    """ Creates all workspaces for the current project

    Wrapper for create_project_workspaces that fills the current project.
    """
    curr_project = os.environ.get('AVALON_PROJECT')
    if not curr_project:
        raise Exception('Could not determine current project.')

    create_project_workspaces(curr_project)


def create_project_workspaces(project):
    """ Creates all workspaces for a given project

    Arguments:
        project (str): The name of a project to create workspaces for
    """
    # retrieve settings
    settings = get_project_settings(project).get('workspace')

    # connect to DB
    dbcon = AvalonMongoDB()

    # get project doc
    project_doc = dbcon.database[project].find_one({"type": "project"})

    # get all assets in the project
    assets = dbcon.database[project].find({"type": "asset"})
    # loop through the assets
    for asset_doc in assets:
        create_asset_workspaces(project_doc, asset_doc, settings)
