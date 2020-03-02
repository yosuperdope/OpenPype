from maya import cmds

import pyblish.api
from pype.plugin import PreCollectorOrder


class CollectMayaCurrentFile(pyblish.api.ContextPlugin):
    """Inject the current working file into context"""

    order = PreCollectorOrder - 0.5
    label = "Maya Current File"
    hosts = ['maya']

    def process(self, context):
        """Inject the current working file"""
        current_file = cmds.file(query=True, sceneName=True)
        context.data['currentFile'] = current_file
