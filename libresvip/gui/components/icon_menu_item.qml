import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Controls.impl
import QtQuick.Controls.Material

MenuItem {
    property string icon_name: ""
    property string label: ""
    contentItem: Row {
        Label {
            text: py.qta.icon(icon_name)
            font.family: materialFontLoader.name
            font.pixelSize: Qt.application.font.pixelSize * 1.2
            width: 35
            anchors.verticalCenter: parent.verticalCenter
        }
        Label {
            text: qsTr(label);
            width: parent.width - 35
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}