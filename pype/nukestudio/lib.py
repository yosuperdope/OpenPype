import os
import sys
import hiero
import pyblish.api
from avalon import io
import avalon.api as avalon
from avalon.vendor.Qt import (QtCore, QtWidgets, QtGui)
from avalon.vendor import qtawesome as qta

import pype.api as pype
from pypeapp import Logger


log = Logger().get_logger(__name__, "nukestudio")

cached_process = None


self = sys.modules[__name__]
self._window = None
self._has_been_setup = False
self._has_menu = False
self._registered_gui = None

AVALON_CONFIG = os.getenv("AVALON_CONFIG", "pype")


def set_workfiles():
    ''' Wrapping function for workfiles launcher '''
    from avalon.tools import workfiles

    # import session to get project dir
    S = avalon.Session
    active_project_root = os.path.normpath(
        os.path.join(S['AVALON_PROJECTS'], S['AVALON_PROJECT'])
    )
    workdir = os.environ["AVALON_WORKDIR"]

    # show workfile gui
    workfiles.show(workdir)

    # getting project
    project = hiero.core.projects()[-1]

    # set project root with backward compatibility
    try:
        project.setProjectDirectory(active_project_root)
    except Exception:
        # old way of seting it
        project.setProjectRoot(active_project_root)

    # get project data from avalon db
    project_data = pype.get_project()["data"]

    log.info("project_data: {}".format(project_data))

    # get format and fps property from avalon db on project
    width = project_data["resolutionWidth"]
    height = project_data["resolutionHeight"]
    pixel_aspect = project_data["pixelAspect"]
    fps = project_data['fps']
    format_name = project_data['code']

    # create new format in hiero project
    format = hiero.core.Format(width, height, pixel_aspect, format_name)
    project.setOutputFormat(format)

    # set fps to hiero project
    project.setFramerate(fps)

    # TODO: add auto colorspace set from project drop
    log.info("Project properties has been synchronised from Avalon db")


def reload_config():
    """Attempt to reload pipeline at run-time.

    CAUTION: This is primarily for development and debugging purposes.

    """

    import importlib

    for module in (
        "{}.api".format(AVALON_CONFIG),
        "{}.templates".format(AVALON_CONFIG),
        "{}.nukestudio.lib".format(AVALON_CONFIG),
        "{}.nukestudio.menu".format(AVALON_CONFIG),
        "{}.nukestudio.tags".format(AVALON_CONFIG)
    ):
        log.info("Reloading module: {}...".format(module))
        try:
            module = importlib.import_module(module)
            reload(module)
        except Exception as e:
            log.warning("Cannot reload module: {}".format(e))
            importlib.reload(module)


def setup(console=False, port=None, menu=True):
    """Setup integration

    Registers Pyblish for Hiero plug-ins and appends an item to the File-menu

    Arguments:
        console (bool): Display console with GUI
        port (int, optional): Port from which to start looking for an
            available port to connect with Pyblish QML, default
            provided by Pyblish Integration.
        menu (bool, optional): Display file menu in Hiero.
    """

    if self._has_been_setup:
        teardown()

    add_submission()

    if menu:
        add_to_filemenu()
        self._has_menu = True

    self._has_been_setup = True
    print("pyblish: Loaded successfully.")


def show():
    """Try showing the most desirable GUI
    This function cycles through the currently registered
    graphical user interfaces, if any, and presents it to
    the user.
    """

    return (_discover_gui() or _show_no_gui)()


def _discover_gui():
    """Return the most desirable of the currently registered GUIs"""

    # Prefer last registered
    guis = reversed(pyblish.api.registered_guis())

    for gui in list(guis) + ["pyblish_lite"]:
        try:
            gui = __import__(gui).show
        except (ImportError, AttributeError):
            continue
        else:
            return gui


def teardown():
    """Remove integration"""
    if not self._has_been_setup:
        return

    if self._has_menu:
        remove_from_filemenu()
        self._has_menu = False

    self._has_been_setup = False
    print("pyblish: Integration torn down successfully")


def remove_from_filemenu():
    raise NotImplementedError("Implement me please.")


def add_to_filemenu():
    # PublishAction()
    # ClipContextAction()
    return


class PyblishSubmission(hiero.exporters.FnSubmission.Submission):

    def __init__(self):
        hiero.exporters.FnSubmission.Submission.__init__(self)

    def addToQueue(self):
        # Add submission to Hiero module for retrieval in plugins.
        hiero.submission = self
        show()


def add_submission():
    registry = hiero.core.taskRegistry
    registry.addSubmission("Pyblish", PyblishSubmission)


class PublishAction(QtWidgets.QAction):
    """
    Action with is showing as menu item
    """

    def __init__(self):
        QtWidgets.QAction.__init__(self, "Publish", None)
        self.triggered.connect(self.publish)

        for interest in ["kShowContextMenu/kTimeline",
                         "kShowContextMenukBin",
                         "kShowContextMenu/kSpreadsheet"]:
            hiero.core.events.registerInterest(interest, self.eventHandler)
            log.info("___ interest: `{}`".format(interest))
            log.info("___ actionHandler: `{}`".format(self.eventHandler))

        self.setShortcut("Ctrl+Alt+P")

    def publish(self):
        # Removing "submission" attribute from hiero module, to prevent tasks
        # from getting picked up when not using the "Export" dialog.
        if hasattr(hiero, "submission"):
            del hiero.submission
        show()

    def eventHandler(self, event):
        # Add the Menu to the right-click menu
        event.menu.addAction(self)


class ClipContextAction(QtWidgets.QAction):
    """
    Action with is showing Clip context in context menu
    """
    def __init__(self):
        QtWidgets.QAction.__init__(self, "Clip Context", None)
        self.triggered.connect(self.clip_context)

        for interest in ["kShowContextMenu/kTimeline",
                         "kShowContextMenu/kBin",
                         "kShowContextMenu/kSpreadsheet"]:
            hiero.core.events.registerInterest(interest, self.eventHandler)

        self.setShortcut("Ctrl+Shift+Alt+C")

    def clip_context(self):
        print("Testing the action")

    def eventHandler(self, event):
        # Add the Menu to the right-click menu
        event.menu.addAction(self)


def _show_no_gui():
    """
    Popup with information about how to register a new GUI
    In the event of no GUI being registered or available,
    this information dialog will appear to guide the user
    through how to get set up with one.
    """

    messagebox = QtWidgets.QMessageBox()
    messagebox.setIcon(messagebox.Warning)
    messagebox.setWindowIcon(QtGui.QIcon(os.path.join(
        os.path.dirname(pyblish.__file__),
        "icons",
        "logo-32x32.svg"))
    )

    spacer = QtWidgets.QWidget()
    spacer.setMinimumSize(400, 0)
    spacer.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
                         QtWidgets.QSizePolicy.Expanding)

    layout = messagebox.layout()
    layout.addWidget(spacer, layout.rowCount(), 0, 1, layout.columnCount())

    messagebox.setWindowTitle("Uh oh")
    messagebox.setText("No registered GUI found.")

    if not pyblish.api.registered_guis():
        messagebox.setInformativeText(
            "In order to show you a GUI, one must first be registered. "
            "Press \"Show details...\" below for information on how to "
            "do that.")

        messagebox.setDetailedText(
            "Pyblish supports one or more graphical user interfaces "
            "to be registered at once, the next acting as a fallback to "
            "the previous."
            "\n"
            "\n"
            "For example, to use Pyblish Lite, first install it:"
            "\n"
            "\n"
            "$ pip install pyblish-lite"
            "\n"
            "\n"
            "Then register it, like so:"
            "\n"
            "\n"
            ">>> import pyblish.api\n"
            ">>> pyblish.api.register_gui(\"pyblish_lite\")"
            "\n"
            "\n"
            "The next time you try running this, Lite will appear."
            "\n"
            "See http://api.pyblish.com/register_gui.html for "
            "more information.")

    else:
        messagebox.setInformativeText(
            "None of the registered graphical user interfaces "
            "could be found."
            "\n"
            "\n"
            "Press \"Show details\" for more information.")

        messagebox.setDetailedText(
            "These interfaces are currently registered."
            "\n"
            "%s" % "\n".join(pyblish.api.registered_guis()))

    messagebox.setStandardButtons(messagebox.Ok)
    messagebox.exec_()


def CreateNukeWorkfile(nodes=None,
                       nodes_effects=None,
                       to_timeline=False,
                       **kwargs):
    ''' Creating nuke workfile with particular version with given nodes
    Also it is creating timeline track items as precomps.

    Arguments:
        nodes(list of dict): each key in dict is knob order is important
        to_timeline(type): will build trackItem with metadata

    Returns:
        bool: True if done

    Raises:
        Exception: with traceback

    '''
    import hiero.core
    from avalon.nuke import imprint
    from pype.nuke import (
        lib as nklib
        )

    # check if the file exists if does then Raise "File exists!"
    if os.path.exists(filepath):
        raise FileExistsError("File already exists: `{}`".format(filepath))

    # if no representations matching then
    #   Raise "no representations to be build"
    if len(representations) == 0:
        raise AttributeError("Missing list of `representations`")

    # check nodes input
    if len(nodes) == 0:
        log.warning("Missing list of `nodes`")

    # create temp nk file
    nuke_script = hiero.core.nuke.ScriptWriter()

    # create root node and save all metadata
    root_node = hiero.core.nuke.RootNode()

    root_path = os.environ["AVALON_PROJECTS"]

    nuke_script.addNode(root_node)

    # here to call pype.nuke.lib.BuildWorkfile
    script_builder = nklib.BuildWorkfile(
                                root_node=root_node,
                                root_path=root_path,
                                nodes=nuke_script.getNodes(),
                                **kwargs
                                )


class SearchComboBox(QtWidgets.QComboBox):
    """Searchable ComboBox with empty placeholder value as first value"""

    def __init__(self, parent=None, placeholder=""):
        super(SearchComboBox, self).__init__(parent)

        self.setEditable(True)
        self.setInsertPolicy(self.NoInsert)
        self.lineEdit().setPlaceholderText(placeholder)

        # Apply completer settings
        completer = self.completer()
        completer.setCompletionMode(completer.PopupCompletion)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

        # Force style sheet on popup menu
        # It won't take the parent stylesheet for some reason
        # todo: better fix for completer popup stylesheet
        if self._window:
            popup = completer.popup()
            popup.setStyleSheet(self._window.styleSheet())

    def populate(self, items):
        self.clear()
        self.addItems([""])     # ensure first item is placeholder
        self.addItems(items)

    def get_valid_value(self):
        """Return the current text if it's a valid value else None

        Note: The empty placeholder value is valid and returns as ""

        """

        text = self.currentText()
        lookup = set(self.itemText(i) for i in range(self.count()))
        if text not in lookup:
            return None

        return text


class SwitchAssetDialog(QtWidgets.QDialog):
    """Widget to support asset switching"""

    switched = QtCore.Signal()

    def __init__(self, parent=None, items=None):
        QtWidgets.QDialog.__init__(self, parent)

        self.setModal(True)  # Force and keep focus dialog

        self.log = log.getLogger(self.__class__.__name__)

        self._items = items

        self._assets_box = SearchComboBox(placeholder="<asset>")
        self._subsets_box = SearchComboBox(placeholder="<subset>")
        self._representations_box = SearchComboBox(
            placeholder="<representation>")

        self._asset_label = QtWidgets.QLabel('')
        self._subset_label = QtWidgets.QLabel('')
        self._repre_label = QtWidgets.QLabel('')

        main_layout = QtWidgets.QVBoxLayout()
        context_layout = QtWidgets.QHBoxLayout()
        asset_layout = QtWidgets.QVBoxLayout()
        subset_layout = QtWidgets.QVBoxLayout()
        repre_layout = QtWidgets.QVBoxLayout()

        accept_icon = qta.icon("fa.check", color="white")
        accept_btn = QtWidgets.QPushButton()
        accept_btn.setIcon(accept_icon)
        accept_btn.setFixedWidth(24)
        accept_btn.setFixedHeight(24)

        asset_layout.addWidget(self._assets_box)
        asset_layout.addWidget(self._asset_label)
        subset_layout.addWidget(self._subsets_box)
        subset_layout.addWidget(self._subset_label)
        repre_layout.addWidget(self._representations_box)
        repre_layout.addWidget(self._repre_label)

        context_layout.addLayout(asset_layout)
        context_layout.addLayout(subset_layout)
        context_layout.addLayout(repre_layout)
        context_layout.addWidget(accept_btn)

        self._accept_btn = accept_btn

        self._assets_box.currentIndexChanged.connect(self.on_assets_change)
        self._subsets_box.currentIndexChanged.connect(self.on_subset_change)
        self._representations_box.currentIndexChanged.connect(
            self.on_repre_change
        )

        main_layout.addLayout(context_layout)
        self.setLayout(main_layout)
        self.setWindowTitle("Switch selected items ...")

        self.connections()

        self.refresh()

        self.setFixedSize(self.sizeHint())  # Lock window size

        # Set default focus to accept button so you don't directly type in
        # first asset field, this also allows to see the placeholder value.
        accept_btn.setFocus()

    def connections(self):
        self._accept_btn.clicked.connect(self._on_accept)

    def on_assets_change(self):
        self.refresh(1)

    def on_subset_change(self):
        self.refresh(2)

    def on_repre_change(self):
        self.refresh(3)

    def refresh(self, refresh_type=0):
        """Build the need comboboxes with content"""
        if refresh_type < 1:
            assets = sorted(self._get_assets())
            self._assets_box.populate(assets)

        if refresh_type < 2:
            last_subset = self._subsets_box.currentText()

            subsets = sorted(self._get_subsets())
            self._subsets_box.populate(subsets)

            if (last_subset != "" and last_subset in list(subsets)):
                index = None
                for i in range(self._subsets_box.count()):
                    if last_subset == str(self._subsets_box.itemText(i)):
                        index = i
                        break
                if index is not None:
                    self._subsets_box.setCurrentIndex(index)

        if refresh_type < 3:
            last_repre = self._representations_box.currentText()

            representations = sorted(self._get_representations())
            self._representations_box.populate(representations)

            if (last_repre != "" and last_repre in list(representations)):
                index = None
                for i in range(self._representations_box.count()):
                    if last_repre == self._representations_box.itemText(i):
                        index = i
                        break
                if index is not None:
                    self._representations_box.setCurrentIndex(index)

        self.set_labels()
        self.validate()

    def set_labels(self):
        default = "*No changes"
        asset_label = default
        subset_label = default
        repre_label = default

        if self._assets_box.currentText() != '':
            asset_label = self._assets_box.currentText()
        if self._subsets_box.currentText() != '':
            subset_label = self._subsets_box.currentText()
        if self._representations_box.currentText() != '':
            repre_label = self._representations_box.currentText()

        self._asset_label.setText(asset_label)
        self._subset_label.setText(subset_label)
        self._repre_label.setText(repre_label)

    def validate(self):
        asset_name = self._assets_box.get_valid_value() or None
        subset_name = self._subsets_box.get_valid_value() or None
        repre_name = self._representations_box.get_valid_value() or None

        asset_ok = True
        subset_ok = True
        repre_ok = True
        for item in self._items:
            if any(not x for x in [asset_name, subset_name, repre_name]):
                _id = io.ObjectId(item["representation"])
                representation = io.find_one({
                    "type": "representation",
                    "_id": _id
                })
                version, subset, asset, project = io.parenthood(representation)

                if asset_name is None:
                    asset_name = asset["name"]

                if subset_name is None:
                    subset_name = subset["name"]

                if repre_name is None:
                    repre_name = representation["name"]

            asset = io.find_one({"name": asset_name, "type": "asset"})
            if asset is None:
                asset_ok = False
                continue
            subset = io.find_one({
                "name": subset_name,
                "type": "subset",
                "parent": asset["_id"]
            })
            if subset is None:
                subset_ok = False
                continue
            version = io.find_one(
                {
                    "type": "version",
                    "parent": subset["_id"]
                },
                sort=[('name', -1)]
            )
            if version is None:
                repre_ok = False
                continue

            repre = io.find_one({
                "name": repre_name,
                "type": "representation",
                "parent": version["_id"]
            })
            if repre is None:
                repre_ok = False

        asset_sheet = ''
        subset_sheet = ''
        repre_sheet = ''
        accept_sheet = ''
        error_msg = '*Please select'
        if asset_ok is False:
            asset_sheet = 'border: 1px solid red;'
            self._asset_label.setText(error_msg)
        if subset_ok is False:
            subset_sheet = 'border: 1px solid red;'
            self._subset_label.setText(error_msg)
        if repre_ok is False:
            repre_sheet = 'border: 1px solid red;'
            self._repre_label.setText(error_msg)
        if asset_ok and subset_ok and repre_ok:
            accept_sheet = 'border: 1px solid green;'

        self._assets_box.setStyleSheet(asset_sheet)
        self._subsets_box.setStyleSheet(subset_sheet)
        self._representations_box.setStyleSheet(repre_sheet)

        self._accept_btn.setEnabled(asset_ok and subset_ok and repre_ok)
        self._accept_btn.setStyleSheet(accept_sheet)

    def _get_assets(self):
        filtered_assets = []
        for asset in io.find({'type': 'asset'}):
            subsets = io.find({
                'type': 'subset',
                'parent': asset['_id']
            })
            for subs in subsets:
                filtered_assets.append(asset['name'])
                break

        return filtered_assets

    def _get_subsets(self):
        # Filter subsets by asset in dropdown
        if self._assets_box.currentText() != "":
            parents = []
            parents.append(io.find_one({
                'type': 'asset',
                'name': self._assets_box.currentText()
            }))

            return self._get_document_names("subset", parents)
        # If any asset in dropdown is selected
        # - filter subsets by selected assets in scene inventory
        assets = []
        for item in self._items:
            _id = io.ObjectId(item["representation"])
            representation = io.find_one(
                {"type": "representation", "_id": _id}
            )
            version, subset, asset, project = io.parenthood(representation)
            assets.append(asset)

        possible_subsets = None
        for asset in assets:
            subsets = io.find({
                'type': 'subset',
                'parent': asset['_id']
            })
            asset_subsets = set()
            for subset in subsets:
                asset_subsets.add(subset['name'])

            if possible_subsets is None:
                possible_subsets = asset_subsets
            else:
                possible_subsets = (possible_subsets & asset_subsets)

        return list(possible_subsets)

    def _get_representations(self):
        if self._subsets_box.currentText() != "":
            subsets = []
            parents = []
            subsets.append(self._subsets_box.currentText())

            for subset in subsets:
                entity = io.find_one({
                    'type': 'subset',
                    'name': subset
                })

                entity = io.find_one(
                    {
                        'type': 'version',
                        'parent': entity['_id']
                    },
                    sort=[('name', -1)]
                )
                if entity not in parents:
                    parents.append(entity)

            return self._get_document_names("representation", parents)

        versions = []
        for item in self._items:
            _id = io.ObjectId(item["representation"])
            representation = io.find_one(
                {"type": "representation", "_id": _id}
            )
            version, subset, asset, project = io.parenthood(representation)
            versions.append(version)

        possible_repres = None
        for version in versions:
            representations = io.find({
                'type': 'representation',
                'parent': version['_id']
            })
            repres = set()
            for repre in representations:
                repres.add(repre['name'])

            if possible_repres is None:
                possible_repres = repres
            else:
                possible_repres = (possible_repres & repres)

        return list(possible_repres)

    def _get_document_names(self, document_type, parents=[]):

        query = {"type": document_type}

        if len(parents) == 1:
            query["parent"] = parents[0]["_id"]
        elif len(parents) > 1:
            or_exprs = []
            for parent in parents:
                expr = {"parent": parent["_id"]}
                or_exprs.append(expr)

            query["$or"] = or_exprs

        return io.find(query).distinct("name")

    def _on_accept(self):

        # Use None when not a valid value or when placeholder value
        asset = self._assets_box.get_valid_value() or None
        subset = self._subsets_box.get_valid_value() or None
        representation = self._representations_box.get_valid_value() or None

        if not any([asset, subset, representation]):
            self.log.error("Nothing selected")
            return

        for item in self._items:
            try:
                switch_item(item,
                            asset_name=asset,
                            subset_name=subset,
                            representation_name=representation)
            except Exception as e:
                self.log.warning(e)

        self.switched.emit()

        self.close()


def switch_item(container,
                asset_name=None,
                subset_name=None,
                representation_name=None):
    """Switch container asset, subset or representation of a container by name.

    It'll always switch to the latest version - of course a different
    approach could be implemented.

    Args:
        container (dict): data of the item to switch with
        asset_name (str): name of the asset
        subset_name (str): name of the subset
        representation_name (str): name of the representation

    Returns:
        dict

    """

    if all(not x for x in [asset_name, subset_name, representation_name]):
        raise ValueError(
            "Must have at least one change provided to switch.")

    # Collect any of current asset, subset and representation if not provided
    # so we can use the original name from those.
    if any(not x for x in [asset_name, subset_name, representation_name]):
        _id = io.ObjectId(container["representation"])
        representation = io.find_one({"type": "representation", "_id": _id})
        version, subset, asset, project = io.parenthood(representation)

        if asset_name is None:
            asset_name = asset["name"]

        if subset_name is None:
            subset_name = subset["name"]

        if representation_name is None:
            representation_name = representation["name"]

    # Find the new one
    asset = io.find_one({"name": asset_name, "type": "asset"})
    assert asset, ("Could not find asset in the database with the name "
                   "'%s'" % asset_name)

    subset = io.find_one({"name": subset_name,
                          "type": "subset",
                          "parent": asset["_id"]})
    assert subset, ("Could not find subset in the database with the name "
                    "'%s'" % subset_name)

    version = io.find_one({"type": "version",
                           "parent": subset["_id"]},
                          sort=[('name', -1)])

    assert version, "Could not find a version for {}.{}".format(
        asset_name, subset_name
    )

    representation = io.find_one({"name": representation_name,
                                  "type": "representation",
                                  "parent": version["_id"]})

    assert representation, (
        "Could not find representation in the database with"
        " the name '%s'" % representation_name)

    avalon.switch(container, representation)

    return representation
