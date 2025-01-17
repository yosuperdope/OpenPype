import os
from openpype.modules import OpenPypeModule
from openpype_interfaces import IPluginPaths


class DeadlineModule(OpenPypeModule, IPluginPaths):
    name = "deadline"

    def __init__(self, manager, settings):
        self.deadline_urls = {}
        super(DeadlineModule, self).__init__(manager, settings)

    def initialize(self, modules_settings):
        # This module is always enabled
        deadline_settings = modules_settings[self.name]
        self.enabled = deadline_settings["enabled"]
        deadline_url = deadline_settings.get("DEADLINE_REST_URL")
        if deadline_url:
            self.deadline_urls = {"default": deadline_url}
        else:
            self.deadline_urls = deadline_settings.get("deadline_urls")  # noqa: E501

        if not self.deadline_urls:
            self.enabled = False
            self.log.warning(("default Deadline Webservice URL "
                              "not specified. Disabling module."))
            return

    def connect_with_modules(self, *_a, **_kw):
        return

    def get_plugin_paths(self):
        """Deadline plugin paths."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return {
            "publish": [os.path.join(current_dir, "plugins", "publish")]
        }
