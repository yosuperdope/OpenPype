import pyblish.api


class ValidateUSDOutputNode(pyblish.api.InstancePlugin):
    """Validate the instance USD LOPs Output Node.

    This will ensure:
        - The LOP Path is set.
        - The LOP Path refers to an existing object.
        - The LOP Path node is a LOP node.

    """

    order = pyblish.api.ValidatorOrder
    families = ["usd"]
    hosts = ["houdini"]
    label = "Validate Output Node (USD)"

    def process(self, instance):

        invalid = self.get_invalid(instance)
        if invalid:
            raise RuntimeError(
                "Output node(s) `%s` are incorrect. "
                "See plug-in log for details." % invalid
            )

    @classmethod
    def get_invalid(cls, instance):

        import hou

        output_node = instance.data["output_node"]

        if output_node is None:
            node = instance[0]
            cls.log.error(
                "USD node '%s' LOP path does not exist. "
                "Ensure a valid LOP path is set." % node.path()
            )

            return [node.path()]

        # Output node must be a Sop node.
        if not isinstance(output_node, hou.LopNode):
            cls.log.error(
                "Output node %s is not a LOP node. "
                "LOP Path must point to a LOP node, "
                "instead found category type: %s"
                % (output_node.path(), output_node.type().category().name())
            )
            return [output_node.path()]
