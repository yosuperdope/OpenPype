import collections
import ftrack_api
from pype.modules.ftrack.lib import BaseAction, statics_icon
from pype.modules.ftrack.lib.avalon_sync import get_avalon_attr


class CleanHierarchicalAttrsAction(BaseAction):
    identifier = "clean.hierarchical.attr"
    label = "Pype Admin"
    variant = "- Clean hierarchical custom attributes"
    description = "Unset empty hierarchical attribute values."
    role_list = ["Pypeclub", "Administrator", "Project Manager"]
    icon = statics_icon("ftrack", "action_icons", "PypeAdmin.svg")

    cust_attr_query = (
        "select value, entity_id from CustomAttributeValue "
        "where entity_id in ({}) and configuration_id is \"{}\""
    )

    def discover(self, session, entities, event):
        """Show only on project entity."""
        valid_ids = []
        for entity_info in event["data"].get("selection", []):
            if entity_info["entityType"].lower() in ("task", "show"):
                valid_ids.append(entity_info["entityId"])

        for entity in entities:
            if (
                entity["id"] in valid_ids
                and entity.entity_type.lower() != "task"
            ):
                return True

        return False

    def launch(self, session, entities, event):
        event_entities = event["data"].get("selection", [])
        self.log.debug(
            "Filtering selected entities to process. {}".format(event_entities)
        )

        filtered_entities = [
            entity for entity in entities
            if entity.entity_type.lower() != "task"
        ]

        if not filtered_entities:
            # This should never happen if launched from ftrack...
            msg = "None of selected entities is valid for this action."
            self.log.info(msg)
            return {
                "success": False,
                "message": msg
            }

        # Show message to user
        msg = (
            "Preparing entities for cleanup. This may take some time."
        )
        self.log.debug(msg)
        self.show_message(event, msg, result=True)

        entity_ids = [
            entity["id"] for entity in filtered_entities
        ]
        joined_entity_ids = ", ".join(entity_ids)
        self.log.debug("Collected {} entities to process. {}".format(
            len(entity_ids), joined_entity_ids
        ))

        attrs, hier_attrs = get_avalon_attr(session)

        max_len = 0
        for attr in hier_attrs:
            key = attr["key"]
            if len(key) > max_len:
                max_len = len(key)

        for attr in hier_attrs:
            configuration_id = attr["id"]
            call_expr = [{
                "action": "query",
                "expression": self.cust_attr_query.format(
                    joined_entity_ids, configuration_id
                )
            }]

            [values] = self.session.call(call_expr)

            data = {}
            for item in values["data"]:
                value = item["value"]
                if value is None:
                    data[item["entity_id"]] = value

            if not data:
                self.log.debug("{} - nothing to clean".format(
                    attr["key"].ljust(max_len)
                ))
                continue

            changes_len = len(data)
            ending = ""
            if changes_len > 1:
                ending += "s"
            self.log.debug("{} - cleaning up {} value{}.".format(
                attr["key"].ljust(max_len), changes_len, ending
            ))
            for entity_id, value in data.items():
                entity_key = collections.OrderedDict({
                    "configuration_id": configuration_id,
                    "entity_id": entity_id
                })
                session.recorded_operations.push(
                    ftrack_api.operation.DeleteEntityOperation(
                        "CustomAttributeValue",
                        entity_key
                    )
                )
            session.commit()

        return True


def register(session, plugins_presets={}):
    '''Register plugin. Called when used as an plugin.'''

    CleanHierarchicalAttrsAction(session, plugins_presets).register()
