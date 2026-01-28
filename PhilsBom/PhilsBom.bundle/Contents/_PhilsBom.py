import adsk.core
import adsk.fusion
import traceback
import ast
import os
import re
import zipfile
import datetime
import webbrowser
import sys
import string
import csv
import json
import plistlib
import itertools
import copy
from urllib.request import urlopen
from datetime import datetime as dt

APP = adsk.core.Application.get()
UI = APP.userInterface if APP else None

APP_VERSION = 1.01
# Legacy App Store update checks are intentionally disabled for PhilsBom.
APP_UPDATE_CHECK_DURATION = 0
APP_URL = ""
APP_MAC_DOWNLOAD_URL = ""
APP_WINDOWS_DOWNLOAD_URL = ""

# Renamed add-in identity.
COMMAND_ID = "PhilsBom"
COMMAND_NAME = "Phils Bom"

RESOURCES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Resources", "")
COMMAND_LOGO = os.path.join(RESOURCES_FOLDER, "PhilsBomLogo.png")
COMMAND_ICON = os.path.join(RESOURCES_FOLDER, "Icon")
COMMAND_ICON_SETTINGS = os.path.join(RESOURCES_FOLDER, "Settings")
COMMAND_ICON_TABLE_MOVE_UP = os.path.join(RESOURCES_FOLDER, "MoveUp")
COMMAND_ICON_TABLE_MOVE_DOWN = os.path.join(RESOURCES_FOLDER, "MoveDown")
COMMAND_ICON_TABLE_ADD = os.path.join(RESOURCES_FOLDER, "Add")
COMMAND_ICON_SETTINGS_RESET = os.path.join(RESOURCES_FOLDER, "Reset")

STRING_CREATE_BOM = "Create BOM"
STRING_SETTINGS = COMMAND_NAME + " Settings"
STRING_APP_SAVE_FOLDER = "Documents"
STRING_SETTINGS_EXTENSION = "-Settings.plist"
STRING_LAST_UPDATE_CHECK_EXTENSION = "-LastUpdateCheck.plist"
STRING_APP_UPDATE_TITLE = COMMAND_NAME + " Update Available"
STRING_APP_UPDATE_MESSAGE = "Do you want to download the new version now?"
STRING_CUSTOM_ITEM_NUMBER_ALPHA = "/@n/"
STRING_CUSTOM_ITEM_NUMBER_NUMERIC = "/#n/"

TITLE_BOM_CREATION_METHOD = "BOM Creation Method"
TITLE_BOM_DELIMITER_TYPE = "BOM CSV File Delimiter"
TITLE_BOM_EXPORT_FILE_TYPE = "BOM Export Filetype"
TITLE_BOM_EXPORT_FILENAME = "BOM Export Filename"
TITLE_INCLUDE_HIDDEN_ITEMS = "Include Hidden Items"
TITLE_INCLUDE_PARENT_COMPONENTS = "Include Parent Components"
TITLE_INCLUDE_LINKED_COMPONENTS = "Include Linked Components"
TITLE_COLUMN_GROUP = "BOM Column Options"
TITLE_COLUMN_TABLE = "Table"
TITLE_TABLE_BUTTON_MOVE_UP = "Move Up"
TITLE_TABLE_BUTTON_MOVE_DOWN = "Move Down"
TITLE_TABLE_BUTTON_ADD = "Add Column"
TITLE_EXPORT_GROUP = "BOM Export Options"
TITLE_FILENAME_GROUP = "BOM Filename Options"
TITLE_BUTTON_SETTINGS_RESET = "Reset All Settings"
TITLE_SETTINGS_DICTIONARY_TEXT = "*** SETTINGS DATA ***"
TITLE_COMMAND_OK_BUTTON = "Save All Settings"
TITLE_FILENAME_PREVIEW = "BOM Filename Preview"
TITLE_USE_CUSTOM_ITEM_NUMBER = "Use Custom Item No."
TITLE_CUSTOM_ITEM_NUMBER = "Template"
TITLE_CUSTOM_ITEM_NUMBER_PREVIEW = "Preview"
TITLE_UNITS_GROUP = "Units"
TITLE_LENGTH_UNIT = "Length units"
TITLE_AREA_UNIT = "Area units"
TITLE_VOLUME_UNIT = "Volume units"
TITLE_MASS_UNIT = "Mass units"
TITLE_COM_UNIT = "Center of Mass units"

TOOLTIP_BOM_TYPE = "Preferred method for BOM creation"
TOOLTIP_BOM_DELIMITER_TYPE = "The CSV file delimiter used between the data columns"
TOOLTIP_INCLUDE_HIDDEN_ITEMS = "Include or exclude hidden items in the BOM"
TOOLTIP_INCLUDE_PARENT_COMPONENTS = "Include components that have no bodies but contain child components"
TOOLTIP_INCLUDE_LINKED_COMPONENTS = "Include components that are linked/referenced from other designs"
TOOLTIP_BOM_EXPORT_FILE_TYPE = "The filetype (format) of the exported BOM"
TOOLTIP_BOM_EXPORT_FILENAME = "The document property used in the filename of the exported BOM"
TOOLTIP_TABLE_BUTTON_MOVE_UP = "Change the order of the columns (left)"
TOOLTIP_TABLE_BUTTON_MOVE_DOWN = "Change the order of the columns (right)"
TOOLTIP_TABLE_BUTTON_ADD = "Add an \"empty\" column"
TOOLTIP_BUTTON_SETTINGS_RESET = "Reset all settings to default values"
TOOLTIP_FILENAME_PREVIEW = "Preview of the filename of the exported BOM"
TOOLTIP_USE_CUSTOM_ITEM_NUMBER = "Keep the standard Item No. or use custom"
TOOLTIP_CUSTOM_ITEM_NUMBER = (
    "Enter template text here to generate the Custom Item No.\n"
    "Use "
    + STRING_CUSTOM_ITEM_NUMBER_ALPHA
    + " to assign A-Z letters, where n denotes the number of letters used\n"
    "Use "
    + STRING_CUSTOM_ITEM_NUMBER_NUMERIC
    + " to assign 1-9 numbers, where n denotes the number of numbers used\n"
    "For example: Part /@2/ - /#3/ \n"
    "Result: Part AA - 001"
)
TOOLTIP_CUSTOM_ITEM_NUMBER_PREVIEW = "Preview of the Custom Item No. sequence"
TOOLTIP_UNITS_GROUP = "Units used for BOM values and headers"
TOOLTIP_LENGTH_UNIT = "Units for length, width, and height columns"
TOOLTIP_AREA_UNIT = "Units for the area column"
TOOLTIP_VOLUME_UNIT = "Units for the volume column"
TOOLTIP_MASS_UNIT = "Units for the mass column"
TOOLTIP_COM_UNIT = "Units for the center of mass column"

LIST_BOM_DELIMITER_TYPES = [
    "Comma (,)",
    "Semicolon (;)",
    "Colon (:)",
    "Equals (=)",
    "Tab (\"\t\")",
    "Space (\" \")",
]
LIST_BOM_CREATION_METHODS = [
    "Grouped By Component",
    "Grouped By Part Name",
    "Grouped By Bodies",
    "Indented",
]
LIST_BOM_EXPORT_FILE_TYPES = [
    "XLSX (.xlsx)",
    "CSV (.csv)",
    "XML (.xml)",
    "JSON (.json)",
]
LIST_BOM_EXPORT_FILENAME_OPTIONS = [
    "Document Name and Suffix",
    "Document Name only",
    "Part Number and Suffix",
    "Part Number only",
]
LIST_LENGTH_UNITS = ["mm", "cm", "m", "in", "ft"]
LIST_AREA_UNITS = ["mm^2", "cm^2", "m^2", "in^2", "ft^2"]
LIST_VOLUME_UNITS = ["mm^3", "cm^3", "m^3", "in^3", "ft^3"]
LIST_MASS_UNITS = ["kg", "g", "lbmass", "ouncemass"]

LIST_SETTINGS_DEFAULT_DICTIONARY_KEYS = [
    "_BOMCreationMethod",
    "_BOMDelimiterType",
    "_includeHiddenItems",
    "_initialDirectory",
    "_BOMExportFilenameOption",
]

LIST_SETTINGS_GROUPED_BY_COMPONENT = [
    {"_partName": {"_title": "Part Name", "_visible": True, "_position": 0}},
    {"_browserPath": {"_title": "Browser Path", "_visible": True, "_position": 1}},
    {"_parentFolder": {"_title": "Parent Folder", "_visible": True, "_position": 2}},
    {"_partNumber": {"_title": "Part Number", "_visible": True, "_position": 3}},
    {"_quantity": {"_title": "Quantity", "_visible": True, "_position": 4}},
    {"_description": {"_title": "Description", "_visible": True, "_position": 5}},
    {"_volume": {"_title": "Volume", "_visible": True, "_position": 6}},
    {"_area": {"_title": "Area", "_visible": True, "_position": 7}},
    {"_mass": {"_title": "Mass", "_visible": True, "_position": 8}},
    {"_material": {"_title": "Material", "_visible": True, "_position": 9}},
    {"_length": {"_title": "Length", "_visible": True, "_position": 10}},
    {"_width": {"_title": "Width", "_visible": True, "_position": 11}},
    {"_height": {"_title": "Height", "_visible": True, "_position": 12}},
    {"_centerOfMass": {"_title": "Center of Mass", "_visible": True, "_position": 13}},
]

LIST_SETTINGS_GROUPED_BY_PART_NAME = [
    {"_partName": {"_title": "Part Name", "_visible": True, "_position": 0}},
    {"_browserPath": {"_title": "Browser Path", "_visible": True, "_position": 1}},
    {"_parentFolder": {"_title": "Parent Folder", "_visible": True, "_position": 2}},
    {"_partNumber": {"_title": "Part Number", "_visible": True, "_position": 3}},
    {"_quantity": {"_title": "Quantity", "_visible": True, "_position": 4}},
    {"_description": {"_title": "Description", "_visible": True, "_position": 5}},
    {"_volume": {"_title": "Volume", "_visible": True, "_position": 6}},
    {"_area": {"_title": "Area", "_visible": True, "_position": 7}},
    {"_mass": {"_title": "Mass", "_visible": True, "_position": 8}},
    {"_material": {"_title": "Material", "_visible": True, "_position": 9}},
    {"_length": {"_title": "Length", "_visible": True, "_position": 10}},
    {"_width": {"_title": "Width", "_visible": True, "_position": 11}},
    {"_height": {"_title": "Height", "_visible": True, "_position": 12}},
    {"_centerOfMass": {"_title": "Center of Mass", "_visible": True, "_position": 13}},
]

LIST_SETTINGS_GROUPED_BY_BODIES = [
    {"_bodyName": {"_title": "Body Name", "_visible": True, "_position": 0}},
    {"_parentComponent": {"_title": "Parent Component", "_visible": True, "_position": 1}},
    {"_parentFolder": {"_title": "Parent Folder", "_visible": True, "_position": 2}},
    {"_quantity": {"_title": "Quantity", "_visible": True, "_position": 3}},
    {"_volume": {"_title": "Volume", "_visible": True, "_position": 4}},
    {"_area": {"_title": "Area", "_visible": True, "_position": 5}},
    {"_mass": {"_title": "Mass", "_visible": True, "_position": 6}},
    {"_material": {"_title": "Material", "_visible": True, "_position": 7}},
    {"_length": {"_title": "Length", "_visible": True, "_position": 8}},
    {"_width": {"_title": "Width", "_visible": True, "_position": 9}},
    {"_height": {"_title": "Height", "_visible": True, "_position": 10}},
    {"_centerOfMass": {"_title": "Center of Mass", "_visible": True, "_position": 11}},
]

LIST_SETTINGS_INDENTED = [
    {"_itemNumber": {"_title": "Item No.", "_visible": True, "_position": 0}},
    {"_itemName": {"_title": "Item Name", "_visible": True, "_position": 1}},
    {"_parentFolder": {"_title": "Parent Folder", "_visible": True, "_position": 2}},
    {"_quantity": {"_title": "Quantity", "_visible": True, "_position": 3}},
    {"_description": {"_title": "Description", "_visible": True, "_position": 4}},
    {"_volume": {"_title": "Volume", "_visible": True, "_position": 5}},
    {"_area": {"_title": "Area", "_visible": True, "_position": 6}},
    {"_mass": {"_title": "Mass", "_visible": True, "_position": 7}},
    {"_material": {"_title": "Material", "_visible": True, "_position": 8}},
    {"_length": {"_title": "Length", "_visible": True, "_position": 9}},
    {"_width": {"_title": "Width", "_visible": True, "_position": 10}},
    {"_height": {"_title": "Height", "_visible": True, "_position": 11}},
]

# Global handler stores to prevent GC in Fusion.
HANDLERS = []
CUSTOM_COMMAND_DEFINITIONS = []

DEBUG_BOM = True


def _log_path():
    try:
        base = os.path.dirname(GetAppSaveFilename(""))
        return os.path.join(base, f"{COMMAND_ID}.log")
    except Exception:
        return None


def _log(message):
    if not DEBUG_BOM:
        return
    try:
        path = _log_path()
        if not path:
            return
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.datetime.now().isoformat()} {COMMAND_ID}: {message}\n")
    except Exception:
        pass


def MessageBox(message, icon=0):
    if UI:
        UI.messageBox(str(message), COMMAND_NAME, 0, icon)


def MessageBoxDebug(titleString, variable):
    MessageBox(f"{titleString}:\n {variable}", 0)


def CleanFusionCompNameInserts(name):
    return re.sub(r"\([0-9]+\)", "", str(name)).strip()


def CleanDescription(description):
    return str(description).replace("\r", "").replace("\n", "").replace("\t", "")


def CleanFilename(filename):
    filename = str(filename)
    if sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
        return re.sub(r"[\\/*?:\"<>|]", "", filename)
    return filename


def ConvertQuotes(stringValue):
    return str(stringValue).replace("\"", "'") if stringValue is not None else ""


def GetEscapeXML(text):
    text = "" if text is None else str(text)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&apos;")
    )


NUMERIC_COLUMNS = {"Quantity", "Volume", "Area", "Mass", "Length", "Width", "Height"}
NUMERIC_HEADER_BASES = {c.lower() for c in NUMERIC_COLUMNS}


def _csv_escape(value, delimiter):
    text = "" if value is None else str(value)
    needs_quote = delimiter in text or "\"" in text or "\n" in text or "\r" in text
    if "\"" in text:
        text = text.replace("\"", "\"\"")
        needs_quote = True
    return f"\"{text}\"" if needs_quote else text


def _csv_cell(value, delimiter, numeric=False):
    text = "" if value is None else str(value).strip()
    # Keep numeric fields unquoted when safe so Excel treats them as numbers.
    if numeric and delimiter not in text and "\"" not in text and "\n" not in text and "\r" not in text:
        return text
    return _csv_escape(text, delimiter)


def _header_base(header_value):
    header = "" if header_value is None else str(header_value)
    base = header.split("(", 1)[0].strip().lower()
    return base


def _excel_number_string(value):
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    # Reject ambiguous formats like 1,234.56 or 1.234,56.
    if "," in text and "." in text:
        return None
    normalized = text.replace(",", ".")
    try:
        num = float(normalized)
    except Exception:
        return None
    # Excel expects dot-decimal in the XML numeric value.
    return str(num)

def ConvertDictionaryToString(dataDictionary):
    try:
        return str(dataDictionary).replace(",", "\n")
    except Exception:
        return "{}"


def ConvertStringToDictionary(dataString):
    if isinstance(dataString, dict):
        return dataString
    text = "" if dataString is None else str(dataString).strip()
    if not text:
        return {}
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", ",")
    try:
        return ast.literal_eval(normalized)
    except Exception:
        try:
            return ast.literal_eval(text)
        except Exception:
            try:
                return json.loads(text)
            except Exception:
                return {}


def _deepcopy_settings_list(data_list):
    return [copy.deepcopy(entry) for entry in data_list]


def _method_default_list(method_name):
    if method_name == "Grouped By Component":
        return _deepcopy_settings_list(LIST_SETTINGS_GROUPED_BY_COMPONENT)
    if method_name == "Grouped By Part Name":
        return _deepcopy_settings_list(LIST_SETTINGS_GROUPED_BY_PART_NAME)
    if method_name == "Grouped By Bodies":
        return _deepcopy_settings_list(LIST_SETTINGS_GROUPED_BY_BODIES)
    if method_name == "Indented":
        return _deepcopy_settings_list(LIST_SETTINGS_INDENTED)
    return []


def _ensure_aliases(data_list):
    for entry in data_list:
        for _, data in entry.items():
            if data.get("_alias") in (None, ""):
                data["_alias"] = data.get("_title", "")
    return data_list


def _units_manager():
    design = adsk.fusion.Design.cast(APP.activeProduct)
    return design.unitsManager if design else None


def _design_default_length_unit():
    unitsMgr = _units_manager()
    unitType = unitsMgr.defaultLengthUnits if unitsMgr else "cm"
    return unitType if unitType in LIST_LENGTH_UNITS else "cm"


def _default_area_unit():
    # Default to square meters for readability across metric designs.
    return "m^2"


def _default_volume_unit():
    # Volume must be cubic units; use cubic meters by default.
    return "m^3"


def _valid_option(value, options, default_value):
    return value if value in options else default_value


def _normalize_settings(appSettingsDictionary):
    settings = dict(appSettingsDictionary) if isinstance(appSettingsDictionary, dict) else {}

    # Seed missing top-level keys with defaults.
    for key in LIST_SETTINGS_DEFAULT_DICTIONARY_KEYS:
        if key not in settings or settings.get(key) in (None, ""):
            settings[key] = SettingsDefaultForKey(key)

    for extra_key in (
        "_BOMExportFileType",
        "_settingsDictionaryText",
        "_useCustomItemNumber",
        "_textCustomItemNumber",
        "_columnGroup",
        "_exportGroup",
        "_filenameGroup",
        "_includeParentComponents",
        "_includeLinkedComponents",
        "_unitsGroup",
        "_lengthUnit",
        "_areaUnit",
        "_volumeUnit",
        "_massUnit",
        "_comUnit",
    ):
        if extra_key not in settings or settings.get(extra_key) is None:
            settings[extra_key] = SettingsDefaultForKey(extra_key)

    # Validate unit selections against supported options.
    settings["_lengthUnit"] = _valid_option(
        settings.get("_lengthUnit"), LIST_LENGTH_UNITS, SettingsDefaultForKey("_lengthUnit")
    )
    settings["_areaUnit"] = _valid_option(
        settings.get("_areaUnit"), LIST_AREA_UNITS, SettingsDefaultForKey("_areaUnit")
    )
    settings["_volumeUnit"] = _valid_option(
        settings.get("_volumeUnit"), LIST_VOLUME_UNITS, SettingsDefaultForKey("_volumeUnit")
    )
    settings["_massUnit"] = _valid_option(
        settings.get("_massUnit"), LIST_MASS_UNITS, SettingsDefaultForKey("_massUnit")
    )
    settings["_comUnit"] = _valid_option(
        settings.get("_comUnit"), LIST_LENGTH_UNITS, settings["_lengthUnit"]
    )

    raw_dict = settings.get("_settingsDictionaryText")
    settings_dict = raw_dict if isinstance(raw_dict, dict) else ConvertStringToDictionary(raw_dict)
    if not isinstance(settings_dict, dict) or not settings_dict:
        settings_dict = SettingsNewDictionary()

    # Ensure each creation method has a complete, alias-populated list.
    for method_name in LIST_BOM_CREATION_METHODS:
        default_list = _method_default_list(method_name)
        current_list = settings_dict.get(method_name)
        if not isinstance(current_list, list) or not current_list:
            settings_dict[method_name] = _ensure_aliases(default_list)
            continue

        current_map = {}
        for entry in current_list:
            for key, data in entry.items():
                current_map[key] = data

        merged_list = []
        for entry in default_list:
            for key, default_data in entry.items():
                data = current_map.get(key, copy.deepcopy(default_data))
                if data.get("_title") in (None, ""):
                    data["_title"] = default_data.get("_title", "")
                if data.get("_position") is None:
                    data["_position"] = default_data.get("_position", 0)
                if data.get("_visible") is None:
                    data["_visible"] = default_data.get("_visible", True)
                if data.get("_alias") in (None, ""):
                    data["_alias"] = data.get("_title", "")
                merged_list.append({key: data})

        # Preserve any custom columns that are not part of the defaults.
        default_keys = {list(entry.keys())[0] for entry in default_list}
        for entry in current_list:
            for key, data in entry.items():
                if key not in default_keys:
                    if data.get("_alias") in (None, ""):
                        data["_alias"] = data.get("_title", "")
                    merged_list.append({key: data})

        settings_dict[method_name] = merged_list

    settings["_settingsDictionaryText"] = settings_dict

    if settings.get("_BOMCreationMethod") not in LIST_BOM_CREATION_METHODS:
        settings["_BOMCreationMethod"] = LIST_BOM_CREATION_METHODS[0]

    return settings


def SettingsDefaultForKey(dictionaryKey):
    if dictionaryKey == "_BOMCreationMethod":
        return LIST_BOM_CREATION_METHODS[0]
    if dictionaryKey == "_BOMExportFileType":
        return LIST_BOM_EXPORT_FILE_TYPES[0]
    if dictionaryKey == "_BOMExportFilenameOption":
        return LIST_BOM_EXPORT_FILENAME_OPTIONS[0]
    if dictionaryKey == "_BOMDelimiterType":
        return GetDelimiterDefault()
    if dictionaryKey == "_includeHiddenItems":
        return False
    if dictionaryKey == "_includeParentComponents":
        return False
    if dictionaryKey == "_includeLinkedComponents":
        return True
    if dictionaryKey == "_initialDirectory":
        return ""
    if dictionaryKey == "_settingsDictionaryText":
        return SettingsNewDictionary()
    if dictionaryKey == "_useCustomItemNumber":
        return False
    if dictionaryKey == "_textCustomItemNumber":
        return "Part /@2/ - /#3/"
    if dictionaryKey == "_columnGroup":
        return True
    if dictionaryKey == "_exportGroup":
        return True
    if dictionaryKey == "_filenameGroup":
        return True
    if dictionaryKey == "_unitsGroup":
        return True
    if dictionaryKey == "_lengthUnit":
        return _design_default_length_unit()
    if dictionaryKey == "_areaUnit":
        return _default_area_unit()
    if dictionaryKey == "_volumeUnit":
        return _default_volume_unit()
    if dictionaryKey == "_massUnit":
        return "kg"
    if dictionaryKey == "_comUnit":
        return _design_default_length_unit()
    return ""


def SettingsDefaults():
    defaults = {}
    for key in LIST_SETTINGS_DEFAULT_DICTIONARY_KEYS:
        defaults[key] = SettingsDefaultForKey(key)
    # Include the additional keys we rely on but that are not in the legacy list.
    for key in (
        "_BOMExportFileType",
        "_settingsDictionaryText",
        "_useCustomItemNumber",
        "_textCustomItemNumber",
        "_columnGroup",
        "_exportGroup",
        "_filenameGroup",
        "_includeParentComponents",
        "_includeLinkedComponents",
        "_unitsGroup",
        "_lengthUnit",
        "_areaUnit",
        "_volumeUnit",
        "_massUnit",
        "_comUnit",
    ):
        defaults[key] = SettingsDefaultForKey(key)
    return defaults


def SettingsNewDictionary():
    settingsDictionaryData = {}
    for keyBOMCreationMethod in LIST_BOM_CREATION_METHODS:
        if keyBOMCreationMethod == "Grouped By Component":
            settingsDictionaryData[keyBOMCreationMethod] = _ensure_aliases(
                _method_default_list(keyBOMCreationMethod)
            )
        elif keyBOMCreationMethod == "Grouped By Part Name":
            settingsDictionaryData[keyBOMCreationMethod] = _ensure_aliases(
                _method_default_list(keyBOMCreationMethod)
            )
        elif keyBOMCreationMethod == "Grouped By Bodies":
            settingsDictionaryData[keyBOMCreationMethod] = _ensure_aliases(
                _method_default_list(keyBOMCreationMethod)
            )
        elif keyBOMCreationMethod == "Indented":
            settingsDictionaryData[keyBOMCreationMethod] = _ensure_aliases(
                _method_default_list(keyBOMCreationMethod)
            )
    return settingsDictionaryData


def SettingsGetValueForKey(appSettingsDictionary, dictionaryKey):
    if not isinstance(appSettingsDictionary, dict):
        return SettingsDefaultForKey(dictionaryKey)
    setting = appSettingsDictionary.get(dictionaryKey)
    if setting in (None, ""):
        return SettingsDefaultForKey(dictionaryKey)
    return setting


def SettingsSetValueForKey(appSettingsDictionary, dictionaryKey, settingValue):
    if isinstance(appSettingsDictionary, dict):
        appSettingsDictionary[dictionaryKey] = settingValue


def SettingsLoad():
    appSettingsFilename = GetAppSaveFilename(STRING_SETTINGS_EXTENSION)
    appSettingsDictionary = None

    try:
        with open(appSettingsFilename, "r", encoding="utf-8") as data:
            appSettingsDictionary = ast.literal_eval(data.read())
    except (IOError, SyntaxError, ValueError):
        try:
            with open(appSettingsFilename, "rb") as data:
                appSettingsDictionary = plistlib.load(data)
        except (IOError, SyntaxError, plistlib.InvalidFileException, ValueError):
            appSettingsDictionary = SettingsDefaults()
    except Exception:
        appSettingsDictionary = SettingsDefaults()

    normalized = _normalize_settings(appSettingsDictionary)
    _log(
        "SettingsLoad: method={} exportType={} units={}/{}/{}/{}/{}".format(
            normalized.get("_BOMCreationMethod"),
            normalized.get("_BOMExportFileType"),
            normalized.get("_lengthUnit"),
            normalized.get("_areaUnit"),
            normalized.get("_volumeUnit"),
            normalized.get("_massUnit"),
            normalized.get("_comUnit"),
        )
    )
    return normalized


def SettingsSave(appSettingsDictionary):
    settings = _normalize_settings(appSettingsDictionary)
    appSettingsFilename = GetAppSaveFilename(STRING_SETTINGS_EXTENSION)
    settings["_appSettingsFilename"] = appSettingsFilename
    with open(appSettingsFilename, "wb") as data:
        plistlib.dump(settings, data)
    _log("SettingsSave: wrote {}".format(appSettingsFilename))


def _select_dropdown_item(dropdown, desired_name):
    if not dropdown:
        return
    try:
        items = dropdown.listItems
        for i in range(items.count):
            item = items.item(i)
            item.isSelected = item.name == desired_name
    except Exception:
        pass


def _add_dropdown(inputs, key, title, options, selected, tooltip=""):
    dropdown = inputs.addDropDownCommandInput(
        COMMAND_ID + key, title, adsk.core.DropDownStyles.TextListDropDownStyle
    )
    items = dropdown.listItems
    for option in options:
        items.add(option, option == selected, "")
    if tooltip:
        dropdown.tooltip = tooltip
    return dropdown


def SettingsReset(
    inputColumnTable,
    inputBOMCreationMethod,
    inputIncludeHiddenItems,
    inputIncludeParentComponents,
    inputIncludeLinkedComponents,
    inputBOMExportFileType,
    inputBOMDelimiterType,
    inputSettingsDictionaryText,
    inputUnitsGroup,
    inputLengthUnit,
    inputAreaUnit,
    inputVolumeUnit,
    inputMassUnit,
    inputComUnit,
):
    try:
        inputSettingsDictionaryText.text = ConvertDictionaryToString(SettingsNewDictionary())
        dataDictionary = ConvertStringToDictionary(inputSettingsDictionaryText.text)

        inputBOMCreationMethod.listItems[0].isSelected = True
        inputIncludeHiddenItems.value = SettingsDefaultForKey("_includeHiddenItems")
        if inputIncludeParentComponents:
            inputIncludeParentComponents.value = SettingsDefaultForKey("_includeParentComponents")
        if inputIncludeLinkedComponents:
            inputIncludeLinkedComponents.value = SettingsDefaultForKey("_includeLinkedComponents")

        settingBOMDelimiterType = GetDelimiterDefault()
        for i in range(len(LIST_BOM_DELIMITER_TYPES)):
            inputBOMDelimiterType.listItems[i].isSelected = (
                settingBOMDelimiterType == LIST_BOM_DELIMITER_TYPES[i]
            )

        inputBOMExportFileType.listItems[0].isSelected = True
        settingBOMExportFileType = inputBOMExportFileType.selectedItem.name
        inputBOMDelimiterType.isVisible = settingBOMExportFileType == "CSV (.csv)"

        # Reset units to defaults and keep COM aligned to the length default.
        default_length = SettingsDefaultForKey("_lengthUnit")
        _select_dropdown_item(inputLengthUnit, default_length)
        _select_dropdown_item(inputAreaUnit, SettingsDefaultForKey("_areaUnit"))
        _select_dropdown_item(inputVolumeUnit, SettingsDefaultForKey("_volumeUnit"))
        _select_dropdown_item(inputMassUnit, SettingsDefaultForKey("_massUnit"))
        _select_dropdown_item(inputComUnit, default_length)
        if inputUnitsGroup:
            inputUnitsGroup.isExpanded = SettingsDefaultForKey("_unitsGroup")

        dataList = dataDictionary[inputBOMCreationMethod.selectedItem.name]
        TableCreateRows(inputColumnTable, dataList)

        MessageBox("Settings have been reset.", 4)
        _log("SettingsReset")
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))


def GetCommandForUniqueID(uniqueID, command):
    try:
        return command.commandInputs.itemById(COMMAND_ID + uniqueID)
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))
        return None


def GetAppSaveFilename(filenameExtension):
    try:
        if sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
            documentsLocation = os.path.join(os.environ["USERPROFILE"], STRING_APP_SAVE_FOLDER)
        else:
            documentsLocation = os.path.join(os.environ["HOME"], STRING_APP_SAVE_FOLDER)

        appSaveLocation = os.path.join(documentsLocation, COMMAND_ID)

        if not os.path.exists(documentsLocation):
            os.mkdir(documentsLocation)
        if not os.path.exists(appSaveLocation):
            os.mkdir(appSaveLocation)

        return os.path.join(appSaveLocation, COMMAND_ID + filenameExtension)
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))
        return ""


def GetParentPath(occPath):
    splits = str(occPath).split("+")
    if splits:
        partPath = splits[-1]
        return str(occPath).replace(partPath, "")
    return ""


def GetDelimiterCharacter(delimiterString):
    if delimiterString == "Comma (,)":
        return ","
    if delimiterString == "Semicolon (;)":
        return ";"
    if delimiterString == "Colon (:)":
        return ":"
    if delimiterString == "Equals (=)":
        return "="
    if delimiterString == "Tab (\"\t\")":
        return "\t"
    if delimiterString == "Space (\" \")":
        return " "
    return ","


def GetDefaultUnitsType():
    unitsMgr = _units_manager()
    unitType = unitsMgr.defaultLengthUnits if unitsMgr else "cm"
    if unitType not in LIST_LENGTH_UNITS:
        unitType = "cm"

    # Mass defaults to kg regardless of the document length unit.
    massType = "kg"

    unitPrefs = APP.preferences.unitAndValuePreferences if APP else None
    unitPrecision = unitPrefs.generalPrecision if unitPrefs else 3
    unitDecimalPoint = unitPrefs.isPeriodDecimalPoint if unitPrefs else True
    unitFootInchDisplayFormat = unitPrefs.footAndInchDisplayFormat if unitPrefs else 0

    return (unitType, massType, unitPrecision, unitDecimalPoint, unitFootInchDisplayFormat)


def GetDelimiterDefault():
    _, _, _, unitDecimalPoint, _ = GetDefaultUnitsType()
    return LIST_BOM_DELIMITER_TYPES[1] if unitDecimalPoint is False else LIST_BOM_DELIMITER_TYPES[0]


def GetSortedDimensions(length, width, height):
    dimensions = [length, width, height]
    newlength = max(dimensions)
    dimensions.remove(newlength)
    newHeight = min(dimensions)
    dimensions.remove(newHeight)
    newWidth = dimensions[0]
    return (newlength, newWidth, newHeight)


def _internal_length_unit(unitsMgr):
    return unitsMgr.internalUnits if unitsMgr else "cm"


def _internal_area_unit(unitsMgr):
    return f"{_internal_length_unit(unitsMgr)}^2"


def _internal_volume_unit(unitsMgr):
    return f"{_internal_length_unit(unitsMgr)}^3"


def GetUnitSettings(appSettingsDictionary):
    settings = _normalize_settings(appSettingsDictionary)
    length_unit = settings.get("_lengthUnit", SettingsDefaultForKey("_lengthUnit"))
    area_unit = settings.get("_areaUnit", SettingsDefaultForKey("_areaUnit"))
    volume_unit = settings.get("_volumeUnit", SettingsDefaultForKey("_volumeUnit"))
    mass_unit = settings.get("_massUnit", SettingsDefaultForKey("_massUnit"))
    com_unit = settings.get("_comUnit", length_unit) or length_unit
    return length_unit, area_unit, volume_unit, mass_unit, com_unit


def _convert_units(value, from_unit, to_unit):
    unitsMgr = _units_manager()
    value = 0.0 if value is None else float(value)
    if not unitsMgr:
        return value
    try:
        return unitsMgr.convert(value, from_unit, to_unit)
    except Exception:
        return value


def ConvertVolume(value, volumeUnit, decimalPlaces):
    unitsMgr = _units_manager()
    if not unitsMgr:
        return round(0.0 if value is None else float(value), decimalPlaces)
    internal_unit = _internal_volume_unit(unitsMgr)
    convertedValue = _convert_units(value, internal_unit, volumeUnit)
    return round(convertedValue, decimalPlaces)


def ConvertArea(value, areaUnit, decimalPlaces):
    unitsMgr = _units_manager()
    if not unitsMgr:
        return round(0.0 if value is None else float(value), decimalPlaces)
    internal_unit = _internal_area_unit(unitsMgr)
    convertedValue = _convert_units(value, internal_unit, areaUnit)
    return round(convertedValue, decimalPlaces)


def ConvertMass(value, massUnit, decimalPlaces):
    convertedValue = _convert_units(value, "kg", massUnit)
    return round(convertedValue, decimalPlaces)


def ConvertDimension(value, lengthUnit, decimalPlaces, unitDecimalPoint):
    unitsMgr = _units_manager()
    if not unitsMgr:
        return round(0.0 if value is None else float(value), decimalPlaces)
    internal_unit = _internal_length_unit(unitsMgr)
    convertedValue = _convert_units(value, internal_unit, lengthUnit)
    return round(convertedValue, decimalPlaces)


def ConvertDimensionFractional(value, lengthUnit):
    unitsMgr = _units_manager()
    if not unitsMgr:
        return "0"
    try:
        return unitsMgr.formatInternalValue(float(value), lengthUnit, False)
    except Exception:
        internal_unit = _internal_length_unit(unitsMgr)
        convertedValue = _convert_units(value, internal_unit, lengthUnit)
        return str(round(convertedValue, 4))


def ConvertCenterOfMass(value, comUnit, decimalPlaces, unitDecimalPoint):
    unitsMgr = _units_manager()
    if not unitsMgr or value is None:
        return ""

    internal_unit = _internal_length_unit(unitsMgr)
    convertedValueX = _convert_units(value.x, internal_unit, comUnit)
    convertedValueY = _convert_units(value.y, internal_unit, comUnit)
    convertedValueZ = _convert_units(value.z, internal_unit, comUnit)

    convertedValueX = round(float(convertedValueX), decimalPlaces)
    convertedValueY = round(float(convertedValueY), decimalPlaces)
    convertedValueZ = round(float(convertedValueZ), decimalPlaces)

    return "{}, {}, {}".format(convertedValueX, convertedValueY, convertedValueZ)


def ConvertCenterOfMassFractional(value, comUnit):
    unitsMgr = _units_manager()
    if not unitsMgr or value is None:
        return ""
    try:
        convertedValueX = unitsMgr.formatInternalValue(value.x, comUnit, False)
        convertedValueY = unitsMgr.formatInternalValue(value.y, comUnit, False)
        convertedValueZ = unitsMgr.formatInternalValue(value.z, comUnit, False)
        return "{}, {}, {}".format(convertedValueX, convertedValueY, convertedValueZ)
    except Exception:
        _, _, unitPrecision, unitDecimalPoint, _ = GetDefaultUnitsType()
        return ConvertCenterOfMass(value, comUnit, unitPrecision, unitDecimalPoint)

def _iter_bodies(bodies):
    if bodies is None:
        return []
    if isinstance(bodies, adsk.fusion.BRepBody):
        return [bodies]
    try:
        return list(bodies)
    except Exception:
        return []


def _occurrence_has_bodies(occ):
    try:
        if occ and occ.bRepBodies and occ.bRepBodies.count > 0:
            return True
    except Exception:
        pass
    try:
        comp = occ.component if occ else None
        return bool(comp and comp.bRepBodies and comp.bRepBodies.count > 0)
    except Exception:
        return False


def _is_linked_occurrence(occ):
    try:
        if hasattr(occ, "isReferencedComponent"):
            return bool(occ.isReferencedComponent)
    except Exception:
        pass
    try:
        comp = occ.component if occ else None
        if comp and hasattr(comp, "isReferencedComponent"):
            return bool(comp.isReferencedComponent)
        if comp and hasattr(comp, "isReferenced"):
            return bool(comp.isReferenced)
    except Exception:
        pass
    return False


def _occurrence_allowed(occ, includeHiddenItems, includeParentComponents, includeLinkedComponents):
    if occ is None:
        return False
    if occ.isVisible is False and includeHiddenItems is False:
        return False
    if includeLinkedComponents is False and _is_linked_occurrence(occ):
        return False
    if includeParentComponents is False and not _occurrence_has_bodies(occ):
        return False
    return True


def GetBodiesVolume(bodies, BOMCreationMethod):
    volume = 0.0
    if BOMCreationMethod == "Grouped By Bodies":
        body = bodies if isinstance(bodies, adsk.fusion.BRepBody) else None
        if body and body.isSolid:
            try:
                volume += body.volume
            except Exception:
                volume += 0.0
        return volume

    for bodyK in _iter_bodies(bodies):
        if getattr(bodyK, "isSolid", False):
            try:
                volume += bodyK.volume
            except Exception:
                volume += 0.0
    return volume


def GetPhysicsArea(bodies, BOMCreationMethod):
    area = 0.0
    if BOMCreationMethod == "Grouped By Bodies":
        body = bodies if isinstance(bodies, adsk.fusion.BRepBody) else None
        if body and body.isSolid and body.physicalProperties:
            area += body.physicalProperties.area
        return area

    for body in _iter_bodies(bodies):
        if body.isSolid and body.physicalProperties:
            area += body.physicalProperties.area
    return area


def GetPhysicalMass(bodies, BOMCreationMethod):
    mass = 0.0
    if BOMCreationMethod == "Grouped By Bodies":
        body = bodies if isinstance(bodies, adsk.fusion.BRepBody) else None
        if body and body.isSolid and body.physicalProperties:
            mass += body.physicalProperties.mass
        return mass

    for body in _iter_bodies(bodies):
        if body.isSolid and body.physicalProperties:
            mass += body.physicalProperties.mass
    return mass


def GetPhysicalMaterial(bodies, BOMCreationMethod):
    if BOMCreationMethod == "Grouped By Bodies":
        body = bodies if isinstance(bodies, adsk.fusion.BRepBody) else None
        if body and body.isSolid and body.material:
            try:
                return body.material.name
            except Exception:
                return ""
        return ""

    matList = []
    for body in _iter_bodies(bodies):
        if body.isSolid and body.material:
            try:
                mat = body.material.name
            except Exception:
                mat = ""
            if mat and mat not in matList:
                matList.append(mat)
    return ", ".join(matList)


def GetOrientedBoundingBox(BOMCreationMethod, comp):
    try:
        orientedBoundingBoxes = []

        if BOMCreationMethod != "Grouped By Bodies" and hasattr(comp, "bRepBodies"):
            for body in comp.bRepBodies:
                try:
                    orientedBoundingBoxes.append(body.orientedMinimumBoundingBox)
                except Exception:
                    pass
            if not orientedBoundingBoxes and hasattr(comp, "orientedMinimumBoundingBox"):
                orientedBoundingBoxes.append(comp.orientedMinimumBoundingBox)
        else:
            if hasattr(comp, "orientedMinimumBoundingBox"):
                orientedBoundingBoxes.append(comp.orientedMinimumBoundingBox)

        if not orientedBoundingBoxes:
            return (0.0, 0.0, 0.0)

        tempBrepMgr = adsk.fusion.TemporaryBRepManager.get()
        tmpBodies = []
        for boundingBox in orientedBoundingBoxes:
            if boundingBox:
                try:
                    tmpBodies.append(tempBrepMgr.createBox(boundingBox))
                except Exception:
                    pass

        if not tmpBodies:
            return (0.0, 0.0, 0.0)

        unionBody = tmpBodies[0]
        for body in tmpBodies[1:]:
            tempBrepMgr.booleanOperation(
                unionBody, body, adsk.fusion.BooleanTypes.UnionBooleanType
            )

        boundingBox = unionBody.orientedMinimumBoundingBox
        length = boundingBox.length
        width = boundingBox.width
        height = boundingBox.height
        return GetSortedDimensions(length, width, height)
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))
        _log("GetOrientedBoundingBox failed")
        return (0.0, 0.0, 0.0)


def GetRequiredColumnData(dataDictionary, BOMCreationMethod):
    dataList = dataDictionary.get(BOMCreationMethod, []) if isinstance(dataDictionary, dict) else []
    temporaryDictionary = {}

    for keyData in dataList:
        for key, data in keyData.items():
            if data.get("_visible") is not True:
                continue

            title = data.get("_title", "")
            alias = data.get("_alias", "")
            position = data.get("_position", 0)

            if title == "":
                if alias == "":
                    continue
                temporaryDictionary[key] = position
            else:
                temporaryDictionary[title] = position

    temporaryDictionarySorted = dict(sorted(temporaryDictionary.items(), key=lambda item: item[1]))
    required = list(temporaryDictionarySorted.keys())
    _log("Required columns ({}): {}".format(BOMCreationMethod, required))
    return required


def GetColumnAliasForKey(dataList, dataKey):
    for keyData in dataList:
        for key, data in keyData.items():
            if key == dataKey or data.get("_title") == dataKey:
                aliasString = data.get("_alias")
                if aliasString is None or aliasString == "":
                    aliasString = data.get("_title")
                return aliasString if aliasString else str(dataKey)
    return str(dataKey)


def GetCustomItemNumberSequence(template):
    letters_set = string.ascii_uppercase
    wrap_around = True
    pattern = re.compile(r"/([@#])(\\d+)/")

    elements = []
    placeholders = []
    pos = 0
    for m in pattern.finditer(template):
        if m.start() > pos:
            elements.append(template[pos : m.start()])
        kind = m.group(1)
        length = int(m.group(2))
        elements.append((kind, length))
        placeholders.append((kind, length))
        pos = m.end()

    if pos < len(template):
        elements.append(template[pos:])

    counters = []
    for kind, length in placeholders:
        if kind == "@":
            counters.append({"type": "letters", "charset": letters_set, "len": length, "pos": [0] * length})
        elif kind == "#":
            counters.append({"type": "numbers", "len": length, "pos": 1})

    def get_value(counter):
        if counter["type"] == "letters":
            return "".join(counter["charset"][i] for i in counter["pos"])
        if counter["type"] == "numbers":
            return str(counter["pos"]).zfill(counter["len"])
        return ""

    def increment_counters():
        for idx in reversed(range(len(counters))):
            counter = counters[idx]
            if counter["type"] == "letters":
                for p in reversed(range(counter["len"])):
                    counter["pos"][p] += 1
                    if counter["pos"][p] < len(counter["charset"]):
                        return True
                    counter["pos"][p] = 0
            elif counter["type"] == "numbers":
                counter["pos"] += 1
                if counter["pos"] <= 10 ** counter["len"] - 1:
                    return True
                counter["pos"] = 1
        return False

    def reset_all():
        for counter in counters:
            if counter["type"] == "letters":
                counter["pos"] = [0] * counter["len"]
            elif counter["type"] == "numbers":
                counter["pos"] = 1

    first = True
    while True:
        if not first:
            if not increment_counters():
                if wrap_around:
                    reset_all()
                else:
                    return
        first = False

        out_str = ""
        ph_i = 0
        for element in elements:
            if isinstance(element, tuple):
                out_str += get_value(counters[ph_i]) if counters else ""
                ph_i += 1
            else:
                out_str += element
        yield out_str


def GetCustomItemNumberVisibility(settingBOMCreationMethod, command):
    inputUseCustomItemNumber = GetCommandForUniqueID("_useCustomItemNumber", command)
    inputCustomItemNumber = GetCommandForUniqueID("_textCustomItemNumber", command)
    inputCustomItemNumberPreview = GetCommandForUniqueID("_textCustomItemNumberPreview", command)

    if not inputUseCustomItemNumber or not inputCustomItemNumber or not inputCustomItemNumberPreview:
        return

    if settingBOMCreationMethod == "Indented":
        inputUseCustomItemNumber.isVisible = True
        inputCustomItemNumber.isVisible = inputUseCustomItemNumber.value
        inputCustomItemNumberPreview.isVisible = inputUseCustomItemNumber.value

        if inputUseCustomItemNumber.value:
            template = inputCustomItemNumber.text
            preview_items = []
            for index in range(3):
                preview_items.append(
                    next(itertools.islice(GetCustomItemNumberSequence(template), index, index + 1))
                )
            inputCustomItemNumberPreview.text = ", ".join(preview_items) + ", ..."
        return

    inputUseCustomItemNumber.isVisible = False
    inputCustomItemNumber.isVisible = False
    inputCustomItemNumberPreview.isVisible = False


def TableMoveRow(direction, inputColumnTable, selectedRow, inputSettingsDictionaryText, settingBOMCreationMethod):
    try:
        if selectedRow == -1:
            MessageBox("Select one row to move.", 0)
            return

        if direction == "Up":
            targetRow = selectedRow - 1
            if targetRow < 0:
                return
        else:
            targetRow = selectedRow + 1
            if targetRow > inputColumnTable.rowCount - 1:
                return

        dataDictionary = ConvertStringToDictionary(inputSettingsDictionaryText.text)
        dataList = dataDictionary[settingBOMCreationMethod]

        foundKey = None
        for keyData in dataList:
            for key, data in keyData.items():
                if data.get("_position") == selectedRow:
                    data["_position"] = targetRow
                    foundKey = key

        adjacentItemNumber = targetRow + 1 if direction == "Up" else targetRow - 1

        for keyData in dataList:
            for key, data in keyData.items():
                if data.get("_position") == targetRow and key != foundKey:
                    data["_position"] = adjacentItemNumber

        inputSettingsDictionaryText.text = ConvertDictionaryToString(dataDictionary)
        TableCreateRows(inputColumnTable, dataList)
        inputColumnTable.selectedRow = targetRow
        _log("TableMoveRow {}: {} -> {}".format(direction, selectedRow, targetRow))
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))


def TableAddRow(inputColumnTable, inputSettingsDictionaryText, settingBOMCreationMethod):
    try:
        uniqueID = str(dt.now()).replace(" ", "_").replace(":", "-").replace(".", "-")

        dataDictionary = ConvertStringToDictionary(inputSettingsDictionaryText.text)
        dataList = dataDictionary[settingBOMCreationMethod]

        newColumnPosition = 0
        for keyData in dataList:
            for _, data in keyData.items():
                if data.get("_position", 0) >= newColumnPosition:
                    newColumnPosition = data.get("_position", 0) + 1

        newColumnDict = {"_title": "", "_visible": True, "_position": newColumnPosition, "_alias": "Empty"}
        dataList.append({uniqueID: newColumnDict})

        inputSettingsDictionaryText.text = ConvertDictionaryToString(dataDictionary)
        TableCreateRows(inputColumnTable, dataList)
        inputColumnTable.selectedRow = newColumnPosition
        _log("TableAddRow: {}".format(uniqueID))
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))


def TableCreateRows(inputColumnTable, dataList):
    try:
        positionDictionary = {}
        dataDictionary = {}

        inputColumnTable.clear()
        for keyData in dataList:
            for key, data in keyData.items():
                positionDictionary[key] = data.get("_position", 0)
                dataDictionary[key] = data

        positionDictionarySorted = dict(sorted(positionDictionary.items(), key=lambda item: item[1]))
        tableInputs = inputColumnTable.commandInputs

        for key in positionDictionarySorted.keys():
            inputCheckbox = tableInputs.addBoolValueInput(
                COMMAND_ID + key, "", True, "", dataDictionary[key].get("_visible", True)
            )
            inputCheckboxString = tableInputs.addStringValueInput(
                COMMAND_ID + key + "_title", "", dataDictionary[key].get("_title", "")
            )
            inputCheckboxString.isReadOnly = True

            aliasString = dataDictionary[key].get("_alias")
            if aliasString is None:
                aliasString = dataDictionary[key].get("_title", "")

            inputAliasString = tableInputs.addStringValueInput(
                COMMAND_ID + key + "_alias", "", aliasString
            )
            inputAliasString.isReadOnly = False

            row = inputColumnTable.rowCount
            inputColumnTable.addCommandInput(inputCheckbox, row, 0)
            inputColumnTable.addCommandInput(inputCheckboxString, row, 1)
            inputColumnTable.addCommandInput(inputAliasString, row, 2)

        inputColumnTable.selectedRow = 0
        inputColumnTable.minimumVisibleRows = 1
        inputColumnTable.maximumVisibleRows = inputColumnTable.rowCount
        inputColumnTable.hasGrid = False
        inputColumnTable.rowSpacing = 1
        inputColumnTable.columnSpacing = 1
        inputColumnTable.columnRatio = "1:2:2"
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))


def UpdateCheck():
    _log("UpdateCheck: disabled")
    return None


def UpdateCheckGetLast():
    try:
        appLastUpdateCheckFilename = GetAppSaveFilename(STRING_LAST_UPDATE_CHECK_EXTENSION)
        with open(appLastUpdateCheckFilename, "rb") as data:
            lastUpdateCheckDictionary = plistlib.load(data)
            last_date = lastUpdateCheckDictionary.get("_lastUpdateCheckDate")
            if last_date:
                return last_date
    except Exception:
        pass

    UpdateCheckSetLast()
    return str(datetime.date.today())


def UpdateCheckSetLast():
    try:
        lastUpdateCheckDictionary = {"_lastUpdateCheckDate": str(datetime.date.today())}
        appLastUpdateCheckFilename = GetAppSaveFilename(STRING_LAST_UPDATE_CHECK_EXTENSION)
        with open(appLastUpdateCheckFilename, "wb") as data:
            plistlib.dump(lastUpdateCheckDictionary, data)
        _log("UpdateCheckSetLast: {}".format(lastUpdateCheckDictionary["_lastUpdateCheckDate"]))
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))


def UpdateCheckAppStoreVersion():
    try:
        page = urlopen(APP_URL)
        html = page.read().decode("utf-8")
        result = re.findall(r"version-title.*$", html, re.MULTILINE)
        if not result:
            return None
        data = result[0]
        version = re.findall(r"Version(.*?),", data)
        if not version:
            return None
        versionNumber = str(version[0])
        split = versionNumber.split(".", 2)
        parts = [split[0], split[1]] if len(split) >= 2 else split
        versionNumber = float(".".join(parts))
        return versionNumber
    except Exception:
        return None

def GetFilenameBOMPrompt(initialFilename):
    try:
        result = UI.inputBox("Filename: ", "Save As", initialFilename)
        inputString, isCancelled = result
        if inputString == "":
            inputString = initialFilename
        return (inputString, isCancelled)
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))
        return (initialFilename, True)


def GetFilenameBOM(BOMExportFilename, BOMCreationMethod, BOMExportFileType, preview):
    try:
        design = adsk.fusion.Design.cast(APP.activeProduct)
        root = design.rootComponent if design else None
        root_name = root.name if root else COMMAND_NAME
        root_part = root.partNumber if root and root.partNumber else root_name

        if BOMExportFilename == "Document Name and Suffix":
            filenamePreviewText = root_name + "-BOM" + " (" + BOMCreationMethod + ")"
        elif BOMExportFilename == "Document Name only":
            filenamePreviewText = root_name
        elif BOMExportFilename == "Part Number and Suffix":
            filenamePreviewText = root_part + "-BOM" + " (" + BOMCreationMethod + ")"
        else:
            filenamePreviewText = root_part

        if preview:
            if BOMExportFileType == "CSV (.csv)":
                return filenamePreviewText + ".csv"
            if BOMExportFileType == "XLSX (.xlsx)":
                return filenamePreviewText + ".xlsx"
            if BOMExportFileType == "XML (.xml)":
                return filenamePreviewText + ".xml"
            if BOMExportFileType == "JSON (.json)":
                return filenamePreviewText + ".json"
        return filenamePreviewText
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))
        return COMMAND_NAME + "-BOM"


def ConvertCSVtoXML(csvHeaders, csvRow):
    s = "\t<row>\n"
    for header, item in zip(csvHeaders, csvRow):
        s += "\t\t<{}>{}</{}>\n".format(header, item, header)
    return s + "\t</row>"


def ExportXLSX(csvFilePath):
    try:
        with open(csvFilePath, newline="", encoding="utf-8") as csvfile:
            reader = list(csv.reader(csvfile))
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))
        return

    numeric_indices = set()
    if reader:
        headers = reader[0]
        for idx, header in enumerate(headers):
            if _header_base(header) in NUMERIC_HEADER_BASES:
                numeric_indices.add(idx)

    rows_xml = []
    for row_idx, row in enumerate(reader, 1):
        cells_xml = []
        for col_idx, cell_value in enumerate(row, 1):
            cell_ref = "{}{}".format(chr(64 + col_idx), row_idx)
            is_header = row_idx == 1
            is_numeric_col = (col_idx - 1) in numeric_indices
            if (not is_header) and is_numeric_col:
                num_text = _excel_number_string(cell_value)
                if num_text is not None:
                    cell_xml = '<c r="{}"><v>{}</v></c>'.format(cell_ref, num_text)
                else:
                    cell_xml = '<c r="{}" t="inlineStr"><is><t>{}</t></is></c>'.format(
                        cell_ref, GetEscapeXML(cell_value)
                    )
            else:
                cell_xml = '<c r="{}" t="inlineStr"><is><t>{}</t></is></c>'.format(
                    cell_ref, GetEscapeXML(cell_value)
                )
            cells_xml.append(cell_xml)
        row_xml = "<row r=\"{}\">{}</row>".format(row_idx, "".join(cells_xml))
        rows_xml.append(row_xml)

    worksheet_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
        "<sheetData>{}</sheetData></worksheet>".format("".join(rows_xml))
    )

    content_types = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
    <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
    <Default Extension=\"xml\" ContentType=\"application/xml\"/>
    <Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>
    <Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>
    <Override PartName=\"/docProps/core.xml\" ContentType=\"application/vnd.openxmlformats-package.core-properties+xml\"/>
    <Override PartName=\"/docProps/app.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.extended-properties+xml\"/>
</Types>"""

    rels_rels = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
    <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>
    <Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties\" Target=\"docProps/core.xml\"/>
    <Relationship Id=\"rId3\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties\" Target=\"docProps/app.xml\"/>
</Relationships>"""

    workbook_rels = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
    <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>
</Relationships>"""

    workbook_xml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">
    <sheets>
        <sheet name=\"Sheet1\" sheetId=\"1\" r:id=\"rId1\"/>
    </sheets>
</workbook>"""

    core_xml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<cp:coreProperties xmlns:cp=\"http://schemas.openxmlformats.org/package/2006/metadata/core-properties\" xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:dcterms=\"http://purl.org/dc/terms/\" xmlns:dcmitype=\"http://purl.org/dc/dcmitype/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
    <dc:creator>Python</dc:creator>
    <cp:lastModifiedBy>Python</cp:lastModifiedBy>
    <dcterms:created xsi:type=\"dcterms:W3CDTF\">2026-01-27T00:00:00Z</dcterms:created>
    <dcterms:modified xsi:type=\"dcterms:W3CDTF\">2026-01-27T00:00:00Z</dcterms:modified>
</cp:coreProperties>"""

    app_xml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Properties xmlns=\"http://schemas.openxmlformats.org/officeDocument/2006/extended-properties\" xmlns:vt=\"http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes\">
    <Application>Python XLSX Writer</Application>
</Properties>"""

    xlsxFilePath = csvFilePath.removesuffix(".csv") + ".xlsx"
    with zipfile.ZipFile(xlsxFilePath, "w", zipfile.ZIP_DEFLATED) as xlsx:
        xlsx.writestr("[Content_Types].xml", content_types)
        xlsx.writestr("_rels/.rels", rels_rels)
        xlsx.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        xlsx.writestr("xl/workbook.xml", workbook_xml)
        xlsx.writestr("xl/worksheets/sheet1.xml", worksheet_xml)
        xlsx.writestr("docProps/core.xml", core_xml)
        xlsx.writestr("docProps/app.xml", app_xml)

    if os.path.exists(csvFilePath):
        os.remove(csvFilePath)


def ExportXML(csvFilePath):
    try:
        with open(csvFilePath, "r", encoding="utf-8") as csvFile:
            csvData = csv.reader(csvFile)
            punct = set(string.punctuation)
            csvHeaders = []
            for header in next(csvData):
                header = "".join(ch for ch in header if ch not in punct)
                header = header.strip().lower().replace(" ", "_")
                csvHeaders.append(header)

            xmlData = "<data>\n"
            for csvRow in csvData:
                xmlData += ConvertCSVtoXML(csvHeaders, csvRow) + "\n"
            xmlData += "</data>"
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))
        return

    xmlFilePath = csvFilePath.removesuffix(".csv") + ".xml"
    with open(xmlFilePath, "w", encoding="utf-8") as xmlFile:
        xmlFile.write(xmlData)

    if os.path.exists(csvFilePath):
        os.remove(csvFilePath)


def ExportJSON(csvFilePath):
    try:
        jsonArray = []
        with open(csvFilePath, encoding="utf-8") as csvFile:
            csvReader = csv.DictReader(csvFile)
            for row in csvReader:
                jsonArray.append(row)

        jsonFilePath = csvFilePath.removesuffix(".csv") + ".json"
        with open(jsonFilePath, "w", encoding="utf-8") as jsonFile:
            jsonString = json.dumps(jsonArray, indent=4)
            jsonFile.write(jsonString)

        if os.path.exists(csvFilePath):
            os.remove(csvFilePath)
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))

def _sort_level_key(level_string):
    parts = str(level_string).rstrip(".").split(".")
    key = []
    for part in parts:
        try:
            key.append(int(part))
        except Exception:
            key.append(0)
    return key


def CollectData(bom, requiredColumns, BOMCreationMethod, delimiter):
    try:
        csvStr = ""
        appSettingsDictionary = SettingsLoad()
        lengthUnit, areaUnit, volumeUnit, massUnit, comUnit = GetUnitSettings(appSettingsDictionary)
        _, _, unitPrecision, unitDecimalPoint, unitFootInchDisplayFormat = GetDefaultUnitsType()
        mass_idx = requiredColumns.index("Mass") if "Mass" in requiredColumns else -1
        mass_total = 0.0
        dataDictionary = SettingsGetValueForKey(appSettingsDictionary, "_settingsDictionaryText")
        if not isinstance(dataDictionary, dict):
            dataDictionary = ConvertStringToDictionary(dataDictionary)
        dataList = dataDictionary.get(BOMCreationMethod, [])

        settingUseCustomItemNumber = SettingsGetValueForKey(appSettingsDictionary, "_useCustomItemNumber")
        settingCustomItemNumber = SettingsGetValueForKey(appSettingsDictionary, "_textCustomItemNumber")
        customSeq = GetCustomItemNumberSequence(settingCustomItemNumber) if settingUseCustomItemNumber else None

        headers = []
        for column in requiredColumns:
            header = GetColumnAliasForKey(dataList, column)
            if column == "Volume":
                header = "{} ({})".format(GetColumnAliasForKey(dataList, "_volume"), volumeUnit)
            elif column == "Area":
                header = "{} ({})".format(GetColumnAliasForKey(dataList, "_area"), areaUnit)
            elif column == "Mass":
                header = "{} ({})".format(GetColumnAliasForKey(dataList, "_mass"), massUnit)
            elif column == "Length":
                header = "{} ({})".format(GetColumnAliasForKey(dataList, "_length"), lengthUnit)
            elif column == "Width":
                header = "{} ({})".format(GetColumnAliasForKey(dataList, "_width"), lengthUnit)
            elif column == "Height":
                header = "{} ({})".format(GetColumnAliasForKey(dataList, "_height"), lengthUnit)
            elif column == "Center of Mass":
                header = "{} ({})".format(GetColumnAliasForKey(dataList, "_centerOfMass"), comUnit)
            headers.append(_csv_escape(header, delimiter))
        csvStr += delimiter.join(headers) + "\n"

        for item in bom:
            name = CleanFusionCompNameInserts(item.get("name", ""))
            volume_raw = item.get("volume", 0)
            area_raw = item.get("area", 0)
            mass_raw = item.get("mass", 0)

            volume = ConvertVolume(volume_raw, volumeUnit, unitPrecision)
            area = ConvertArea(area_raw, areaUnit, unitPrecision)
            mass = ConvertMass(mass_raw, massUnit, unitPrecision)

            comp = item.get("component")
            length = item.get("length", 0)
            width = item.get("width", 0)
            height = item.get("height", 0)
            if (length, width, height) == (0, 0, 0) and comp is not None:
                length, width, height = GetOrientedBoundingBox(BOMCreationMethod, comp)

            if lengthUnit in ("in", "ft") and unitFootInchDisplayFormat == 1:
                length = ConvertDimensionFractional(length, lengthUnit)
                width = ConvertDimensionFractional(width, lengthUnit)
                height = ConvertDimensionFractional(height, lengthUnit)
            elif lengthUnit in ("in", "ft") and unitFootInchDisplayFormat == 2:
                length = "Architectural format unsupported"
                width = "Architectural format unsupported"
                height = "Architectural format unsupported"
            else:
                length = ConvertDimension(length, lengthUnit, unitPrecision, unitDecimalPoint)
                width = ConvertDimension(width, lengthUnit, unitPrecision, unitDecimalPoint)
                height = ConvertDimension(height, lengthUnit, unitPrecision, unitDecimalPoint)

            instances = item.get("quantity", item.get("instances", 1))
            if mass_idx != -1:
                try:
                    mass_total += float(mass) * float(instances)
                except Exception:
                    pass
            com_raw = item.get("com", 0)
            if not com_raw or instances > 1:
                com = ""
            else:
                if comUnit in ("in", "ft") and unitFootInchDisplayFormat == 1:
                    com = ConvertCenterOfMassFractional(com_raw, comUnit)
                elif comUnit in ("in", "ft") and unitFootInchDisplayFormat == 2:
                    com = "Architectural format unsupported"
                else:
                    com = ConvertCenterOfMass(com_raw, comUnit, unitPrecision, unitDecimalPoint)

            if unitDecimalPoint is False:
                volume = str(volume).replace(".", ",")
                area = str(area).replace(".", ",")
                mass = str(mass).replace(".", ",")
                length = str(length).replace(".", ",")
                width = str(width).replace(".", ",")
                height = str(height).replace(".", ",")
                com = str(com).replace(".", ",")

            path = item.get("path", "")
            folder = item.get("folder", "")
            partnumber = item.get("partnumber", "")
            desc = item.get("desc", "")
            material = item.get("material", "")
            level = item.get("level", "")

            row_values = []
            for column in requiredColumns:
                if column == "Body Name":
                    value = ConvertQuotes(name)
                elif column == "Part Name":
                    value = ConvertQuotes(name)
                elif column == "Parent Component":
                    value = ConvertQuotes(path)
                elif column == "Browser Path":
                    value = ConvertQuotes(path)
                elif column == "Parent Folder":
                    value = ConvertQuotes(folder)
                elif column == "Part Number":
                    value = ConvertQuotes(partnumber)
                elif column == "Quantity":
                    value = str(instances)
                elif column == "Description":
                    value = ConvertQuotes(desc)
                elif column == "Volume":
                    value = str(volume)
                elif column == "Area":
                    value = str(area)
                elif column == "Mass":
                    value = str(mass)
                elif column == "Material":
                    value = ConvertQuotes(material)
                elif column == "Length":
                    value = str(length)
                elif column == "Width":
                    value = str(width)
                elif column == "Height":
                    value = str(height)
                elif column == "Center of Mass":
                    value = str(com)
                elif column == "Item No.":
                    if customSeq:
                        value = next(customSeq)
                    else:
                        value = str(level)
                elif column == "Item Name":
                    value = ConvertQuotes(name)
                else:
                    value = ""
                row_values.append(_csv_cell(value, delimiter, numeric=column in NUMERIC_COLUMNS))
            csvStr += delimiter.join(row_values) + "\n"

        # Append a mass total row when the Mass column is present.
        if mass_idx != -1:
            total_mass = round(mass_total, unitPrecision)
            total_mass_str = str(total_mass)
            if unitDecimalPoint is False:
                total_mass_str = total_mass_str.replace(".", ",")

            total_row = []
            label_written = False
            for idx, column in enumerate(requiredColumns):
                if idx == mass_idx:
                    value = total_mass_str
                elif (not label_written) and (column not in NUMERIC_COLUMNS):
                    value = "Total mass"
                    label_written = True
                else:
                    value = ""
                total_row.append(_csv_cell(value, delimiter, numeric=column in NUMERIC_COLUMNS))
            csvStr += delimiter.join(total_row) + "\n"

        return csvStr
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))
        return ""


def CreateIndentedBOM(
    occurrences,
    levelString,
    globalBOM,
    BOMCreationMethod,
    includeHiddenItems,
    includeParentComponents,
    includeLinkedComponents,
    multiplier=1,
):
    counter = 0
    itemDict = {}
    localEntries = []

    for i in range(occurrences.count):
        occ = occurrences.item(i)
        if occ.isVisible is False and includeHiddenItems is False:
            continue
        if includeLinkedComponents is False and _is_linked_occurrence(occ):
            continue
        has_bodies = _occurrence_has_bodies(occ)
        if includeParentComponents is False and not has_bodies:
            children = occ.childOccurrences
            if children and children.count > 0:
                CreateIndentedBOM(
                    children,
                    levelString,
                    globalBOM,
                    BOMCreationMethod,
                    includeHiddenItems,
                    includeParentComponents,
                    includeLinkedComponents,
                    multiplier,
                )
            continue
        name = CleanFusionCompNameInserts(occ.component.name)
        if name not in itemDict:
            itemDict[name] = {"occ": occ, "quantity": 1}
            localEntries.append(name)
        else:
            itemDict[name]["quantity"] += 1

    for name in localEntries:
        entry = itemDict[name]
        occ = entry["occ"]
        quantity_here = entry["quantity"] * multiplier

        counter += 1
        level = str(counter) if levelString == "" else levelString + str(counter)
        childLevelString = level + "."

        comp = occ.component
        try:
            folderName = comp.parentDesign.parentDocument.dataFile.parentFolder.name
        except Exception:
            folderName = ""

        volume = GetBodiesVolume(comp.bRepBodies, BOMCreationMethod)
        area = GetPhysicsArea(comp.bRepBodies, BOMCreationMethod)
        mass = GetPhysicalMass(comp.bRepBodies, BOMCreationMethod)
        material = GetPhysicalMaterial(comp.bRepBodies, BOMCreationMethod)

        length = width = height = 0
        if comp.bRepBodies.count > 0:
            length, width, height = GetOrientedBoundingBox(BOMCreationMethod, comp)

        try:
            com = occ.physicalProperties.centerOfMass
        except Exception:
            com = 0

        globalBOM.append(
            {
                "level": str(level),
                "component": comp,
                "path": occ.fullPathName,
                "parentpath": GetParentPath(occ.fullPathName),
                "folder": folderName,
                "partnumber": comp.partNumber,
                "name": name,
                "instances": quantity_here,
                "quantity": quantity_here,
                "volume": volume,
                "area": area,
                "mass": mass,
                "material": material,
                "desc": CleanDescription(comp.description),
                "length": length,
                "width": width,
                "height": height,
                "com": com,
            }
        )

        children = occ.childOccurrences
        if children and children.count > 0:
            CreateIndentedBOM(
                children,
                childLevelString,
                globalBOM,
                BOMCreationMethod,
                includeHiddenItems,
                includeParentComponents,
                includeLinkedComponents,
                quantity_here,
            )


def CreateBOM():
    try:
        currentWorkspace = UI.activeWorkspace
        for workspace in UI.workspaces:
            if workspace.name == "Design":
                workspace.activate()
                break
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))
        return

    design = adsk.fusion.Design.cast(APP.activeProduct)
    if not design:
        MessageBox("No active design.", 3)
        return

    root = design.rootComponent
    occs = root.allOccurrences
    if occs.count == 0:
        MessageBox("Component not found in this design.", 3)
        return

    appSettingsDictionary = SettingsLoad()
    previousSaveDirectory = SettingsGetValueForKey(appSettingsDictionary, "_initialDirectory")

    folderDialog = UI.createFolderDialog()
    folderDialog.title = "Select Save Folder"
    if os.path.exists(previousSaveDirectory):
        folderDialog.initialDirectory = previousSaveDirectory

    try:
        if currentWorkspace:
            currentWorkspace.activate()
        dialogResult = folderDialog.showDialog()
    except TypeError:
        folderDialog.initialDirectory = ""
        dialogResult = folderDialog.showDialog()

    if dialogResult != adsk.core.DialogResults.DialogOK:
        return

    folderPath = folderDialog.folder
    SettingsSetValueForKey(appSettingsDictionary, "_initialDirectory", folderPath)
    SettingsSave(appSettingsDictionary)

    BOMCreationMethod = SettingsGetValueForKey(appSettingsDictionary, "_BOMCreationMethod")
    settingBOMExportFileType = SettingsGetValueForKey(appSettingsDictionary, "_BOMExportFileType")
    initialFilename = GetFilenameBOM(
        SettingsGetValueForKey(appSettingsDictionary, "_BOMExportFilenameOption"),
        BOMCreationMethod,
        settingBOMExportFileType,
        False,
    )

    newFilename, isCancelled = GetFilenameBOMPrompt(CleanFilename(initialFilename))
    if isCancelled:
        return

    filename = newFilename + ".csv"
    filePath = os.path.join(folderPath, CleanFilename(filename))

    dataDictionary = SettingsGetValueForKey(appSettingsDictionary, "_settingsDictionaryText")
    if not isinstance(dataDictionary, dict):
        dataDictionary = ConvertStringToDictionary(dataDictionary)

    requiredColumns = GetRequiredColumnData(dataDictionary, BOMCreationMethod)

    delimiter = GetDelimiterCharacter(SettingsGetValueForKey(appSettingsDictionary, "_BOMDelimiterType"))
    if settingBOMExportFileType in ("XLSX (.xlsx)", "XML (.xml)", "JSON (.json)"):
        delimiter = ","

    includeHiddenItems = SettingsGetValueForKey(appSettingsDictionary, "_includeHiddenItems")
    includeParentComponents = SettingsGetValueForKey(appSettingsDictionary, "_includeParentComponents")
    includeLinkedComponents = SettingsGetValueForKey(appSettingsDictionary, "_includeLinkedComponents")

    _log(
        "CreateBOM: method={} export={} hidden={} parents={} linked={} cols={}".format(
            BOMCreationMethod,
            settingBOMExportFileType,
            includeHiddenItems,
            includeParentComponents,
            includeLinkedComponents,
            requiredColumns,
        )
    )
    _log("CreateBOM: filePath={}".format(filePath))

    bom = []
    globalBOM = []

    if BOMCreationMethod == "Grouped By Bodies":
        allBodies = []
        for i in reversed(range(occs.count)):
            occ = occs.item(i)
            if not _occurrence_allowed(
                occ, includeHiddenItems, includeParentComponents, includeLinkedComponents
            ):
                continue
            for j in reversed(range(occ.bRepBodies.count)):
                allBodies.append(occ.bRepBodies[j])

        for body in reversed(allBodies):
            try:
                folderName = body.parentComponent.parentDesign.parentDocument.dataFile.parentFolder.name
            except Exception:
                folderName = ""

            material = GetPhysicalMaterial(body, BOMCreationMethod)
            name_clean = CleanFusionCompNameInserts(body.name)

            match_index = None
            for idx, bomI in enumerate(bom):
                if bomI["name"] == name_clean and bomI["material"] == material:
                    match_index = idx
                    break

            if match_index is not None:
                bom[match_index]["instances"] += 1
                bom[match_index]["quantity"] = bom[match_index]["instances"]
                continue

            try:
                com = body.physicalProperties.centerOfMass
            except Exception:
                com = 0

            bom.append(
                {
                    "component": body,
                    "path": body.parentComponent.name,
                    "parentpath": "",
                    "folder": folderName,
                    "partnumber": "",
                    "name": name_clean,
                    "instances": 1,
                    "quantity": 1,
                    "volume": GetBodiesVolume(body, BOMCreationMethod),
                    "area": GetPhysicsArea(body, BOMCreationMethod),
                    "mass": GetPhysicalMass(body, BOMCreationMethod),
                    "material": material,
                    "desc": "",
                    "com": com,
                }
            )
    elif BOMCreationMethod == "Indented":
        CreateIndentedBOM(
            root.occurrences,
            "",
            globalBOM,
            BOMCreationMethod,
            includeHiddenItems,
            includeParentComponents,
            includeLinkedComponents,
            1,
        )
        bom = sorted(globalBOM, key=lambda b: _sort_level_key(b.get("level", "")))
    else:
        for i in reversed(range(occs.count)):
            occ = occs.item(i)
            if not _occurrence_allowed(
                occ, includeHiddenItems, includeParentComponents, includeLinkedComponents
            ):
                continue

            comp = occ.component
            occPath = occ.fullPathName

            try:
                folderName = comp.parentDesign.parentDocument.dataFile.parentFolder.name
            except Exception:
                folderName = ""

            found_index = None
            for idx, bomI in enumerate(bom):
                if BOMCreationMethod == "Grouped By Component":
                    if bomI["component"] == comp:
                        parentPathWithoutPartPath = GetParentPath(occPath)
                        if bomI["parentpath"] == parentPathWithoutPartPath:
                            found_index = idx
                            break
                else:
                    if bomI["name"] == comp.name:
                        found_index = idx
                        break

            if found_index is not None:
                bom[found_index]["instances"] += 1
                bom[found_index]["quantity"] = bom[found_index]["instances"]
                continue

            try:
                com = occ.physicalProperties.centerOfMass
            except Exception:
                com = 0

            bom.append(
                {
                    "component": comp,
                    "path": occPath,
                    "parentpath": GetParentPath(occPath),
                    "folder": folderName,
                    "partnumber": comp.partNumber,
                    "name": comp.name,
                    "instances": 1,
                    "quantity": 1,
                    "volume": GetBodiesVolume(comp.bRepBodies, BOMCreationMethod),
                    "area": GetPhysicsArea(comp.bRepBodies, BOMCreationMethod),
                    "mass": GetPhysicalMass(comp.bRepBodies, BOMCreationMethod),
                    "material": GetPhysicalMaterial(comp.bRepBodies, BOMCreationMethod),
                    "desc": CleanDescription(comp.description),
                    "com": com,
                }
            )

    csvStr = CollectData(bom, requiredColumns, BOMCreationMethod, delimiter)
    if not csvStr:
        MessageBox("No BOM data was generated.", 3)
        _log("CreateBOM: empty csv")
        return

    with open(filePath, "w", encoding="utf-8") as output:
        output.writelines(csvStr)

    if settingBOMExportFileType == "XLSX (.xlsx)":
        ExportXLSX(filePath)
    elif settingBOMExportFileType == "XML (.xml)":
        ExportXML(filePath)
    elif settingBOMExportFileType == "JSON (.json)":
        ExportJSON(filePath)

    MessageBox("BOM saved successfully.", 2)
    _log("CreateBOM: success")


def SetContextMenu(args):
    try:
        menuArgs = adsk.core.MarkingMenuEventArgs.cast(args)
        cmdDef1 = UI.commandDefinitions.itemById(COMMAND_ID + "_contextMenuButton1")
        cmdDef2 = UI.commandDefinitions.itemById(COMMAND_ID + "_contextMenuButton2")
        if not cmdDef1 or not cmdDef2:
            return

        linearMenu = menuArgs.linearMarkingMenu
        existing_sep = linearMenu.controls.itemById(COMMAND_ID + "_linearSeparator")
        if existing_sep:
            existing_sep.deleteMe()

        linearMenu.controls.addSeparator(COMMAND_ID + "_linearSeparator")
        dropdown = linearMenu.controls.addDropDown(COMMAND_NAME, "")
        dropdown.controls.addCommand(cmdDef1)
        dropdown.controls.addCommand(cmdDef2)
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))


class ContextMenuHandler(adsk.core.MarkingMenuEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            SetContextMenu(args)
        except Exception:
            if UI:
                UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))


class ContextMenuCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            updatingApp = UpdateCheck()
            if updatingApp is True:
                return

            command = args.command
            onExecute = CommandExecutedEventHandler()
            HANDLERS.append(onExecute)
            command.execute.add(onExecute)
        except Exception:
            if UI:
                UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))


class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            command = args.command

            onExecute = CommandExecutedEventHandler()
            command.execute.add(onExecute)
            HANDLERS.append(onExecute)

            onInputChanged = CommandInputChangedHandler()
            command.inputChanged.add(onInputChanged)
            HANDLERS.append(onInputChanged)

            command.isExecutedWhenPreEmpted = False

            appSettingsDictionary = SettingsLoad()
            inputs = command.commandInputs

            inputs.addImageCommandInput(COMMAND_ID + "_commandLogo", "", COMMAND_LOGO)

            uniqueID = "_BOMCreationMethod"
            settingBOMCreationMethod = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            inputBOMCreationMethod = inputs.addDropDownCommandInput(
                COMMAND_ID + uniqueID,
                TITLE_BOM_CREATION_METHOD,
                adsk.core.DropDownStyles.TextListDropDownStyle,
            )
            selectionTypeItems = inputBOMCreationMethod.listItems
            for i in range(len(LIST_BOM_CREATION_METHODS)):
                selectionTypeItems.add(LIST_BOM_CREATION_METHODS[i], False, "")
                if settingBOMCreationMethod == LIST_BOM_CREATION_METHODS[i]:
                    selectionTypeItems[i].isSelected = True
            inputBOMCreationMethod.tooltip = TOOLTIP_BOM_TYPE

            uniqueID = "_columnGroup"
            columnGroupInput = inputs.addGroupCommandInput(COMMAND_ID + uniqueID, TITLE_COLUMN_GROUP)
            columnGroupInput.isExpanded = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            columnGroupInputInputs = columnGroupInput.children

            uniqueID = "_columnTable"
            inputColumnTable = columnGroupInputInputs.addTableCommandInput(
                COMMAND_ID + uniqueID, TITLE_COLUMN_TABLE, 3, "1:2:2"
            )
            tableInputs = inputColumnTable.commandInputs

            uniqueID = "_tableRowMoveUp"
            tableButtonMoveUpInput = tableInputs.addBoolValueInput(
                COMMAND_ID + uniqueID, TITLE_TABLE_BUTTON_MOVE_UP, False, COMMAND_ICON_TABLE_MOVE_UP, True
            )
            tableButtonMoveUpInput.tooltip = TOOLTIP_TABLE_BUTTON_MOVE_UP
            inputColumnTable.addToolbarCommandInput(tableButtonMoveUpInput)

            uniqueID = "_tableRowMoveDown"
            tableButtonMoveDownInput = tableInputs.addBoolValueInput(
                COMMAND_ID + uniqueID, TITLE_TABLE_BUTTON_MOVE_DOWN, False, COMMAND_ICON_TABLE_MOVE_DOWN, True
            )
            tableButtonMoveDownInput.tooltip = TOOLTIP_TABLE_BUTTON_MOVE_DOWN
            inputColumnTable.addToolbarCommandInput(tableButtonMoveDownInput)

            uniqueID = "_tableRowAdd"
            tableButtonAddInput = tableInputs.addBoolValueInput(
                COMMAND_ID + uniqueID, TITLE_TABLE_BUTTON_ADD, False, COMMAND_ICON_TABLE_ADD, True
            )
            tableButtonAddInput.tooltip = TOOLTIP_TABLE_BUTTON_ADD
            inputColumnTable.addToolbarCommandInput(tableButtonAddInput)

            uniqueID = "_useCustomItemNumber"
            settingUseCustomItemNumber = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            inputUseCustomItemNumber = columnGroupInputInputs.addBoolValueInput(
                COMMAND_ID + uniqueID, TITLE_USE_CUSTOM_ITEM_NUMBER, True, "", settingUseCustomItemNumber
            )
            inputUseCustomItemNumber.tooltip = TOOLTIP_USE_CUSTOM_ITEM_NUMBER

            uniqueID = "_textCustomItemNumber"
            settingCustomItemNumber = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            inputCustomItemNumber = columnGroupInputInputs.addTextBoxCommandInput(
                COMMAND_ID + uniqueID, TITLE_CUSTOM_ITEM_NUMBER, settingCustomItemNumber, 1, False
            )
            inputCustomItemNumber.tooltip = TOOLTIP_CUSTOM_ITEM_NUMBER

            uniqueID = "_textCustomItemNumberPreview"
            inputCustomItemNumberPreview = columnGroupInputInputs.addTextBoxCommandInput(
                COMMAND_ID + uniqueID, TITLE_CUSTOM_ITEM_NUMBER_PREVIEW, "", 2, False
            )
            inputCustomItemNumberPreview.tooltip = TOOLTIP_CUSTOM_ITEM_NUMBER_PREVIEW
            inputCustomItemNumberPreview.isReadOnly = True

            uniqueID = "_exportGroup"
            exportGroupInput = inputs.addGroupCommandInput(COMMAND_ID + uniqueID, TITLE_EXPORT_GROUP)
            exportGroupInput.isExpanded = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            exportGroupInputInputs = exportGroupInput.children

            uniqueID = "_includeHiddenItems"
            settingIncludeHiddenItems = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            inputIncludeHiddenItems = exportGroupInputInputs.addBoolValueInput(
                COMMAND_ID + uniqueID, TITLE_INCLUDE_HIDDEN_ITEMS, True, "", settingIncludeHiddenItems
            )
            inputIncludeHiddenItems.tooltip = TOOLTIP_INCLUDE_HIDDEN_ITEMS

            uniqueID = "_includeParentComponents"
            settingIncludeParentComponents = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            inputIncludeParentComponents = exportGroupInputInputs.addBoolValueInput(
                COMMAND_ID + uniqueID, TITLE_INCLUDE_PARENT_COMPONENTS, True, "", settingIncludeParentComponents
            )
            inputIncludeParentComponents.tooltip = TOOLTIP_INCLUDE_PARENT_COMPONENTS

            uniqueID = "_includeLinkedComponents"
            settingIncludeLinkedComponents = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            inputIncludeLinkedComponents = exportGroupInputInputs.addBoolValueInput(
                COMMAND_ID + uniqueID, TITLE_INCLUDE_LINKED_COMPONENTS, True, "", settingIncludeLinkedComponents
            )
            inputIncludeLinkedComponents.tooltip = TOOLTIP_INCLUDE_LINKED_COMPONENTS

            uniqueID = "_BOMExportFileType"
            settingBOMExportFileType = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            inputBOMExportFileType = exportGroupInputInputs.addDropDownCommandInput(
                COMMAND_ID + uniqueID, TITLE_BOM_EXPORT_FILE_TYPE, adsk.core.DropDownStyles.TextListDropDownStyle
            )
            selectionTypeItems = inputBOMExportFileType.listItems
            for i in range(len(LIST_BOM_EXPORT_FILE_TYPES)):
                selectionTypeItems.add(LIST_BOM_EXPORT_FILE_TYPES[i], False, "")
                if settingBOMExportFileType == LIST_BOM_EXPORT_FILE_TYPES[i]:
                    selectionTypeItems[i].isSelected = True
            inputBOMExportFileType.tooltip = TOOLTIP_BOM_EXPORT_FILE_TYPE

            uniqueID = "_BOMDelimiterType"
            settingBOMDelimiterType = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            inputBOMDelimiterType = exportGroupInputInputs.addDropDownCommandInput(
                COMMAND_ID + uniqueID, TITLE_BOM_DELIMITER_TYPE, adsk.core.DropDownStyles.TextListDropDownStyle
            )
            selectionTypeItems = inputBOMDelimiterType.listItems
            for i in range(len(LIST_BOM_DELIMITER_TYPES)):
                selectionTypeItems.add(LIST_BOM_DELIMITER_TYPES[i], False, "")
                if settingBOMDelimiterType == LIST_BOM_DELIMITER_TYPES[i]:
                    selectionTypeItems[i].isSelected = True
            inputBOMDelimiterType.tooltip = TOOLTIP_BOM_DELIMITER_TYPE
            inputBOMDelimiterType.isVisible = settingBOMExportFileType == "CSV (.csv)"

            # Units group: allow per-export unit control.
            lengthUnit, areaUnit, volumeUnit, massUnit, comUnit = GetUnitSettings(appSettingsDictionary)
            uniqueID = "_unitsGroup"
            unitsGroupInput = inputs.addGroupCommandInput(COMMAND_ID + uniqueID, TITLE_UNITS_GROUP)
            unitsGroupInput.isExpanded = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            unitsGroupInput.tooltip = TOOLTIP_UNITS_GROUP
            unitsGroupInputInputs = unitsGroupInput.children

            inputLengthUnit = _add_dropdown(
                unitsGroupInputInputs,
                "_lengthUnit",
                TITLE_LENGTH_UNIT,
                LIST_LENGTH_UNITS,
                lengthUnit,
                TOOLTIP_LENGTH_UNIT,
            )
            inputAreaUnit = _add_dropdown(
                unitsGroupInputInputs,
                "_areaUnit",
                TITLE_AREA_UNIT,
                LIST_AREA_UNITS,
                areaUnit,
                TOOLTIP_AREA_UNIT,
            )
            inputVolumeUnit = _add_dropdown(
                unitsGroupInputInputs,
                "_volumeUnit",
                TITLE_VOLUME_UNIT,
                LIST_VOLUME_UNITS,
                volumeUnit,
                TOOLTIP_VOLUME_UNIT,
            )
            inputMassUnit = _add_dropdown(
                unitsGroupInputInputs,
                "_massUnit",
                TITLE_MASS_UNIT,
                LIST_MASS_UNITS,
                massUnit,
                TOOLTIP_MASS_UNIT,
            )
            inputComUnit = _add_dropdown(
                unitsGroupInputInputs,
                "_comUnit",
                TITLE_COM_UNIT,
                LIST_LENGTH_UNITS,
                comUnit,
                TOOLTIP_COM_UNIT,
            )

            uniqueID = "_filenameGroup"
            filenameGroupInput = inputs.addGroupCommandInput(COMMAND_ID + uniqueID, TITLE_FILENAME_GROUP)
            filenameGroupInput.isExpanded = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            filenameGroupInputInputs = filenameGroupInput.children

            uniqueID = "_BOMExportFilenameOption"
            settingBOMExportFilename = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            inputBOMExportFilename = filenameGroupInputInputs.addDropDownCommandInput(
                COMMAND_ID + uniqueID, TITLE_BOM_EXPORT_FILENAME, adsk.core.DropDownStyles.TextListDropDownStyle
            )
            selectionTypeItems = inputBOMExportFilename.listItems
            for i in range(len(LIST_BOM_EXPORT_FILENAME_OPTIONS)):
                selectionTypeItems.add(LIST_BOM_EXPORT_FILENAME_OPTIONS[i], False, "")
                if settingBOMExportFilename == LIST_BOM_EXPORT_FILENAME_OPTIONS[i]:
                    selectionTypeItems[i].isSelected = True
            inputBOMExportFilename.tooltip = TOOLTIP_BOM_EXPORT_FILENAME

            uniqueID = "_filenamePreview"
            inputFilenamePreview = filenameGroupInputInputs.addStringValueInput(
                COMMAND_ID + uniqueID, TITLE_FILENAME_PREVIEW, ""
            )
            inputFilenamePreview.isReadOnly = True
            inputFilenamePreview.tooltip = TOOLTIP_FILENAME_PREVIEW
            inputFilenamePreview.value = GetFilenameBOM(
                inputBOMExportFilename.selectedItem.name,
                inputBOMCreationMethod.selectedItem.name,
                inputBOMExportFileType.selectedItem.name,
                True,
            )

            uniqueID = "_settingsResetButton"
            inputButtonSettingsReset = inputs.addBoolValueInput(
                COMMAND_ID + uniqueID, TITLE_BUTTON_SETTINGS_RESET, False, COMMAND_ICON_SETTINGS_RESET, False
            )
            inputButtonSettingsReset.tooltip = TOOLTIP_BUTTON_SETTINGS_RESET

            uniqueID = "_settingsDictionaryText"
            settingsDictionaryData = SettingsGetValueForKey(appSettingsDictionary, uniqueID)
            debugMode = False
            inputSettingsDictionaryText = inputs.addTextBoxCommandInput(
                COMMAND_ID + uniqueID,
                TITLE_SETTINGS_DICTIONARY_TEXT,
                ConvertDictionaryToString(settingsDictionaryData),
                50,
                debugMode,
            )
            inputSettingsDictionaryText.isVisible = debugMode
            inputSettingsDictionaryText.isReadOnly = debugMode

            dataDictionary = ConvertStringToDictionary(inputSettingsDictionaryText.text)
            dataList = dataDictionary[inputBOMCreationMethod.selectedItem.name]
            TableCreateRows(inputColumnTable, dataList)

            GetCustomItemNumberVisibility(settingBOMCreationMethod, command)
            command.okButtonText = TITLE_COMMAND_OK_BUTTON
            _log("CommandCreated: settings UI ready")
        except Exception:
            if UI:
                UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))


class CommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            command = args.firingEvent.sender
            commandInput = args.input

            inputBOMCreationMethod = GetCommandForUniqueID("_BOMCreationMethod", command)
            inputIncludeHiddenItems = GetCommandForUniqueID("_includeHiddenItems", command)
            inputIncludeParentComponents = GetCommandForUniqueID("_includeParentComponents", command)
            inputIncludeLinkedComponents = GetCommandForUniqueID("_includeLinkedComponents", command)
            inputBOMExportFileType = GetCommandForUniqueID("_BOMExportFileType", command)
            inputBOMDelimiterType = GetCommandForUniqueID("_BOMDelimiterType", command)
            inputColumnTable = GetCommandForUniqueID("_columnTable", command)
            inputSettingsDictionaryText = GetCommandForUniqueID("_settingsDictionaryText", command)
            inputBOMExportFilename = GetCommandForUniqueID("_BOMExportFilenameOption", command)
            inputFilenamePreview = GetCommandForUniqueID("_filenamePreview", command)
            inputUnitsGroup = GetCommandForUniqueID("_unitsGroup", command)
            inputLengthUnit = GetCommandForUniqueID("_lengthUnit", command)
            inputAreaUnit = GetCommandForUniqueID("_areaUnit", command)
            inputVolumeUnit = GetCommandForUniqueID("_volumeUnit", command)
            inputMassUnit = GetCommandForUniqueID("_massUnit", command)
            inputComUnit = GetCommandForUniqueID("_comUnit", command)

            dataDictionary = ConvertStringToDictionary(inputSettingsDictionaryText.text)

            if commandInput.id == COMMAND_ID + "_settingsResetButton":
                SettingsReset(
                    inputColumnTable,
                    inputBOMCreationMethod,
                    inputIncludeHiddenItems,
                    inputIncludeParentComponents,
                    inputIncludeLinkedComponents,
                    inputBOMExportFileType,
                    inputBOMDelimiterType,
                    inputSettingsDictionaryText,
                    inputUnitsGroup,
                    inputLengthUnit,
                    inputAreaUnit,
                    inputVolumeUnit,
                    inputMassUnit,
                    inputComUnit,
                )
                return

            settingBOMCreationMethod = inputBOMCreationMethod.selectedItem.name
            if settingBOMCreationMethod not in dataDictionary:
                dataDictionary[settingBOMCreationMethod] = _method_default_list(settingBOMCreationMethod)

            dataList = dataDictionary[settingBOMCreationMethod]
            if commandInput.id == COMMAND_ID + "_BOMCreationMethod":
                TableCreateRows(inputColumnTable, dataList)
                inputSettingsDictionaryText.text = ConvertDictionaryToString(dataDictionary)

            dataDictionary = ConvertStringToDictionary(inputSettingsDictionaryText.text)
            dataList = dataDictionary[settingBOMCreationMethod]

            for inputColumnID in dataList:
                for key in inputColumnID.keys():
                    if commandInput.id == COMMAND_ID + key:
                        inputCheckbox = GetCommandForUniqueID(key, command)
                        newDataValue = inputColumnID[key]
                        newDataValue["_visible"] = inputCheckbox.value

                        boolCheckboxIsChecked = False
                        for keyData in dataList:
                            for _, dct in keyData.items():
                                if dct.get("_visible") is True:
                                    boolCheckboxIsChecked = True
                                    break
                            if boolCheckboxIsChecked:
                                break

                        if boolCheckboxIsChecked is False:
                            inputCheckbox.value = True
                            newDataValue["_visible"] = True

                        inputSettingsDictionaryText.text = ConvertDictionaryToString(dataDictionary)
                        break

                    if commandInput.id == COMMAND_ID + key + "_alias":
                        inputAliasString = GetCommandForUniqueID(key + "_alias", command)
                        newDataValue = inputColumnID[key]
                        newDataValue["_alias"] = inputAliasString.value
                        inputSettingsDictionaryText.text = ConvertDictionaryToString(dataDictionary)
                        break

            if commandInput.id == COMMAND_ID + "_tableRowMoveUp":
                TableMoveRow(
                    "Up",
                    inputColumnTable,
                    inputColumnTable.selectedRow,
                    inputSettingsDictionaryText,
                    settingBOMCreationMethod,
                )
                commandInput.value = False
            elif commandInput.id == COMMAND_ID + "_tableRowMoveDown":
                TableMoveRow(
                    "Down",
                    inputColumnTable,
                    inputColumnTable.selectedRow,
                    inputSettingsDictionaryText,
                    settingBOMCreationMethod,
                )
                commandInput.value = False
            elif commandInput.id == COMMAND_ID + "_tableRowAdd":
                TableAddRow(inputColumnTable, inputSettingsDictionaryText, settingBOMCreationMethod)
                commandInput.value = False

            if commandInput.id == COMMAND_ID + "_BOMExportFileType":
                settingBOMExportFileType = inputBOMExportFileType.selectedItem.name
                inputBOMDelimiterType.isVisible = settingBOMExportFileType == "CSV (.csv)"

            inputFilenamePreview.value = GetFilenameBOM(
                inputBOMExportFilename.selectedItem.name,
                inputBOMCreationMethod.selectedItem.name,
                inputBOMExportFileType.selectedItem.name,
                True,
            )

            GetCustomItemNumberVisibility(settingBOMCreationMethod, command)
        except Exception:
            if UI:
                UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))


class CommandExecutedEventHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            command = args.firingEvent.sender
            cmdDef = command.parentCommandDefinition
            appSettingsDictionary = SettingsLoad()

            if cmdDef.id == COMMAND_ID + "_contextMenuButton2":
                settingsKey = "_BOMCreationMethod"
                inputBOMCreationMethod = GetCommandForUniqueID(settingsKey, command)
                SettingsSetValueForKey(appSettingsDictionary, settingsKey, inputBOMCreationMethod.selectedItem.name)

                settingsKey = "_settingsDictionaryText"
                inputSettingsDictionaryText = GetCommandForUniqueID(settingsKey, command)
                dataDictionary = ConvertStringToDictionary(inputSettingsDictionaryText.text)
                SettingsSetValueForKey(appSettingsDictionary, settingsKey, dataDictionary)

                settingsKey = "_useCustomItemNumber"
                inputUseCustomItemNumber = GetCommandForUniqueID(settingsKey, command)
                SettingsSetValueForKey(appSettingsDictionary, settingsKey, inputUseCustomItemNumber.value)

                settingsKey = "_textCustomItemNumber"
                inputCustomItemNumber = GetCommandForUniqueID(settingsKey, command)
                SettingsSetValueForKey(appSettingsDictionary, settingsKey, inputCustomItemNumber.text)

                settingsKey = "_includeHiddenItems"
                inputIncludeHiddenItems = GetCommandForUniqueID(settingsKey, command)
                SettingsSetValueForKey(appSettingsDictionary, settingsKey, inputIncludeHiddenItems.value)

                settingsKey = "_includeParentComponents"
                inputIncludeParentComponents = GetCommandForUniqueID(settingsKey, command)
                SettingsSetValueForKey(appSettingsDictionary, settingsKey, inputIncludeParentComponents.value)

                settingsKey = "_includeLinkedComponents"
                inputIncludeLinkedComponents = GetCommandForUniqueID(settingsKey, command)
                SettingsSetValueForKey(appSettingsDictionary, settingsKey, inputIncludeLinkedComponents.value)

                settingsKey = "_BOMExportFileType"
                inputBOMExportFileType = GetCommandForUniqueID(settingsKey, command)
                SettingsSetValueForKey(appSettingsDictionary, settingsKey, inputBOMExportFileType.selectedItem.name)

                settingsKey = "_BOMDelimiterType"
                inputBOMDelimiterType = GetCommandForUniqueID(settingsKey, command)
                SettingsSetValueForKey(appSettingsDictionary, settingsKey, inputBOMDelimiterType.selectedItem.name)

                settingsKey = "_BOMExportFilenameOption"
                inputBOMExportFilename = GetCommandForUniqueID(settingsKey, command)
                SettingsSetValueForKey(appSettingsDictionary, settingsKey, inputBOMExportFilename.selectedItem.name)

                settingsKey = "_columnGroup"
                SettingsSetValueForKey(appSettingsDictionary, settingsKey, GetCommandForUniqueID(settingsKey, command).isExpanded)
                settingsKey = "_exportGroup"
                SettingsSetValueForKey(appSettingsDictionary, settingsKey, GetCommandForUniqueID(settingsKey, command).isExpanded)
                settingsKey = "_filenameGroup"
                SettingsSetValueForKey(appSettingsDictionary, settingsKey, GetCommandForUniqueID(settingsKey, command).isExpanded)

                settingsKey = "_unitsGroup"
                unitsGroup = GetCommandForUniqueID(settingsKey, command)
                if unitsGroup:
                    SettingsSetValueForKey(appSettingsDictionary, settingsKey, unitsGroup.isExpanded)

                for settingsKey in (
                    "_lengthUnit",
                    "_areaUnit",
                    "_volumeUnit",
                    "_massUnit",
                    "_comUnit",
                ):
                    unitInput = GetCommandForUniqueID(settingsKey, command)
                    if unitInput and unitInput.selectedItem:
                        SettingsSetValueForKey(
                            appSettingsDictionary, settingsKey, unitInput.selectedItem.name
                        )

                SettingsSave(appSettingsDictionary)
                MessageBox("Settings have been updated successfully.", 2)
                _log("Settings updated")
            else:
                CreateBOM()
        except Exception:
            if UI:
                UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))

MARKING_MENU_HANDLER = None


def _delete_cmd_def(cmd_id):
    try:
        cmd = UI.commandDefinitions.itemById(cmd_id)
        if cmd:
            cmd.deleteMe()
    except Exception:
        pass


def run(context):
    global MARKING_MENU_HANDLER
    try:
        _delete_cmd_def(COMMAND_ID)
        _delete_cmd_def(COMMAND_ID + "_contextMenuButton1")
        _delete_cmd_def(COMMAND_ID + "_contextMenuButton2")

        if MARKING_MENU_HANDLER:
            try:
                UI.markingMenuDisplaying.remove(MARKING_MENU_HANDLER)
            except Exception:
                pass
            MARKING_MENU_HANDLER = None

        contextMenuOnCommandCreated = ContextMenuCommandCreatedEventHandler()
        onMarkingMenuDisplaying = ContextMenuHandler()
        onCommandCreated = CommandCreatedEventHandler()

        HANDLERS.append(contextMenuOnCommandCreated)
        HANDLERS.append(onMarkingMenuDisplaying)
        HANDLERS.append(onCommandCreated)

        UI.markingMenuDisplaying.add(onMarkingMenuDisplaying)
        MARKING_MENU_HANDLER = onMarkingMenuDisplaying

        icon_folder = COMMAND_ICON if os.path.isdir(COMMAND_ICON) else ""
        settings_icon_folder = COMMAND_ICON_SETTINGS if os.path.isdir(COMMAND_ICON_SETTINGS) else ""
        if not icon_folder:
            _log("run: missing icon folder {}".format(COMMAND_ICON))
        if not settings_icon_folder:
            _log("run: missing settings icon folder {}".format(COMMAND_ICON_SETTINGS))

        cmdDef1 = UI.commandDefinitions.addButtonDefinition(
            COMMAND_ID + "_contextMenuButton1", STRING_CREATE_BOM, "", icon_folder
        )
        cmdDef2 = UI.commandDefinitions.addButtonDefinition(
            COMMAND_ID + "_contextMenuButton2", STRING_SETTINGS, "", settings_icon_folder
        )

        cmdDef1.commandCreated.add(contextMenuOnCommandCreated)
        cmdDef2.commandCreated.add(onCommandCreated)

        CUSTOM_COMMAND_DEFINITIONS.append(cmdDef1)
        CUSTOM_COMMAND_DEFINITIONS.append(cmdDef2)

        _log("run: PhilsBom initialized")
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))


def stop(context):
    global MARKING_MENU_HANDLER
    try:
        _delete_cmd_def(COMMAND_ID)
        _delete_cmd_def(COMMAND_ID + "_contextMenuButton1")
        _delete_cmd_def(COMMAND_ID + "_contextMenuButton2")

        if MARKING_MENU_HANDLER:
            try:
                UI.markingMenuDisplaying.remove(MARKING_MENU_HANDLER)
            except Exception:
                pass
            MARKING_MENU_HANDLER = None

        HANDLERS.clear()
        for obj in CUSTOM_COMMAND_DEFINITIONS:
            if getattr(obj, "isValid", False):
                obj.deleteMe()
        CUSTOM_COMMAND_DEFINITIONS.clear()

        _log("stop: PhilsBom stopped")
    except Exception:
        if UI:
            UI.messageBox("ERROR:\n{}".format(traceback.format_exc()))
