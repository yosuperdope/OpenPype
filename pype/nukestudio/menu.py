import os
import sys
import hiero.core
from pypeapp import Logger
from avalon.api import Session
from hiero.ui import findMenuAction

# this way we secure compatibility between nuke 10 and 11
try:
    from PySide.QtGui import *
except Exception:
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *

from .tags import add_tags_from_presets

from .lib import (
    reload_config,
    set_workfiles
)

log = Logger().get_logger(__name__, "nukestudio")

self = sys.modules[__name__]
self._change_context_menu = None


def _update_menu_task_label(*args):
    """Update the task label in Avalon menu to current session"""

    object_name = self._change_context_menu
    found_menu = findMenuAction(object_name)

    if not found_menu:
        log.warning("Can't find menuItem: {}".format(object_name))
        return

    label = "{}, {}".format(Session["AVALON_ASSET"],
                            Session["AVALON_TASK"])

    menu = found_menu.menu()
    self._change_context_menu = label
    menu.setTitle(label)


class Pype_QAction(QAction):
    def __init__(self, name, parent=None):
        QAction.__init__(self, name, parent)

    def eventHandler(self, event):
        # Add the Menu to the right-click menu
        event.menu.addAction(self)


def install():
    """
    Installing menu into Nukestudio

    """

    # here is the best place to add menu
    from avalon.tools import (
        creator,
        publish,
        cbloader,
        cbsceneinventory,
        contextmanager,
        libraryloader
    )

    menu_name = os.environ['AVALON_LABEL']

    context_label = "{0}, {1}".format(
        Session["AVALON_ASSET"], Session["AVALON_TASK"]
    )

    self._change_context_menu = context_label

    # Grab Hiero's MenuBar
    M = hiero.ui.menuBar()

    try:
        check_made_menu = findMenuAction(menu_name)
        menu = check_made_menu.menu()
    except Exception:
        menu = M.addMenu(menu_name)

    context_label_menu = menu.addMenu(context_label)

    actions = [
        {
            'parent': context_label_menu,
            'action': Pype_QAction('Set Context', None),
            'function': contextmanager.show,
        },
        "separator",
        {
            'action': Pype_QAction("Work Files...", None),
            'function': set_workfiles,
        },
        {
            'action': Pype_QAction('Create Default Tags..', None),
            'function': add_tags_from_presets,
        },
        "separator",
        {
            'interests': ["kShowContextMenu/kTimeline",
                           "kShowContextMenu/kSpreadsheet",
                           "pype_menu"],
            'action': Pype_QAction('Publish...', None),
            'function': publish.show,
            'shortcut': "Ctrl+Alt+P"
        },
        {
            'action': Pype_QAction('Library...', None),
            'function': libraryloader.show,
        },
        "separator",
        {
            'action': Pype_QAction('Reload pipeline...', None),
            'function': reload_config,
        }]

    # Create menu items
    for a in actions:
        add_to_menu = menu
        if isinstance(a, dict):
            action = a["action"]
            action.triggered.connect(a["function"])

            # parent it into submenu if any
            if 'parent' in a.keys():
                add_to_menu = a["parent"]

            # add shortcut if any
            if 'shortcut' in a.keys():
                action.setShortcut(a["shortcut"])

            # add the action to correct interests
            if 'interests' in a.keys():
                for interest in a["interests"]:
                    if "pype_menu" in interest:
                        # add action to menu
                        add_to_menu.addAction(action)
                        hiero.ui.registerAction(action)
                    else:
                        hiero.core.events.registerInterest(
                            interest, action.eventHandler)
            else:
                # add action to menu
                add_to_menu.addAction(action)
                hiero.ui.registerAction(action)

        if isinstance(a, str):
            add_to_menu.addSeparator()
