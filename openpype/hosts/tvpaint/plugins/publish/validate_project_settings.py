import json

import pyblish.api


class ValidateProjectSettings(pyblish.api.ContextPlugin):
    """Validate project settings against database.
    """

    label = "Validate Project Settings"
    order = pyblish.api.ValidatorOrder
    optional = True

    def process(self, context):
        scene_data = {
            "fps": context.data.get("sceneFps"),
            "resolutionWidth": context.data.get("sceneWidth"),
            "resolutionHeight": context.data.get("sceneHeight"),
            "pixelAspect": context.data.get("scenePixelAspect")
        }
        invalid = {}
        for k in scene_data.keys():
            expected_value = context.data["assetEntity"]["data"][k]
            if scene_data[k] != expected_value:
                invalid[k] = {
                    "current": scene_data[k], "expected": expected_value
                }

        if invalid:
            raise AssertionError(
                "Project settings does not match database:\n{}".format(
                    json.dumps(invalid, sort_keys=True, indent=4)
                )
            )
