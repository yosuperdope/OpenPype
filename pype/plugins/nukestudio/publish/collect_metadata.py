from pyblish import api


class CollectClipMetadata(api.InstancePlugin):
    """Collect Metadata from selected track items."""

    order = api.CollectorOrder + 0.496
    label = "Collect Metadata"
    families = ["plate"]
    hosts = ["nukestudio"]

    def process(self, instance):
        # get basic data
        item = instance.data["item"]

        # get metadata from separate sources
        timeline_md = self.metadata_to_string(dict(item.metadata()))
        mediasource_md = self.metadata_to_string(
            dict(item.source().mediaSource().metadata()))

        # join all metadata
        metadata = dict(mediasource_md, **timeline_md)

        # add metadata to instance
        instance.data["metadata"] = metadata
        instance.data["families"] += ["metadata"]
        self.log.info("Collected Metadata of `source media` and `track item`")
        self.log.debug("Metadata keys: `{}`".format(metadata.keys()))

        return

    def metadata_to_string(self, metadata):
        data = dict()
        for k, v in metadata.items():
            if v not in ["-", ""]:
                data[str(k)] = v

        return data
