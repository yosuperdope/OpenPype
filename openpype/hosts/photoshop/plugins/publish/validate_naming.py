import pyblish.api
import openpype.api
from avalon import photoshop


class ValidateNamingRepair(pyblish.api.Action):
    """Repair the instance asset."""

    label = "Repair"
    icon = "wrench"
    on = "failed"

    def process(self, context, plugin):

        # Get the errored instances
        failed = []
        for result in context.data["results"]:
            if (result["error"] is not None and result["instance"] is not None
                    and result["instance"] not in failed):
                failed.append(result["instance"])

        # Apply pyblish.logic to get the instances for the plug-in
        instances = pyblish.api.instances_by_plugin(failed, plugin)
        stub = photoshop.stub()
        for instance in instances:
            self.log.info("validate_naming instance {}".format(instance))
            name = instance.data["name"].replace(" ", "_")
            name = name.replace(instance.data["family"], '')
            instance[0].Name = name
            data = stub.read(instance[0])
            data["subset"] = "image" + name
            stub.imprint(instance[0], data)

            name = stub.PUBLISH_ICON + name
            stub.rename_layer(instance.data["uuid"], name)

        return True


class ValidateNaming(pyblish.api.InstancePlugin):
    """Validate the instance name.

    Spaces in names are not allowed. Will be replace with underscores.
    """

    label = "Validate Naming"
    hosts = ["photoshop"]
    order = openpype.api.ValidateContentsOrder
    families = ["image"]
    actions = [ValidateNamingRepair]

    def process(self, instance):
        help_msg = ' Use Repair action (A) in Pyblish to fix it.'
        msg = "Name \"{}\" is not allowed.{}".format(instance.data["name"],
                                                     help_msg)
        assert " " not in instance.data["name"], msg

        msg = "Subset \"{}\" is not allowed.{}".format(instance.data["subset"],
                                                       help_msg)
        assert " " not in instance.data["subset"], msg
