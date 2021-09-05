import os
import pyblish.api

from openpype.hosts.houdini.api import lib


class ValidateFileExtension(pyblish.api.InstancePlugin):
    """Validate the output file extension fits the output family.

    File extensions:
        - Pointcache must be .abc
        - Camera must be .abc
        - VDB must be .vdb

    """

    order = pyblish.api.ValidatorOrder
    families = ["pointcache", "camera", "vdbcache"]
    hosts = ["houdini"]
    label = "Output File Extension"

    family_extensions = {
        "pointcache": ".abc",
        "camera": ".abc",
        "vdbcache": ".vdb",
    }

    def process(self, instance):

        invalid = self.get_invalid(instance)
        if invalid:
            raise RuntimeError(
                "ROP node has incorrect " "file extension: %s" % invalid
            )

    @classmethod
    def get_invalid(cls, instance):

        # Get ROP node from instance
        node = instance[0]

        # Create lookup for current family in instance
        families = []
        family = instance.data.get("family", None)
        if family:
            families.append(family)
        families = set(families)

        # Perform extension check
        output = lib.get_output_parameter(node).eval()
        _, output_extension = os.path.splitext(output)

        for family in families:
            extension = cls.family_extensions.get(family, None)
            if extension is None:
                raise RuntimeError("Unsupported family: %s" % family)

            if output_extension != extension:
                return [node.path()]
