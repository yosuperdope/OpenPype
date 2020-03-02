import os
import pyblish.api
from pype.plugin import PreCollectorOrder


class CollectCurrentUserPype(pyblish.api.ContextPlugin):
    """Inject the currently logged on user into the Context"""

    # Order must be after default pyblish-base CollectCurrentUser
    order = PreCollectorOrder + 0.001
    label = "Collect Pype User"

    def process(self, context):
        user = os.getenv("PYPE_USERNAME", "").strip()
        if not user:
            return

        context.data["user"] = user
        self.log.debug("Pype user is \"{}\"".format(user))
