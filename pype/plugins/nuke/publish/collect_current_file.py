import pyblish.api
from pype.plugin import PreCollectorOrder


class CollectCurrentFile(pyblish.api.ContextPlugin):
    """Inject the current working file into context"""

    order = PreCollectorOrder - 0.5
    label = "Collect Current File"
    hosts = ["nuke"]

    def process(self, context):
        import os
        import nuke
        current_file = nuke.root().name()

        normalised = os.path.normpath(current_file)

        context.data["current_file"] = normalised
        context.data["currentFile"] = normalised
