/****************************************************************************
** Meta object code from reading C++ file 'dioLcAdapter.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.13.2)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include <memory>
#include "dioLcAdapter.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'dioLcAdapter.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.13.2. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
struct qt_meta_stringdata_CDioLcAdapter_t {
    QByteArrayData data[44];
    char stringdata0[671];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    qptrdiff(offsetof(qt_meta_stringdata_CDioLcAdapter_t, stringdata0) + ofs \
        - idx * sizeof(QByteArrayData)) \
    )
static const qt_meta_stringdata_CDioLcAdapter_t qt_meta_stringdata_CDioLcAdapter = {
    {
QT_MOC_LITERAL(0, 0, 13), // "CDioLcAdapter"
QT_MOC_LITERAL(1, 14, 15), // "signalComOpenCB"
QT_MOC_LITERAL(2, 30, 0), // ""
QT_MOC_LITERAL(3, 31, 7), // "portNum"
QT_MOC_LITERAL(4, 39, 18), // "ucHardwareMajorVer"
QT_MOC_LITERAL(5, 58, 18), // "ucHardwareMinorVer"
QT_MOC_LITERAL(6, 77, 16), // "ucHardwareRevVer"
QT_MOC_LITERAL(7, 94, 18), // "ucFirmwareMajorVer"
QT_MOC_LITERAL(8, 113, 18), // "ucFirmwareMinorVer"
QT_MOC_LITERAL(9, 132, 16), // "ucFirmwareRevVer"
QT_MOC_LITERAL(10, 149, 7), // "ucError"
QT_MOC_LITERAL(11, 157, 9), // "uiErrorId"
QT_MOC_LITERAL(12, 167, 16), // "signalComCloseCB"
QT_MOC_LITERAL(13, 184, 20), // "signalGetDeviceVerCB"
QT_MOC_LITERAL(14, 205, 20), // "signalSetPwmParamsCB"
QT_MOC_LITERAL(15, 226, 7), // "ucChIdx"
QT_MOC_LITERAL(16, 234, 20), // "signalGetPwmParamsCB"
QT_MOC_LITERAL(17, 255, 9), // "ucPwmMode"
QT_MOC_LITERAL(18, 265, 10), // "ucPwmValue"
QT_MOC_LITERAL(19, 276, 16), // "ucPwmHoldingTime"
QT_MOC_LITERAL(20, 293, 10), // "ucPwmOnOff"
QT_MOC_LITERAL(21, 304, 23), // "signalSetGeneralParamCB"
QT_MOC_LITERAL(22, 328, 7), // "paramId"
QT_MOC_LITERAL(23, 336, 10), // "paramValue"
QT_MOC_LITERAL(24, 347, 23), // "signalGetGeneralParamCB"
QT_MOC_LITERAL(25, 371, 19), // "signalIapDownloadCB"
QT_MOC_LITERAL(26, 391, 7), // "ucDevId"
QT_MOC_LITERAL(27, 399, 15), // "uiFileTotalSize"
QT_MOC_LITERAL(28, 415, 20), // "uiFileSizeDownloaded"
QT_MOC_LITERAL(29, 436, 11), // "slotTimeout"
QT_MOC_LITERAL(30, 448, 17), // "slotBoardOpenPort"
QT_MOC_LITERAL(31, 466, 5), // "devId"
QT_MOC_LITERAL(32, 472, 4), // "port"
QT_MOC_LITERAL(33, 477, 18), // "slotBoardClosePort"
QT_MOC_LITERAL(34, 496, 23), // "slotBoardIsDeviceOpened"
QT_MOC_LITERAL(35, 520, 19), // "slotBoardGetVerInfo"
QT_MOC_LITERAL(36, 540, 21), // "slotBoardSetPwmParams"
QT_MOC_LITERAL(37, 562, 21), // "slotBoardGetPwmParams"
QT_MOC_LITERAL(38, 584, 19), // "slotSetGeneralParam"
QT_MOC_LITERAL(39, 604, 9), // "ucParamId"
QT_MOC_LITERAL(40, 614, 10), // "ucParamLen"
QT_MOC_LITERAL(41, 625, 19), // "slotGetGeneralParam"
QT_MOC_LITERAL(42, 645, 15), // "slotIapDownload"
QT_MOC_LITERAL(43, 661, 9) // "imageFile"

    },
    "CDioLcAdapter\0signalComOpenCB\0\0portNum\0"
    "ucHardwareMajorVer\0ucHardwareMinorVer\0"
    "ucHardwareRevVer\0ucFirmwareMajorVer\0"
    "ucFirmwareMinorVer\0ucFirmwareRevVer\0"
    "ucError\0uiErrorId\0signalComCloseCB\0"
    "signalGetDeviceVerCB\0signalSetPwmParamsCB\0"
    "ucChIdx\0signalGetPwmParamsCB\0ucPwmMode\0"
    "ucPwmValue\0ucPwmHoldingTime\0ucPwmOnOff\0"
    "signalSetGeneralParamCB\0paramId\0"
    "paramValue\0signalGetGeneralParamCB\0"
    "signalIapDownloadCB\0ucDevId\0uiFileTotalSize\0"
    "uiFileSizeDownloaded\0slotTimeout\0"
    "slotBoardOpenPort\0devId\0port\0"
    "slotBoardClosePort\0slotBoardIsDeviceOpened\0"
    "slotBoardGetVerInfo\0slotBoardSetPwmParams\0"
    "slotBoardGetPwmParams\0slotSetGeneralParam\0"
    "ucParamId\0ucParamLen\0slotGetGeneralParam\0"
    "slotIapDownload\0imageFile"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_CDioLcAdapter[] = {

 // content:
       8,       // revision
       0,       // classname
       0,    0, // classinfo
      18,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       8,       // signalCount

 // signals: name, argc, parameters, tag, flags
       1,    9,  104,    2, 0x06 /* Public */,
      12,    2,  123,    2, 0x06 /* Public */,
      13,    8,  128,    2, 0x06 /* Public */,
      14,    3,  145,    2, 0x06 /* Public */,
      16,    7,  152,    2, 0x06 /* Public */,
      21,    4,  167,    2, 0x06 /* Public */,
      24,    4,  176,    2, 0x06 /* Public */,
      25,    5,  185,    2, 0x06 /* Public */,

 // slots: name, argc, parameters, tag, flags
      29,    0,  196,    2, 0x0a /* Public */,
      30,    2,  197,    2, 0x0a /* Public */,
      33,    2,  202,    2, 0x0a /* Public */,
      34,    1,  207,    2, 0x0a /* Public */,
      35,    1,  210,    2, 0x0a /* Public */,
      36,    6,  213,    2, 0x0a /* Public */,
      37,    2,  226,    2, 0x0a /* Public */,
      38,    6,  231,    2, 0x0a /* Public */,
      41,    6,  244,    2, 0x0a /* Public */,
      42,    2,  257,    2, 0x0a /* Public */,

 // signals: parameters
    QMetaType::Void, QMetaType::UShort, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UInt,    3,    4,    5,    6,    7,    8,    9,   10,   11,
    QMetaType::Void, QMetaType::UChar, QMetaType::UInt,   10,   11,
    QMetaType::Void, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UInt,    4,    5,    6,    7,    8,    9,   10,   11,
    QMetaType::Void, QMetaType::UChar, QMetaType::UChar, QMetaType::UInt,   15,   10,   11,
    QMetaType::Void, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UInt,   15,   17,   18,   19,   20,   10,   11,
    QMetaType::Void, QMetaType::UChar, QMetaType::UInt, QMetaType::UChar, QMetaType::UInt,   22,   23,   10,   11,
    QMetaType::Void, QMetaType::UChar, QMetaType::UInt, QMetaType::UChar, QMetaType::UInt,   22,   23,   10,   11,
    QMetaType::Void, QMetaType::UChar, QMetaType::UInt, QMetaType::UInt, QMetaType::UChar, QMetaType::UInt,   26,   27,   28,   10,   11,

 // slots: parameters
    QMetaType::Void,
    QMetaType::Int, QMetaType::UInt, QMetaType::UShort,   31,   32,
    QMetaType::Int, QMetaType::UInt, QMetaType::UShort,   31,   32,
    QMetaType::Int, QMetaType::UChar,   31,
    QMetaType::Int, QMetaType::UInt,   31,
    QMetaType::Int, QMetaType::UInt, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar,   31,   15,   17,   18,   19,   20,
    QMetaType::Int, QMetaType::UInt, QMetaType::UChar,   31,   15,
    QMetaType::Int, QMetaType::UInt, QMetaType::UChar, QMetaType::UChar, QMetaType::UInt, QMetaType::UChar, QMetaType::UInt,   31,   39,   40,   23,   10,   11,
    QMetaType::Int, QMetaType::UInt, QMetaType::UChar, QMetaType::UChar, QMetaType::UInt, QMetaType::UChar, QMetaType::UInt,   31,   39,   40,   23,   10,   11,
    QMetaType::Int, QMetaType::UInt, QMetaType::QString,   31,   43,

       0        // eod
};

void CDioLcAdapter::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        auto *_t = static_cast<CDioLcAdapter *>(_o);
        Q_UNUSED(_t)
        switch (_id) {
        case 0: _t->signalComOpenCB((*reinterpret_cast< unsigned short(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< unsigned char(*)>(_a[4])),(*reinterpret_cast< unsigned char(*)>(_a[5])),(*reinterpret_cast< unsigned char(*)>(_a[6])),(*reinterpret_cast< unsigned char(*)>(_a[7])),(*reinterpret_cast< unsigned char(*)>(_a[8])),(*reinterpret_cast< uint(*)>(_a[9]))); break;
        case 1: _t->signalComCloseCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< uint(*)>(_a[2]))); break;
        case 2: _t->signalGetDeviceVerCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< unsigned char(*)>(_a[4])),(*reinterpret_cast< unsigned char(*)>(_a[5])),(*reinterpret_cast< unsigned char(*)>(_a[6])),(*reinterpret_cast< unsigned char(*)>(_a[7])),(*reinterpret_cast< uint(*)>(_a[8]))); break;
        case 3: _t->signalSetPwmParamsCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< uint(*)>(_a[3]))); break;
        case 4: _t->signalGetPwmParamsCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< unsigned char(*)>(_a[4])),(*reinterpret_cast< unsigned char(*)>(_a[5])),(*reinterpret_cast< unsigned char(*)>(_a[6])),(*reinterpret_cast< uint(*)>(_a[7]))); break;
        case 5: _t->signalSetGeneralParamCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< uint(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< uint(*)>(_a[4]))); break;
        case 6: _t->signalGetGeneralParamCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< uint(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< uint(*)>(_a[4]))); break;
        case 7: _t->signalIapDownloadCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< uint(*)>(_a[2])),(*reinterpret_cast< uint(*)>(_a[3])),(*reinterpret_cast< unsigned char(*)>(_a[4])),(*reinterpret_cast< uint(*)>(_a[5]))); break;
        case 8: _t->slotTimeout(); break;
        case 9: { int _r = _t->slotBoardOpenPort((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< unsigned short(*)>(_a[2])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 10: { int _r = _t->slotBoardClosePort((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< unsigned short(*)>(_a[2])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 11: { int _r = _t->slotBoardIsDeviceOpened((*reinterpret_cast< unsigned char(*)>(_a[1])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 12: { int _r = _t->slotBoardGetVerInfo((*reinterpret_cast< uint(*)>(_a[1])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 13: { int _r = _t->slotBoardSetPwmParams((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< unsigned char(*)>(_a[4])),(*reinterpret_cast< unsigned char(*)>(_a[5])),(*reinterpret_cast< unsigned char(*)>(_a[6])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 14: { int _r = _t->slotBoardGetPwmParams((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 15: { int _r = _t->slotSetGeneralParam((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< uint(*)>(_a[4])),(*reinterpret_cast< unsigned char(*)>(_a[5])),(*reinterpret_cast< uint(*)>(_a[6])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 16: { int _r = _t->slotGetGeneralParam((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< uint(*)>(_a[4])),(*reinterpret_cast< unsigned char(*)>(_a[5])),(*reinterpret_cast< uint(*)>(_a[6])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 17: { int _r = _t->slotIapDownload((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< QString(*)>(_a[2])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        default: ;
        }
    } else if (_c == QMetaObject::IndexOfMethod) {
        int *result = reinterpret_cast<int *>(_a[0]);
        {
            using _t = void (CDioLcAdapter::*)(unsigned short , unsigned char , unsigned char , unsigned char , unsigned char , unsigned char , unsigned char , unsigned char , unsigned int );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&CDioLcAdapter::signalComOpenCB)) {
                *result = 0;
                return;
            }
        }
        {
            using _t = void (CDioLcAdapter::*)(unsigned char , unsigned int );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&CDioLcAdapter::signalComCloseCB)) {
                *result = 1;
                return;
            }
        }
        {
            using _t = void (CDioLcAdapter::*)(unsigned char , unsigned char , unsigned char , unsigned char , unsigned char , unsigned char , unsigned char , unsigned int );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&CDioLcAdapter::signalGetDeviceVerCB)) {
                *result = 2;
                return;
            }
        }
        {
            using _t = void (CDioLcAdapter::*)(unsigned char , unsigned char , unsigned int );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&CDioLcAdapter::signalSetPwmParamsCB)) {
                *result = 3;
                return;
            }
        }
        {
            using _t = void (CDioLcAdapter::*)(unsigned char , unsigned char , unsigned char , unsigned char , unsigned char , unsigned char , unsigned int );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&CDioLcAdapter::signalGetPwmParamsCB)) {
                *result = 4;
                return;
            }
        }
        {
            using _t = void (CDioLcAdapter::*)(unsigned char , unsigned int , unsigned char , unsigned int );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&CDioLcAdapter::signalSetGeneralParamCB)) {
                *result = 5;
                return;
            }
        }
        {
            using _t = void (CDioLcAdapter::*)(unsigned char , unsigned int , unsigned char , unsigned int );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&CDioLcAdapter::signalGetGeneralParamCB)) {
                *result = 6;
                return;
            }
        }
        {
            using _t = void (CDioLcAdapter::*)(unsigned char , unsigned int , unsigned int , unsigned char , unsigned int );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&CDioLcAdapter::signalIapDownloadCB)) {
                *result = 7;
                return;
            }
        }
    }
}

QT_INIT_METAOBJECT const QMetaObject CDioLcAdapter::staticMetaObject = { {
    &QThread::staticMetaObject,
    qt_meta_stringdata_CDioLcAdapter.data,
    qt_meta_data_CDioLcAdapter,
    qt_static_metacall,
    nullptr,
    nullptr
} };


const QMetaObject *CDioLcAdapter::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *CDioLcAdapter::qt_metacast(const char *_clname)
{
    if (!_clname) return nullptr;
    if (!strcmp(_clname, qt_meta_stringdata_CDioLcAdapter.stringdata0))
        return static_cast<void*>(this);
    return QThread::qt_metacast(_clname);
}

int CDioLcAdapter::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QThread::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 18)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 18;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 18)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 18;
    }
    return _id;
}

// SIGNAL 0
void CDioLcAdapter::signalComOpenCB(unsigned short _t1, unsigned char _t2, unsigned char _t3, unsigned char _t4, unsigned char _t5, unsigned char _t6, unsigned char _t7, unsigned char _t8, unsigned int _t9)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t3))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t4))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t5))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t6))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t7))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t8))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t9))) };
    QMetaObject::activate(this, &staticMetaObject, 0, _a);
}

// SIGNAL 1
void CDioLcAdapter::signalComCloseCB(unsigned char _t1, unsigned int _t2)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))) };
    QMetaObject::activate(this, &staticMetaObject, 1, _a);
}

// SIGNAL 2
void CDioLcAdapter::signalGetDeviceVerCB(unsigned char _t1, unsigned char _t2, unsigned char _t3, unsigned char _t4, unsigned char _t5, unsigned char _t6, unsigned char _t7, unsigned int _t8)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t3))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t4))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t5))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t6))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t7))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t8))) };
    QMetaObject::activate(this, &staticMetaObject, 2, _a);
}

// SIGNAL 3
void CDioLcAdapter::signalSetPwmParamsCB(unsigned char _t1, unsigned char _t2, unsigned int _t3)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t3))) };
    QMetaObject::activate(this, &staticMetaObject, 3, _a);
}

// SIGNAL 4
void CDioLcAdapter::signalGetPwmParamsCB(unsigned char _t1, unsigned char _t2, unsigned char _t3, unsigned char _t4, unsigned char _t5, unsigned char _t6, unsigned int _t7)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t3))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t4))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t5))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t6))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t7))) };
    QMetaObject::activate(this, &staticMetaObject, 4, _a);
}

// SIGNAL 5
void CDioLcAdapter::signalSetGeneralParamCB(unsigned char _t1, unsigned int _t2, unsigned char _t3, unsigned int _t4)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t3))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t4))) };
    QMetaObject::activate(this, &staticMetaObject, 5, _a);
}

// SIGNAL 6
void CDioLcAdapter::signalGetGeneralParamCB(unsigned char _t1, unsigned int _t2, unsigned char _t3, unsigned int _t4)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t3))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t4))) };
    QMetaObject::activate(this, &staticMetaObject, 6, _a);
}

// SIGNAL 7
void CDioLcAdapter::signalIapDownloadCB(unsigned char _t1, unsigned int _t2, unsigned int _t3, unsigned char _t4, unsigned int _t5)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t3))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t4))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t5))) };
    QMetaObject::activate(this, &staticMetaObject, 7, _a);
}
QT_WARNING_POP
QT_END_MOC_NAMESPACE
