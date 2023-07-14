import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import QtQuick.Shapes

GridLayout {
    property var info
    rows: 10
    columns: 10

    Image {
        Layout.row: 0
        Layout.column: 0
        Layout.rowSpan: 3
        Layout.columnSpan: 3
        sourceSize.width: 100
        sourceSize.height: 100
        source: info.icon_base64
        fillMode: Image.PreserveAspectFit
        Shape {
            layer.enabled: true
            layer.samples: 4
            layer.smooth: true
            anchors.fill: parent

            ShapePath {
                startX: 0
                startY: 0
                fillColor: window.Material.dialogColor
                strokeColor: "transparent"
                PathLine { x: 50; y: 0 }
                PathArc {x: 0; y: 50; radiusX: 50; radiusY: 50; direction: PathArc.Counterclockwise }
                PathLine { x: 0; y: 0 }
            }

            ShapePath {
                startX: 0
                startY: 100
                fillColor: window.Material.dialogColor
                strokeColor: "transparent"
                PathLine { x: 50; y: 100 }
                PathArc {x: 0; y: 50; radiusX: 50; radiusY: 50; direction: PathArc.Clockwise }
                PathLine { x: 0; y: 100 }
            }

            ShapePath {
                startX: 100
                startY: 0
                fillColor: window.Material.dialogColor
                strokeColor: "transparent"
                PathLine { x: 50; y: 0 }
                PathArc {x: 100; y: 50; radiusX: 50; radiusY: 50; direction: PathArc.Clockwise }
                PathLine { x: 100; y: 0 }
            }

            ShapePath {
                startX: 100
                startY: 100
                fillColor: window.Material.dialogColor
                strokeColor: "transparent"
                PathLine { x: 50; y: 100 }
                PathArc {x: 100; y: 50; radiusX: 50; radiusY: 50; direction: PathArc.Counterclockwise }
                PathLine { x: 100; y: 100 }
            }
        }
    }

    Label {
        Layout.row: 0
        Layout.column: 3
        Layout.columnSpan: 7
        text: qsTr(info.name)
        font.pixelSize: 30
        font.bold: true
    }

    Button {
        Layout.row: 1
        Layout.column: 3
        Layout.columnSpan: 3
        background: Rectangle {
            color: "transparent"
        }
        contentItem: RowLayout {
            Label {
                text: py.qta.icon("mdi6.tag")
                font.family: materialFontLoader.name
            }
            Label {
                text: info.version
            }
        }
        ToolTip {
            z: 1
            visible: parent.hovered
            text: qsTr("Version")
        }
    }

    Button {
        Layout.row: 1
        Layout.column: 6
        Layout.columnSpan: 4
        background: Rectangle {
            color: "transparent"
        }
        contentItem: RowLayout {
            Label {
                text: py.qta.icon("mdi6.account")
                font.family: materialFontLoader.name
            }

            Label {
                text: info.author
                font.underline: true
                HoverHandler {
                    acceptedDevices: PointerDevice.AllPointerTypes
                    cursorShape: Qt.PointingHandCursor
                }
            }

            Label {
                text: py.qta.icon("mdi6.open-in-new")
                font.family: materialFontLoader.name
            }
        }
        ToolTip {
            z: 1
            visible: parent.hovered
            text: info.website
        }
        onClicked: Qt.openUrlExternally(info.website)
    }

    RowLayout {
        Layout.row: 2
        Layout.column: 3
        Layout.columnSpan: 7
        Label {
            text: py.qta.icon("mdi6.file-outline")
            font.family: materialFontLoader.name
        }
        Label {
            text: qsTr(info.file_format) + " " + info.suffix
        }
    }

    Rectangle {
        Layout.row: 3
        Layout.column: 0
        Layout.columnSpan: 10
        Layout.fillWidth: true
        height: 1
        color: Material.color(Material.Gray, Material.Shade0)
        border.color: Material.color(
            Material.Black,
            Material.Shade0
        )
        border.width: 1
    }

    ColumnLayout {
        Layout.row: 4
        Layout.column: 0
        Layout.columnSpan: 10
        spacing: 10
        Label {
            text: qsTr("Introduction")
            font.bold: true
        }
        Label {
            Layout.maximumWidth: 500
            text: qsTr(info.description)
            wrapMode: Text.Wrap
        }
    }
}