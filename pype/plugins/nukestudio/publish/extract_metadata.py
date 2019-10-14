from pyblish import api
from pype import api as pype
import json
import os

class ExtractClipMetadata(pype.Extractor):
    """Extract Metadata from selected track items. Save it as `json` representation"""

    order = api.ExtractorOrder + 0.496
    label = "Extract Metadata"
    families = ["metadata"]
    hosts = ["nukestudio"]

    def process(self, instance):
        # get basic data
        metadata = instance.data["metadata"]
        family = "metadata"
        asset = instance.data["asset"]
        subset = instance.data["subset"]
        staging_dir = self.staging_dir(instance)
        self.log.debug("__ staging_dir: `{}`".format(staging_dir))

        # get json file name
        subset_split = [t.capitalize() for t in pype.split_camelcase(subset)]
        name = family + ''.join(subset_split)
        file = "{0}_{1}.{2}".format(asset, name, "json")
        self.log.debug("__ file: `{}`".format(file))

        # create json file
        self.metadata_to_json(metadata, staging_dir, file)

        # create representaion
        json_repr = {
            'files': file,
            'stagingDir': staging_dir,
            'name': "metadata",
            'ext': "json"
        }
        instance.data["representations"].append(
            json_repr)

        return

    def metadata_to_json(self, data, staging_dir, file):
        with open(os.path.join(staging_dir, file), "w") as outfile:
            outfile.write(json.dumps(data, indent=4, sort_keys=True))
