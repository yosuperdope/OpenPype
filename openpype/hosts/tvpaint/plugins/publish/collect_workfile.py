import os
import json
import pyblish.api
from avalon import io

from openpype.lib import get_subset_name


class CollectWorkfile(pyblish.api.ContextPlugin):
    label = "Collect Workfile"
    order = pyblish.api.CollectorOrder - 0.4
    hosts = ["tvpaint"]

    def process(self, context):
        current_file = context.data["currentFile"]

        self.log.info(
            "Workfile path used for workfile family: {}".format(current_file)
        )

        dirpath, filename = os.path.split(current_file)
        basename, ext = os.path.splitext(filename)
        instance = context.create_instance(name=basename)

        # Get subset name of workfile instance
        # Collect asset doc to get asset id
        # - not sure if it's good idea to require asset id in
        #   get_subset_name?
        family = "workfile"
        asset_name = context.data["workfile_context"]["asset"]
        asset_doc = io.find_one(
            {
                "type": "asset",
                "name": asset_name
            },
            {"_id": 1}
        )
        asset_id = None
        if asset_doc:
            asset_id = asset_doc["_id"]

        # Project name from workfile context
        project_name = context.data["workfile_context"]["project"]
        # Host name from environemnt variable
        host_name = os.environ["AVALON_APP"]
        # Use empty variant value
        variant = ""
        task_name = io.Session["AVALON_TASK"]
        subset_name = get_subset_name(
            family,
            variant,
            task_name,
            asset_id,
            project_name,
            host_name
        )

        # Create Workfile instance
        instance.data.update({
            "subset": subset_name,
            "asset": context.data["asset"],
            "label": subset_name,
            "publish": True,
            "family": "workfile",
            "families": ["workfile"],
            "representations": [{
                "name": ext.lstrip("."),
                "ext": ext.lstrip("."),
                "files": filename,
                "stagingDir": dirpath
            }]
        })
        self.log.info("Collected workfile instance: {}".format(
            json.dumps(instance.data, indent=4)
        ))
