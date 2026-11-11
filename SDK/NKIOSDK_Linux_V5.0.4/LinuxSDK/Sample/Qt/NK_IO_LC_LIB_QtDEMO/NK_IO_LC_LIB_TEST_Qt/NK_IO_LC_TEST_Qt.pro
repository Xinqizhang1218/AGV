QT       += core gui
QT       += serialport
QMAKE_LFLAGS += -no-pie
greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

CONFIG += c++11

# The following define makes your compiler emit warnings if you use
# any Qt feature that has been marked deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS

# You can also make your code fail to compile if it uses deprecated APIs.
# In order to do so, uncomment the following line.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

SOURCES += \
    dioLcAdapter.cpp \
    dioTestPage.cpp \
    ledWidget.cpp \
    lightControlPage.cpp \
    loginDialog.cpp \
    main.cpp \
    mainWindow.cpp \
    navigationWidget.cpp \
    rightWidget.cpp \
    switchButton.cpp

HEADERS += \
    NKIOLIB.h \
    NKLCLIB.h \
    dioLcAdapter.h \
    dioTestPage.h \
    ledWidget.h \
    lightControlPage.h \
    loginDialog.h \
    mainWindow.h \
    navigationWidget.h \
    rightWidget.h \
    switchButton.h

FORMS += \
    dioTestPage.ui \
    lightControlPage.ui \
    loginDialog.ui \
    mainWindow.ui \
    navigationWidget.ui \
    rightWidget.ui

# Default rules for deployment.
qnx: target.path = /tmp/$${TARGET}/bin
else: unix:!android: target.path = /opt/$${TARGET}/bin
!isEmpty(target.path): INSTALLS += target


RESOURCES += \
    mainWindow.qrc



unix:!macx: LIBS += -L$$PWD/./ -lNKLCLIB

INCLUDEPATH += $$PWD/.
DEPENDPATH += $$PWD/.

unix:!macx: PRE_TARGETDEPS += $$PWD/./libNKLCLIB.a


unix:!macx: LIBS += -L$$PWD/./ -lNKIOLIB

INCLUDEPATH += $$PWD/.
DEPENDPATH += $$PWD/.

unix:!macx: PRE_TARGETDEPS += $$PWD/./libNKIOLIB.a


