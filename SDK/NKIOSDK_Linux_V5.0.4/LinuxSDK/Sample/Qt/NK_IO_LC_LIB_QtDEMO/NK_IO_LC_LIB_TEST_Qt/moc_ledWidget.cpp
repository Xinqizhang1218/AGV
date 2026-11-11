/****************************************************************************
** Meta object code from reading C++ file 'ledWidget.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.13.2)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include <memory>
#include "ledWidget.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'ledWidget.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.13.2. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
struct qt_meta_stringdata_ledWidget_t {
    QByteArrayData data[10];
    char stringdata0[69];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    qptrdiff(offsetof(qt_meta_stringdata_ledWidget_t, stringdata0) + ofs \
        - idx * sizeof(QByteArrayData)) \
    )
static const qt_meta_stringdata_ledWidget_t qt_meta_stringdata_ledWidget = {
    {
QT_MOC_LITERAL(0, 0, 9), // "ledWidget"
QT_MOC_LITERAL(1, 10, 10), // "setOnColor"
QT_MOC_LITERAL(2, 21, 0), // ""
QT_MOC_LITERAL(3, 22, 5), // "color"
QT_MOC_LITERAL(4, 28, 11), // "setOffColor"
QT_MOC_LITERAL(5, 40, 6), // "toggle"
QT_MOC_LITERAL(6, 47, 6), // "turnOn"
QT_MOC_LITERAL(7, 54, 2), // "on"
QT_MOC_LITERAL(8, 57, 7), // "turnOff"
QT_MOC_LITERAL(9, 65, 3) // "off"

    },
    "ledWidget\0setOnColor\0\0color\0setOffColor\0"
    "toggle\0turnOn\0on\0turnOff\0off"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_ledWidget[] = {

 // content:
       8,       // revision
       0,       // classname
       0,    0, // classinfo
       7,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       0,       // signalCount

 // slots: name, argc, parameters, tag, flags
       1,    1,   49,    2, 0x0a /* Public */,
       4,    1,   52,    2, 0x0a /* Public */,
       5,    0,   55,    2, 0x0a /* Public */,
       6,    1,   56,    2, 0x0a /* Public */,
       6,    0,   59,    2, 0x2a /* Public | MethodCloned */,
       8,    1,   60,    2, 0x0a /* Public */,
       8,    0,   63,    2, 0x2a /* Public | MethodCloned */,

 // slots: parameters
    QMetaType::Void, QMetaType::QColor,    3,
    QMetaType::Void, QMetaType::QColor,    3,
    QMetaType::Void,
    QMetaType::Void, QMetaType::Bool,    7,
    QMetaType::Void,
    QMetaType::Void, QMetaType::Bool,    9,
    QMetaType::Void,

       0        // eod
};

void ledWidget::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        auto *_t = static_cast<ledWidget *>(_o);
        Q_UNUSED(_t)
        switch (_id) {
        case 0: _t->setOnColor((*reinterpret_cast< const QColor(*)>(_a[1]))); break;
        case 1: _t->setOffColor((*reinterpret_cast< const QColor(*)>(_a[1]))); break;
        case 2: _t->toggle(); break;
        case 3: _t->turnOn((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 4: _t->turnOn(); break;
        case 5: _t->turnOff((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 6: _t->turnOff(); break;
        default: ;
        }
    }
}

QT_INIT_METAOBJECT const QMetaObject ledWidget::staticMetaObject = { {
    &QWidget::staticMetaObject,
    qt_meta_stringdata_ledWidget.data,
    qt_meta_data_ledWidget,
    qt_static_metacall,
    nullptr,
    nullptr
} };


const QMetaObject *ledWidget::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *ledWidget::qt_metacast(const char *_clname)
{
    if (!_clname) return nullptr;
    if (!strcmp(_clname, qt_meta_stringdata_ledWidget.stringdata0))
        return static_cast<void*>(this);
    return QWidget::qt_metacast(_clname);
}

int ledWidget::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QWidget::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 7)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 7;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 7)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 7;
    }
    return _id;
}
QT_WARNING_POP
QT_END_MOC_NAMESPACE
