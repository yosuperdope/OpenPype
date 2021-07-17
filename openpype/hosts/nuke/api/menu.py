import os
import nuke
from avalon.api import Session

from .lib import WorkfileSettings
from openpype.api import Logger, BuildWorkfile, get_current_project_settings

from openpype.tools import workfiles

log = Logger().get_logger(__name__)

menu_label = os.environ["AVALON_LABEL"]


def install():
    menubar = nuke.menu("Nuke")
    menu = menubar.findItem(menu_label)

    # replace reset resolution from avalon core to pype's
    name = "Work Files..."
    rm_item = [
        (i, item) for i, item in enumerate(menu.items()) if name in item.name()
    ][0]

    log.debug("Changing Item: {}".format(rm_item))

    menu.removeItem(rm_item[1].name())
    menu.addCommand(
        name,
        workfiles.show,
        index=2
    )
    menu.addSeparator(index=3)
    # replace reset resolution from avalon core to pype's
    name = "Reset Resolution"
    new_name = "Set Resolution"
    rm_item = [
        (i, item) for i, item in enumerate(menu.items()) if name in item.name()
    ][0]

    log.debug("Changing Item: {}".format(rm_item))
    # rm_item[1].setEnabled(False)
    menu.removeItem(rm_item[1].name())
    menu.addCommand(
        new_name,
        lambda: WorkfileSettings().reset_resolution(),
        index=(rm_item[0])
    )

    # replace reset frame range from avalon core to pype's
    name = "Reset Frame Range"
    new_name = "Set Frame Range"
    rm_item = [
        (i, item) for i, item in enumerate(menu.items()) if name in item.name()
    ][0]
    log.debug("Changing Item: {}".format(rm_item))
    # rm_item[1].setEnabled(False)
    menu.removeItem(rm_item[1].name())
    menu.addCommand(
        new_name,
        lambda: WorkfileSettings().reset_frame_range_handles(),
        index=(rm_item[0])
    )

    # add colorspace menu item
    name = "Set Colorspace"
    menu.addCommand(
        name, lambda: WorkfileSettings().set_colorspace()
    )
    log.debug("Adding menu item: {}".format(name))

    # add item that applies all setting above
    name = "Apply All Settings"
    menu.addCommand(
        name,
        lambda: WorkfileSettings().set_context_settings()
    )
    log.debug("Adding menu item: {}".format(name))

    menu.addSeparator()

    # add workfile builder menu item
    name = "Build Workfile"
    menu.addCommand(
        name, lambda: BuildWorkfile().process()
    )
    log.debug("Adding menu item: {}".format(name))

    # adding shortcuts
    add_shortcuts_from_presets()

    # add studio menu
    install_studio_menu()


def uninstall():

    menubar = nuke.menu("Nuke")
    menu = menubar.findItem(menu_label)

    for item in menu.items():
        log.info("Removing menu item: {}".format(item.name()))
        menu.removeItem(item.name())


def install_studio_menu():
    try:
        import scriptsmenu.launchfornuke as launchfornuke
        import scriptsmenu.scriptsmenu as scriptsmenu
    except ImportError:
        log.warning(
            "Skipping studio.menu install, because "
            "'scriptsmenu' module seems unavailable."
        )
        return

    # load configuration of custom menu
    settings = get_current_project_settings()
    config = settings['nuke'].get('menu', {}).get('menu_items', [])

    # process title
    title = settings['nuke'].get('menu', {}).get('menu_title')
    # expand env vars
    if '$' in title:
        title = os.environ.get(title.replace('$', ''))
    # default to menu name
    if not title:
        title = menu_label.title()

    # run the launcher for Nuke menu
    studio_menu = launchfornuke.main(title=title)

    # apply configuration
    studio_menu.build_from_configuration(studio_menu, config)
    add_gizmo_menu(studio_menu)


def add_gizmo_menu(menu, search_dir='gizmos', title="Gizmos"):
    """ adds all gizmos in a directory to a menu
    """
    sub_menu = menu.add_menu(parent=menu,
                             title=title)
    # search all NUKE_PATHs
    for paths in os.getenv('NUKE_PATH').split(';'):
        # if the dir name matches the search dir, continue
        if os.path.basename(paths) == search_dir:
            for file in os.listdir(paths):
                # add every file in the dir that's a gizmo
                if file.endswith('.gizmo'):
                    gizmo = file.replace('.gizmo', '')
                    menu.add_script(parent=sub_menu,
                                    title=gizmo,
                                    command='nuke.tcl("{}")'.format(gizmo),
                                    sourcetype='python',
                                    tags=["gizmo"])


def add_shortcuts_from_presets():
    menubar = nuke.menu("Nuke")
    nuke_presets = get_current_project_settings()["nuke"]["general"]

    if nuke_presets.get("menu"):
        menu_label_mapping = {
            "manage": "Manage...",
            "create": "Create...",
            "load": "Load...",
            "build_workfile": "Build Workfile",
            "publish": "Publish..."
        }

        for command_name, shortcut_str in nuke_presets.get("menu").items():
            log.info("menu_name `{}` | menu_label `{}`".format(
                command_name, menu_label
            ))
            log.info("Adding Shortcut `{}` to `{}`".format(
                shortcut_str, command_name
            ))
            try:
                menu = menubar.findItem(menu_label)
                item_label = menu_label_mapping[command_name]
                menuitem = menu.findItem(item_label)
                menuitem.setShortcut(shortcut_str)
            except AttributeError as e:
                log.error(e)
