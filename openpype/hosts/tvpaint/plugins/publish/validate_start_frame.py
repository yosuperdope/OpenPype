import pyblish.api
from avalon.tvpaint import lib


class RepairStartFrame(pyblish.api.Action):
    """Repair start frame."""

    label = "Repair"
    icon = "wrench"
    on = "failed"

    def process(self, context, plugin):
        lib.execute_george("tv_startframe 0")


class ValidateStartFrame(pyblish.api.ContextPlugin):
    """Validate start frame being at frame 0."""

    label = "Validate Start Frame"
    order = pyblish.api.ValidatorOrder
    hosts = ["tvpaint"]
    actions = [RepairStartFrame]
    optional = True

    def process(self, context):
        start_frame = lib.execute_george("tv_startframe")
        assert int(start_frame) == 0, "Start frame has to be frame 0."
