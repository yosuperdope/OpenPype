from pyblish import api


class CollectClipMetadata(api.InstancePlugin):
    """Collect Metadata from selected track items."""

    order = api.CollectorOrder + 0.011
    label = "Collect Metadata"
    hosts = ["nukestudio"]

    def process(self, instance):
        item = instance.data["item"]
        ti_metadata = self.metadata_to_string(dict(item.metadata()))
        ms_metadata = self.metadata_to_string(
            dict(item.source().mediaSource().metadata()))

        instance.data["metadata"] = dict(ms_metadata, **ti_metadata)

        self.log.info("Collected Metadata of `source media` and `track item`")
        self.log.debug(
            "Metadata keys: `{}`".format(instance.data["metadata"].keys())
        )

        return

    def metadata_to_string(self, metadata):
        data = dict()
        for k, v in metadata.items():
            if v not in ["-", ""]:
                data[str(k)] = v

        return data
