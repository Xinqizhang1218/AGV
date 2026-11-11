/****************************************************************************
** Meta object code from reading C++ file 'lightControlPage.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.13.2)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include <memory>
#include "../NK_IO_LC_LIB_TEST_Qt/lightControlPage.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'lightControlPage.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.13.2. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
struct qt_meta_stringdata_lightControlPage_t {
    QByteArrayData data[78];
    char stringdata0[1332];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    qptrdiff(offsetof(qt_meta_stringdata_lightControlPage_t, stringdata0) + ofs \
        - idx * sizeof(QByteArrayData)) \
    )
static const qt_meta_stringdata_lightControlPage_t qt_meta_stringdata_lightControlPage = {
    {
QT_MOC_LITERAL(0, 0, 16), // "lightControlPage"
QT_MOC_LITERAL(1, 17, 19), // "signalBoardOpenPort"
QT_MOC_LITERAL(2, 37, 0), // ""
QT_MOC_LITERAL(3, 38, 5), // "devId"
QT_MOC_LITERAL(4, 44, 4), // "port"
QT_MOC_LITERAL(5, 49, 20), // "signalBoardClosePort"
QT_MOC_LITERAL(6, 70, 25), // "signalBoardIsDeviceOpened"
QT_MOC_LITERAL(7, 96, 21), // "signalBoardGetVerInfo"
QT_MOC_LITERAL(8, 118, 23), // "signalBoardSetPwmParams"
QT_MOC_LITERAL(9, 142, 7), // "ucChIdx"
QT_MOC_LITERAL(10, 150, 9), // "ucPwmMode"
QT_MOC_LITERAL(11, 160, 10), // "ucPwmValue"
QT_MOC_LITERAL(12, 171, 16), // "ucPwmHoldingTime"
QT_MOC_LITERAL(13, 188, 10), // "ucPwmOnOff"
QT_MOC_LITERAL(14, 199, 23), // "signalBoardGetPwmParams"
QT_MOC_LITERAL(15, 223, 21), // "signalSetGeneralParam"
QT_MOC_LITERAL(16, 245, 9), // "ucParamId"
QT_MOC_LITERAL(17, 255, 10), // "ucParamLen"
QT_MOC_LITERAL(18, 266, 10), // "paramValue"
QT_MOC_LITERAL(19, 277, 7), // "ucError"
QT_MOC_LITERAL(20, 285, 9), // "uiErrorId"
QT_MOC_LITERAL(21, 295, 21), // "signalGetGeneralParam"
QT_MOC_LITERAL(22, 317, 17), // "signalIapDownload"
QT_MOC_LITERAL(23, 335, 9), // "imageFile"
QT_MOC_LITERAL(24, 345, 13), // "slotOnConnect"
QT_MOC_LITERAL(25, 359, 18), // "slotOnReadParamCh0"
QT_MOC_LITERAL(26, 378, 19), // "slotOnWriteParamCh0"
QT_MOC_LITERAL(27, 398, 15), // "slotOnTurnOnCh0"
QT_MOC_LITERAL(28, 414, 5), // "onoff"
QT_MOC_LITERAL(29, 420, 25), // "slotOnWriteParamOnlineCh0"
QT_MOC_LITERAL(30, 446, 5), // "value"
QT_MOC_LITERAL(31, 452, 18), // "slotOnReadParamCh1"
QT_MOC_LITERAL(32, 471, 19), // "slotOnWriteParamCh1"
QT_MOC_LITERAL(33, 491, 15), // "slotOnTurnOnCh1"
QT_MOC_LITERAL(34, 507, 25), // "slotOnWriteParamOnlineCh1"
QT_MOC_LITERAL(35, 533, 18), // "slotOnReadParamCh2"
QT_MOC_LITERAL(36, 552, 19), // "slotOnWriteParamCh2"
QT_MOC_LITERAL(37, 572, 15), // "slotOnTurnOnCh2"
QT_MOC_LITERAL(38, 588, 25), // "slotOnWriteParamOnlineCh2"
QT_MOC_LITERAL(39, 614, 18), // "slotOnReadParamCh3"
QT_MOC_LITERAL(40, 633, 19), // "slotOnWriteParamCh3"
QT_MOC_LITERAL(41, 653, 15), // "slotOnTurnOnCh3"
QT_MOC_LITERAL(42, 669, 25), // "slotOnWriteParamOnlineCh3"
QT_MOC_LITERAL(43, 695, 21), // "slotOnReadCh0Advanced"
QT_MOC_LITERAL(44, 717, 21), // "slotOnReadCh1Advanced"
QT_MOC_LITERAL(45, 739, 21), // "slotOnReadCh2Advanced"
QT_MOC_LITERAL(46, 761, 21), // "slotOnReadCh3Advanced"
QT_MOC_LITERAL(47, 783, 22), // "slotOnWriteCh0Advanced"
QT_MOC_LITERAL(48, 806, 22), // "slotOnWriteCh1Advanced"
QT_MOC_LITERAL(49, 829, 22), // "slotOnWriteCh2Advanced"
QT_MOC_LITERAL(50, 852, 22), // "slotOnWriteCh3Advanced"
QT_MOC_LITERAL(51, 875, 13), // "slotComOpenCB"
QT_MOC_LITERAL(52, 889, 7), // "portNum"
QT_MOC_LITERAL(53, 897, 16), // "hardwareMajorVer"
QT_MOC_LITERAL(54, 914, 16), // "hardwareMinorVer"
QT_MOC_LITERAL(55, 931, 14), // "hardwareRevVer"
QT_MOC_LITERAL(56, 946, 16), // "firmwareMajorVer"
QT_MOC_LITERAL(57, 963, 16), // "firmwareMinorVer"
QT_MOC_LITERAL(58, 980, 14), // "firmwareRevVer"
QT_MOC_LITERAL(59, 995, 14), // "slotComCloseCB"
QT_MOC_LITERAL(60, 1010, 18), // "slotGetDeviceVerCB"
QT_MOC_LITERAL(61, 1029, 18), // "ucHardwareMajorVer"
QT_MOC_LITERAL(62, 1048, 18), // "ucHardwareMinorVer"
QT_MOC_LITERAL(63, 1067, 16), // "ucHardwareRevVer"
QT_MOC_LITERAL(64, 1084, 18), // "ucFirmwareMajorVer"
QT_MOC_LITERAL(65, 1103, 18), // "ucFirmwareMinorVer"
QT_MOC_LITERAL(66, 1122, 16), // "ucFirmwareRevVer"
QT_MOC_LITERAL(67, 1139, 18), // "slotSetPwmParamsCB"
QT_MOC_LITERAL(68, 1158, 18), // "slotGetPwmParamsCB"
QT_MOC_LITERAL(69, 1177, 21), // "slotSetGeneralParamCB"
QT_MOC_LITERAL(70, 1199, 7), // "paramId"
QT_MOC_LITERAL(71, 1207, 21), // "slotGetGeneralParamCB"
QT_MOC_LITERAL(72, 1229, 17), // "slotOpenImageFile"
QT_MOC_LITERAL(73, 1247, 21), // "slotDownloadImageFile"
QT_MOC_LITERAL(74, 1269, 17), // "slotIapDownloadCB"
QT_MOC_LITERAL(75, 1287, 7), // "ucDevId"
QT_MOC_LITERAL(76, 1295, 15), // "uiFileTotalSize"
QT_MOC_LITERAL(77, 1311, 20) // "uiFileSizeDownloaded"

    },
    "lightControlPage\0signalBoardOpenPort\0"
    "\0devId\0port\0signalBoardClosePort\0"
    "signalBoardIsDeviceOpened\0"
    "signalBoardGetVerInfo\0signalBoardSetPwmParams\0"
    "ucChIdx\0ucPwmMode\0ucPwmValue\0"
    "ucPwmHoldingTime\0ucPwmOnOff\0"
    "signalBoardGetPwmParams\0signalSetGeneralParam\0"
    "ucParamId\0ucParamLen\0paramValue\0ucError\0"
    "uiErrorId\0signalGetGeneralParam\0"
    "signalIapDownload\0imageFile\0slotOnConnect\0"
    "slotOnReadParamCh0\0slotOnWriteParamCh0\0"
    "slotOnTurnOnCh0\0onoff\0slotOnWriteParamOnlineCh0\0"
    "value\0slotOnReadParamCh1\0slotOnWriteParamCh1\0"
    "slotOnTurnOnCh1\0slotOnWriteParamOnlineCh1\0"
    "slotOnReadParamCh2\0slotOnWriteParamCh2\0"
    "slotOnTurnOnCh2\0slotOnWriteParamOnlineCh2\0"
    "slotOnReadParamCh3\0slotOnWriteParamCh3\0"
    "slotOnTurnOnCh3\0slotOnWriteParamOnlineCh3\0"
    "slotOnReadCh0Advanced\0slotOnReadCh1Advanced\0"
    "slotOnReadCh2Advanced\0slotOnReadCh3Advanced\0"
    "slotOnWriteCh0Advanced\0slotOnWriteCh1Advanced\0"
    "slotOnWriteCh2Advanced\0slotOnWriteCh3Advanced\0"
    "slotComOpenCB\0portNum\0hardwareMajorVer\0"
    "hardwareMinorVer\0hardwareRevVer\0"
    "firmwareMajorVer\0firmwareMinorVer\0"
    "firmwareRevVer\0slotComCloseCB\0"
    "slotGetDeviceVerCB\0ucHardwareMajorVer\0"
    "ucHardwareMinorVer\0ucHardwareRevVer\0"
    "ucFirmwareMajorVer\0ucFirmwareMinorVer\0"
    "ucFirmwareRevVer\0slotSetPwmParamsCB\0"
    "slotGetPwmParamsCB\0slotSetGeneralParamCB\0"
    "paramId\0slotGetGeneralParamCB\0"
    "slotOpenImageFile\0slotDownloadImageFile\0"
    "slotIapDownloadCB\0ucDevId\0uiFileTotalSize\0"
    "uiFileSizeDownloaded"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_lightControlPage[] = {

 // content:
       8,       // revision
       0,       // classname
       0,    0, // classinfo
      44,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       9,       // signalCount

 // signals: name, argc, parameters, tag, flags
       1,    2,  234,    2, 0x06 /* Public */,
       5,    2,  239,    2, 0x06 /* Public */,
       6,    1,  244,    2, 0x06 /* Public */,
       7,    1,  247,    2, 0x06 /* Public */,
       8,    6,  250,    2, 0x06 /* Public */,
      14,    2,  263,    2, 0x06 /* Public */,
      15,    6,  268,    2, 0x06 /* Public */,
      21,    6,  281,    2, 0x06 /* Public */,
      22,    2,  294,    2, 0x06 /* Public */,

 // slots: name, argc, parameters, tag, flags
      24,    0,  299,    2, 0x09 /* Protected */,
      25,    0,  300,    2, 0x09 /* Protected */,
      26,    0,  301,    2, 0x09 /* Protected */,
      27,    1,  302,    2, 0x09 /* Protected */,
      29,    1,  305,    2, 0x09 /* Protected */,
      31,    0,  308,    2, 0x09 /* Protected */,
      32,    0,  309,    2, 0x09 /* Protected */,
      33,    1,  310,    2, 0x09 /* Protected */,
      34,    1,  313,    2, 0x09 /* Protected */,
      35,    0,  316,    2, 0x09 /* Protected */,
      36,    0,  317,    2, 0x09 /* Protected */,
      37,    1,  318,    2, 0x09 /* Protected */,
      38,    1,  321,    2, 0x09 /* Protected */,
      39,    0,  324,    2, 0x09 /* Protected */,
      40,    0,  325,    2, 0x09 /* Protected */,
      41,    1,  326,    2, 0x09 /* Protected */,
      42,    1,  329,    2, 0x09 /* Protected */,
      43,    0,  332,    2, 0x09 /* Protected */,
      44,    0,  333,    2, 0x09 /* Protected */,
      45,    0,  334,    2, 0x09 /* Protected */,
      46,    0,  335,    2, 0x09 /* Protected */,
      47,    0,  336,    2, 0x09 /* Protected */,
      48,    0,  337,    2, 0x09 /* Protected */,
      49,    0,  338,    2, 0x09 /* Protected */,
      50,    0,  339,    2, 0x09 /* Protected */,
      51,    9,  340,    2, 0x09 /* Protected */,
      59,    2,  359,    2, 0x09 /* Protected */,
      60,    8,  364,    2, 0x09 /* Protected */,
      67,    3,  381,    2, 0x09 /* Protected */,
      68,    7,  388,    2, 0x09 /* Protected */,
      69,    4,  403,    2, 0x09 /* Protected */,
      71,    4,  412,    2, 0x09 /* Protected */,
      72,    0,  421,    2, 0x09 /* Protected */,
      73,    0,  422,    2, 0x09 /* Protected */,
      74,    5,  423,    2, 0x09 /* Protected */,

 // signals: parameters
    QMetaType::Int, QMetaType::UInt, QMetaType::UShort,    3,    4,
    QMetaType::Int, QMetaType::UInt, QMetaType::UShort,    3,    4,
    QMetaType::Int, QMetaType::UChar,    3,
    QMetaType::Int, QMetaType::UInt,    3,
    QMetaType::Int, QMetaType::UInt, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar,    3,    9,   10,   11,   12,   13,
    QMetaType::Int, QMetaType::UInt, QMetaType::UChar,    3,    9,
    QMetaType::Int, QMetaType::UInt, QMetaType::UChar, QMetaType::UChar, QMetaType::UInt, QMetaType::UChar, QMetaType::UInt,    3,   16,   17,   18,   19,   20,
    QMetaType::Int, QMetaType::UInt, QMetaType::UChar, QMetaType::UChar, QMetaType::UInt, QMetaType::UChar, QMetaType::UInt,    3,   16,   17,   18,   19,   20,
    QMetaType::Int, QMetaType::UInt, QMetaType::QString,    3,   23,

 // slots: parameters
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::Bool,   28,
    QMetaType::Void, QMetaType::Int,   30,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::Bool,   28,
    QMetaType::Void, QMetaType::Int,   30,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::Bool,   28,
    QMetaType::Void, QMetaType::Int,   30,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::Bool,   28,
    QMetaType::Void, QMetaType::Int,   30,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::UShort, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UInt,   52,   53,   54,   55,   56,   57,   58,   19,   20,
    QMetaType::Void, QMetaType::UChar, QMetaType::UInt,   19,   20,
    QMetaType::Void, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UInt,   61,   62,   63,   64,   65,   66,   19,   20,
    QMetaType::Void, QMetaType::UChar, QMetaType::UChar, QMetaType::UInt,    9,   19,   20,
    QMetaType::Void, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UChar, QMetaType::UInt,    9,   10,   11,   12,   13,   19,   20,
    QMetaType::Void, QMetaType::UChar, QMetaType::UInt, QMetaType::UChar, QMetaType::UInt,   70,   18,   19,   20,
    QMetaType::Void, QMetaType::UChar, QMetaType::UInt, QMetaType::UChar, QMetaType::UInt,   70,   18,   19,   20,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::UChar, QMetaType::UInt, QMetaType::UInt, QMetaType::UChar, QMetaType::UInt,   75,   76,   77,   19,   20,

       0        // eod
};

void lightControlPage::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        auto *_t = static_cast<lightControlPage *>(_o);
        Q_UNUSED(_t)
        switch (_id) {
        case 0: { int _r = _t->signalBoardOpenPort((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< unsigned short(*)>(_a[2])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 1: { int _r = _t->signalBoardClosePort((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< unsigned short(*)>(_a[2])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 2: { int _r = _t->signalBoardIsDeviceOpened((*reinterpret_cast< unsigned char(*)>(_a[1])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 3: { int _r = _t->signalBoardGetVerInfo((*reinterpret_cast< uint(*)>(_a[1])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 4: { int _r = _t->signalBoardSetPwmParams((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< unsigned char(*)>(_a[4])),(*reinterpret_cast< unsigned char(*)>(_a[5])),(*reinterpret_cast< unsigned char(*)>(_a[6])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 5: { int _r = _t->signalBoardGetPwmParams((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 6: { int _r = _t->signalSetGeneralParam((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< uint(*)>(_a[4])),(*reinterpret_cast< unsigned char(*)>(_a[5])),(*reinterpret_cast< uint(*)>(_a[6])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 7: { int _r = _t->signalGetGeneralParam((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< uint(*)>(_a[4])),(*reinterpret_cast< unsigned char(*)>(_a[5])),(*reinterpret_cast< uint(*)>(_a[6])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 8: { int _r = _t->signalIapDownload((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< QString(*)>(_a[2])));
            if (_a[0]) *reinterpret_cast< int*>(_a[0]) = std::move(_r); }  break;
        case 9: _t->slotOnConnect(); break;
        case 10: _t->slotOnReadParamCh0(); break;
        case 11: _t->slotOnWriteParamCh0(); break;
        case 12: _t->slotOnTurnOnCh0((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 13: _t->slotOnWriteParamOnlineCh0((*reinterpret_cast< int(*)>(_a[1]))); break;
        case 14: _t->slotOnReadParamCh1(); break;
        case 15: _t->slotOnWriteParamCh1(); break;
        case 16: _t->slotOnTurnOnCh1((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 17: _t->slotOnWriteParamOnlineCh1((*reinterpret_cast< int(*)>(_a[1]))); break;
        case 18: _t->slotOnReadParamCh2(); break;
        case 19: _t->slotOnWriteParamCh2(); break;
        case 20: _t->slotOnTurnOnCh2((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 21: _t->slotOnWriteParamOnlineCh2((*reinterpret_cast< int(*)>(_a[1]))); break;
        case 22: _t->slotOnReadParamCh3(); break;
        case 23: _t->slotOnWriteParamCh3(); break;
        case 24: _t->slotOnTurnOnCh3((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 25: _t->slotOnWriteParamOnlineCh3((*reinterpret_cast< int(*)>(_a[1]))); break;
        case 26: _t->slotOnReadCh0Advanced(); break;
        case 27: _t->slotOnReadCh1Advanced(); break;
        case 28: _t->slotOnReadCh2Advanced(); break;
        case 29: _t->slotOnReadCh3Advanced(); break;
        case 30: _t->slotOnWriteCh0Advanced(); break;
        case 31: _t->slotOnWriteCh1Advanced(); break;
        case 32: _t->slotOnWriteCh2Advanced(); break;
        case 33: _t->slotOnWriteCh3Advanced(); break;
        case 34: _t->slotComOpenCB((*reinterpret_cast< unsigned short(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< unsigned char(*)>(_a[4])),(*reinterpret_cast< unsigned char(*)>(_a[5])),(*reinterpret_cast< unsigned char(*)>(_a[6])),(*reinterpret_cast< unsigned char(*)>(_a[7])),(*reinterpret_cast< unsigned char(*)>(_a[8])),(*reinterpret_cast< uint(*)>(_a[9]))); break;
        case 35: _t->slotComCloseCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< uint(*)>(_a[2]))); break;
        case 36: _t->slotGetDeviceVerCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< unsigned char(*)>(_a[4])),(*reinterpret_cast< unsigned char(*)>(_a[5])),(*reinterpret_cast< unsigned char(*)>(_a[6])),(*reinterpret_cast< unsigned char(*)>(_a[7])),(*reinterpret_cast< uint(*)>(_a[8]))); break;
        case 37: _t->slotSetPwmParamsCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< uint(*)>(_a[3]))); break;
        case 38: _t->slotGetPwmParamsCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< unsigned char(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< unsigned char(*)>(_a[4])),(*reinterpret_cast< unsigned char(*)>(_a[5])),(*reinterpret_cast< unsigned char(*)>(_a[6])),(*reinterpret_cast< uint(*)>(_a[7]))); break;
        case 39: _t->slotSetGeneralParamCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< uint(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< uint(*)>(_a[4]))); break;
        case 40: _t->slotGetGeneralParamCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< uint(*)>(_a[2])),(*reinterpret_cast< unsigned char(*)>(_a[3])),(*reinterpret_cast< uint(*)>(_a[4]))); break;
        case 41: _t->slotOpenImageFile(); break;
        case 42: _t->slotDownloadImageFile(); break;
        case 43: _t->slotIapDownloadCB((*reinterpret_cast< unsigned char(*)>(_a[1])),(*reinterpret_cast< uint(*)>(_a[2])),(*reinterpret_cast< uint(*)>(_a[3])),(*reinterpret_cast< unsigned char(*)>(_a[4])),(*reinterpret_cast< uint(*)>(_a[5]))); break;
        default: ;
        }
    } else if (_c == QMetaObject::IndexOfMethod) {
        int *result = reinterpret_cast<int *>(_a[0]);
        {
            using _t = int (lightControlPage::*)(unsigned int , unsigned short );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&lightControlPage::signalBoardOpenPort)) {
                *result = 0;
                return;
            }
        }
        {
            using _t = int (lightControlPage::*)(unsigned int , unsigned short );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&lightControlPage::signalBoardClosePort)) {
                *result = 1;
                return;
            }
        }
        {
            using _t = int (lightControlPage::*)(unsigned char );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&lightControlPage::signalBoardIsDeviceOpened)) {
                *result = 2;
                return;
            }
        }
        {
            using _t = int (lightControlPage::*)(unsigned int );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&lightControlPage::signalBoardGetVerInfo)) {
                *result = 3;
                return;
            }
        }
        {
            using _t = int (lightControlPage::*)(unsigned int , unsigned char , unsigned char , unsigned char , unsigned char , unsigned char );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&lightControlPage::signalBoardSetPwmParams)) {
                *result = 4;
                return;
            }
        }
        {
            using _t = int (lightControlPage::*)(unsigned int , unsigned char );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&lightControlPage::signalBoardGetPwmParams)) {
                *result = 5;
                return;
            }
        }
        {
            using _t = int (lightControlPage::*)(unsigned int , unsigned char , unsigned char , unsigned int , unsigned char , unsigned int );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&lightControlPage::signalSetGeneralParam)) {
                *result = 6;
                return;
            }
        }
        {
            using _t = int (lightControlPage::*)(unsigned int , unsigned char , unsigned char , unsigned int , unsigned char , unsigned int );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&lightControlPage::signalGetGeneralParam)) {
                *result = 7;
                return;
            }
        }
        {
            using _t = int (lightControlPage::*)(unsigned int , QString );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&lightControlPage::signalIapDownload)) {
                *result = 8;
                return;
            }
        }
    }
}

QT_INIT_METAOBJECT const QMetaObject lightControlPage::staticMetaObject = { {
    &QWidget::staticMetaObject,
    qt_meta_stringdata_lightControlPage.data,
    qt_meta_data_lightControlPage,
    qt_static_metacall,
    nullptr,
    nullptr
} };


const QMetaObject *lightControlPage::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *lightControlPage::qt_metacast(const char *_clname)
{
    if (!_clname) return nullptr;
    if (!strcmp(_clname, qt_meta_stringdata_lightControlPage.stringdata0))
        return static_cast<void*>(this);
    return QWidget::qt_metacast(_clname);
}

int lightControlPage::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QWidget::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 44)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 44;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 44)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 44;
    }
    return _id;
}

// SIGNAL 0
int lightControlPage::signalBoardOpenPort(unsigned int _t1, unsigned short _t2)
{
    int _t0{};
    void *_a[] = { const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t0))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))) };
    QMetaObject::activate(this, &staticMetaObject, 0, _a);
    return _t0;
}

// SIGNAL 1
int lightControlPage::signalBoardClosePort(unsigned int _t1, unsigned short _t2)
{
    int _t0{};
    void *_a[] = { const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t0))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))) };
    QMetaObject::activate(this, &staticMetaObject, 1, _a);
    return _t0;
}

// SIGNAL 2
int lightControlPage::signalBoardIsDeviceOpened(unsigned char _t1)
{
    int _t0{};
    void *_a[] = { const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t0))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))) };
    QMetaObject::activate(this, &staticMetaObject, 2, _a);
    return _t0;
}

// SIGNAL 3
int lightControlPage::signalBoardGetVerInfo(unsigned int _t1)
{
    int _t0{};
    void *_a[] = { const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t0))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))) };
    QMetaObject::activate(this, &staticMetaObject, 3, _a);
    return _t0;
}

// SIGNAL 4
int lightControlPage::signalBoardSetPwmParams(unsigned int _t1, unsigned char _t2, unsigned char _t3, unsigned char _t4, unsigned char _t5, unsigned char _t6)
{
    int _t0{};
    void *_a[] = { const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t0))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t3))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t4))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t5))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t6))) };
    QMetaObject::activate(this, &staticMetaObject, 4, _a);
    return _t0;
}

// SIGNAL 5
int lightControlPage::signalBoardGetPwmParams(unsigned int _t1, unsigned char _t2)
{
    int _t0{};
    void *_a[] = { const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t0))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))) };
    QMetaObject::activate(this, &staticMetaObject, 5, _a);
    return _t0;
}

// SIGNAL 6
int lightControlPage::signalSetGeneralParam(unsigned int _t1, unsigned char _t2, unsigned char _t3, unsigned int _t4, unsigned char _t5, unsigned int _t6)
{
    int _t0{};
    void *_a[] = { const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t0))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t3))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t4))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t5))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t6))) };
    QMetaObject::activate(this, &staticMetaObject, 6, _a);
    return _t0;
}

// SIGNAL 7
int lightControlPage::signalGetGeneralParam(unsigned int _t1, unsigned char _t2, unsigned char _t3, unsigned int _t4, unsigned char _t5, unsigned int _t6)
{
    int _t0{};
    void *_a[] = { const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t0))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t3))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t4))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t5))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t6))) };
    QMetaObject::activate(this, &staticMetaObject, 7, _a);
    return _t0;
}

// SIGNAL 8
int lightControlPage::signalIapDownload(unsigned int _t1, QString _t2)
{
    int _t0{};
    void *_a[] = { const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t0))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))), const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t2))) };
    QMetaObject::activate(this, &staticMetaObject, 8, _a);
    return _t0;
}
QT_WARNING_POP
QT_END_MOC_NAMESPACE
