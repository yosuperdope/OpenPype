import os

import pyblish.api
from pype.plugin import PreCollectorOrder
from maya import cmds


class CollectMayaWorkspace(pyblish.api.ContextPlugin):
    """Inject the current workspace into context"""

    order = PreCollectorOrder - 0.5
    label = "Maya Workspace"

    hosts = ['maya']
    version = (0, 1, 0)

    def process(self, context):
        workspace = cmds.workspace(rootDirectory=True, query=True)
        if not workspace:
            # Project has not been set. Files will
            # instead end up next to the working file.
            workspace = cmds.workspace(dir=True, query=True)

        # Maya returns forward-slashes by default
        normalised = os.path.normpath(workspace)

        context.set_data('workspaceDir', value=normalised)
