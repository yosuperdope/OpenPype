import openpype.hosts.maya.api.plugin
from avalon import api, maya
from maya import cmds
import os
from openpype.api import get_project_settings
from openpype.lib import get_creator_by_name


class ReferenceLoader(openpype.hosts.maya.api.plugin.ReferenceLoader):
    """Load the model"""

    families = ["model",
                "pointcache",
                "animation",
                "mayaAscii",
                "setdress",
                "layout",
                "camera",
                "rig",
                "camerarig",
                "xgen"]
    representations = ["ma", "abc", "fbx", "mb"]

    label = "Reference"
    order = -10
    icon = "code-fork"
    color = "orange"

    # Name of creator class that will be used to create animation instance
    animation_creator_name = "CreateAnimation"

    def process_reference(self, context, name, namespace, options):
        import maya.cmds as cmds
        from avalon import maya
        import pymel.core as pm

        try:
            family = context["representation"]["context"]["family"]
        except ValueError:
            family = "model"

        with maya.maintained_selection():

            groupName = "{}:{}".format(namespace, name)
            cmds.loadPlugin("AbcImport.mll", quiet=True)
            nodes = cmds.file(self.fname,
                              namespace=namespace,
                              sharedReferenceFile=False,
                              groupReference=True,
                              groupName="{}:{}".format(namespace, name),
                              reference=True,
                              returnNewNodes=True)

            # namespace = cmds.referenceQuery(nodes[0], namespace=True)

            shapes = cmds.ls(nodes, shapes=True, long=True)

            newNodes = (list(set(nodes) - set(shapes)))

            current_namespace = pm.namespaceInfo(currentNamespace=True)

            if current_namespace != ":":
                groupName = current_namespace + ":" + groupName

            groupNode = pm.PyNode(groupName)
            roots = set()

            for node in newNodes:
                try:
                    roots.add(pm.PyNode(node).getAllParents()[-2])
                except:  # noqa: E722
                    pass

            if family not in ["layout", "setdress", "mayaAscii"]:
                for root in roots:
                    root.setParent(world=True)

            groupNode.zeroTransformPivots()
            for root in roots:
                root.setParent(groupNode)

            cmds.setAttr(groupName + ".displayHandle", 1)

            settings = get_project_settings(os.environ['AVALON_PROJECT'])
            colors = settings['maya']['load']['colors']
            c = colors.get(family)
            if c is not None:
                groupNode.useOutlinerColor.set(1)
                groupNode.outlinerColor.set(
                    (float(c[0])/255),
                    (float(c[1])/255),
                    (float(c[2])/255)
                )

            self[:] = newNodes

            cmds.setAttr(groupName + ".displayHandle", 1)
            # get bounding box
            bbox = cmds.exactWorldBoundingBox(groupName)
            # get pivot position on world space
            pivot = cmds.xform(groupName, q=True, sp=True, ws=True)
            # center of bounding box
            cx = (bbox[0] + bbox[3]) / 2
            cy = (bbox[1] + bbox[4]) / 2
            cz = (bbox[2] + bbox[5]) / 2
            # add pivot position to calculate offset
            cx = cx + pivot[0]
            cy = cy + pivot[1]
            cz = cz + pivot[2]
            # set selection handle offset to center of bounding box
            cmds.setAttr(groupName + ".selectHandleX", cx)
            cmds.setAttr(groupName + ".selectHandleY", cy)
            cmds.setAttr(groupName + ".selectHandleZ", cz)

            if family == "rig":
                self._post_process_rig(name, namespace, context, options)
            else:
                if "translate" in options:
                    cmds.setAttr(groupName + ".t", *options["translate"])

            return newNodes

    def switch(self, container, representation):
        self.update(container, representation)

    def _post_process_rig(self, name, namespace, context, options):

        output = next((node for node in self if
                       node.endswith("out_SET")), None)
        controls = next((node for node in self if
                         node.endswith("controls_SET")), None)

        assert output, "No out_SET in rig, this is a bug."
        assert controls, "No controls_SET in rig, this is a bug."

        # Find the roots amongst the loaded nodes
        roots = cmds.ls(self[:], assemblies=True, long=True)
        assert roots, "No root nodes in rig, this is a bug."

        asset = api.Session["AVALON_ASSET"]
        dependency = str(context["representation"]["_id"])

        self.log.info("Creating subset: {}".format(namespace))

        # Create the animation instance
        creator_plugin = get_creator_by_name(self.animation_creator_name)
        with maya.maintained_selection():
            cmds.select([output, controls] + roots, noExpand=True)
            api.create(
                creator_plugin,
                name=namespace,
                asset=asset,
                options={"useSelection": True},
                data={"dependencies": dependency}
            )
