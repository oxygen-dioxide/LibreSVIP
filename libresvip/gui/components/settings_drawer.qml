import QtCore
import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

Drawer {
    width: window.width * 0.3
    height: window.height
    signal openSettings()
    signal autoOpenSaveFolderChanged(bool value)
    signal autoSetOutputFileExtensionChanged(bool value)
    signal resetTasksOnInputChangeChanged(bool value)
    signal autoDetectInputFormatChanged(bool value)

    Column {
        anchors.fill: parent
        anchors.margins: 10
        Switch {
            text: qsTr("Auto-Detect Input File Type")
            checked: py.config_items.get_bool("auto_detect_input_format")
            onClicked: {
                py.config_items.set_bool("auto_detect_input_format", checked)
                autoDetectInputFormatChanged(checked)
            }
            Component.onCompleted: {
                autoDetectInputFormatChanged.connect( (value) => {
                    value === checked ? null : checked = value
                })
            }
        }
        Switch {
            text: qsTr("Reset Task List When Changing Input File Type")
            checked: py.config_items.get_bool("reset_tasks_on_input_change")
            onClicked: {
                py.config_items.set_bool("reset_tasks_on_input_change", checked)
                resetTasksOnInputChangeChanged(checked)
            }
            Component.onCompleted: {
                resetTasksOnInputChangeChanged.connect( (value) => {
                    value === checked ? null : checked = value
                })
            }
        }
        Switch {
            text: qsTr("Set Output File Extension Automatically")
            checked: py.config_items.get_bool("auto_set_output_extension")
            onClicked: {
                py.config_items.set_bool("auto_set_output_extension", checked)
                autoSetOutputFileExtensionChanged(checked)
            }
            Component.onCompleted: {
                autoSetOutputFileExtensionChanged.connect( (value) => {
                    value === checked ? null : checked = value
                })
            }
        }
        Switch {
            text: qsTr("Multi-Threaded Conversion")
            checked: py.config_items.get_bool("multi_threaded_conversion")
            onClicked: {
                py.config_items.set_bool("multi_threaded_conversion", checked)
            }
        }
        Switch {
            text: qsTr("Open Output Folder When Done")
            checked: py.config_items.get_bool("open_save_folder_on_completion")
            onClicked: {
                py.config_items.set_bool("open_save_folder_on_completion", checked)
                autoOpenSaveFolderChanged(checked)
            }
            Component.onCompleted: {
                autoOpenSaveFolderChanged.connect( (value) => {
                    value === checked ? null : checked = value
                })
            }
        }
        Switch {
            text: qsTr("Auto Check for Updates")
        }
        ColumnLayout {
            anchors.margins: 20
            Label {
                text: qsTr("Set Save Path")
                font.bold: true
            }
            RadioButton {
                text: qsTr("Same as Source")
                onClicked: {
                    let path = "."
                    converterPage.saveFolder.text = path
                    py.config_items.set_save_folder(path)
                }
                checked: py.config_items.get_save_folder() === "."
            }
            RadioButton {
                text: qsTr("Desktop")
                onClicked: {
                    let path = dialogs.url2path(StandardPaths.standardLocations(StandardPaths.DesktopLocation)[0])
                    converterPage.saveFolder.text = path
                    py.config_items.set_save_folder(path)
                }
                checked: py.config_items.get_save_folder() === dialogs.url2path(
                    StandardPaths.standardLocations(StandardPaths.DesktopLocation)[0]
                )
            }
            RadioButton {
                text: qsTr("Custom (Browse ...)")
                onClicked: {
                    actions.chooseSavePath.trigger()
                }
            }
        }
        ColumnLayout {
            anchors.margins: 20
            Label {
                text: qsTr("Deal With Existing Files")
                font.bold: true
            }
            RadioButton {
                text: qsTr("Overwrite")
                onClicked: {
                }
            }
            RadioButton {
                text: qsTr("Skip")
                onClicked: {
                }
            }
            RadioButton {
                text: qsTr("Prompt")
                onClicked: {
                }
            }
        }
    }
    Component.onCompleted: {
        openSettings.connect(this.open)
    }
}