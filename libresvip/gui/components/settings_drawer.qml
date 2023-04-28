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

    Column {
        anchors.fill: parent
        anchors.margins: 10
        Switch {
            text: qsTr("Auto-Detect Input File Type")
        }
        Switch {
            text: qsTr("Reset Task List When Changing Input File Type")
        }
        Switch {
            text: qsTr("Set Output File Extension Automatically")
        }
        Switch {
            text: qsTr("Multi-Threaded Conversion")
        }
        Switch {
            text: qsTr("Open Save Path When Finished")
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
            }
            RadioButton {
                text: qsTr("Desktop")
                onClicked: {
                    let path = dialogs.url2path(StandardPaths.standardLocations(StandardPaths.DesktopLocation)[0])
                    converterPage.saveFolder.text = path
                    py.config_items.set_save_folder(path)
                }
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