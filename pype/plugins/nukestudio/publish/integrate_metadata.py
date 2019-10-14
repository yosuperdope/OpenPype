from pyblish import api
from avalon.io import ObjectId
from pype.nukestudio.tags import create_tag
import datetime

class IntegratePypeMetadata(api.InstancePlugin):
    """Integrate Metadata to clips."""

    order = api.IntegratorOrder + 0.2
    label = "Integrate Metadata"
    families = ["plate"]
    hosts = ["nukestudio"]
    extensions = ["exr", "dpx"]

    def process(self, instance):
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d-%H:%M")
        item = instance.data["item"]
        ins_data_repr = instance.data.get("repreDocs", [])
        instance_repr = [r for r in ins_data_repr
                         if r["context"]["representation"] in self.extensions]

        if instance_repr is []:
            return

        for repr in instance_repr:
            repr_context = repr["context"].copy()
            repr.pop("context", None)

            tag_name = "published_{}".format(timestamp)
            tag_data = {"note": "Published: {}".format(str(now)),
                        "icon": {
                            "path": "pype.png"
                        },
                        "metadata": {
                            "pypeRepresentation": self.serialize(repr),
                            "pypeContext": self.serialize(repr_context)
                            }
                        }
            self.log.info(tag_data.get("icon", {}).get("path", ''))
            # create nks tag and add metadata to the tag
            tag = create_tag(tag_name, tag_data)

            # add the tag to published clip
            item.addTag(tag)

            # create clip with pype representation

        return

    def serialize(self, data):
        """
        Convert all nested content to serialized objects

        Args:
            data (dict): nested data

        Returns:
            dict: nested data
        """

        if isinstance(data, (list or tuple)):
            # loops if list or tuple
            for i, item in enumerate(data):
                data[i] = self.serialize(item)
            return data

        for key, value in data.items():
            if isinstance(value, dict):
                # loops if dictionary
                data[key] = self.serialize(value)

            elif isinstance(value, ObjectId):
                data[key] = str(value)

            elif isinstance(value, unicode):
                data[key] = str(value)

        return data
