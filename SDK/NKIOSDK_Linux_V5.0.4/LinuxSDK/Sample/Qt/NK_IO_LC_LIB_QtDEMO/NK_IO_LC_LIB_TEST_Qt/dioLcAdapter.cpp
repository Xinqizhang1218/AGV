#include "qmessagebox.h"
#include "qcoreapplication.h"
#include "qsettings.h"
#include "sys/io.h"
#include "dioLcAdapter.h"


CDioLcAdapter *CDioLcAdapter::pThis = NULL;

CDioLcAdapter::CDioLcAdapter(QObject *parent) :QThread(parent)
{
    //m_bLoaded = -1;
    pThis = this;
    m_bLcEnabled = false;
    m_bAioEnabled = false;

    pvInit();

    m_xtimer = new QTimer(this);
    connect(m_xtimer, SIGNAL(timeout()), this, SLOT(slotTimeout()));
    m_xtimer->setInterval(40);
    m_xtimer->start();

}
CDioLcAdapter::~CDioLcAdapter()
{

}

void CDioLcAdapter::slotTimeout()
{

    if (m_bLcEnabled)
    {
        m_DIOLC_Process();
    }
}


// slot to open the device port, for the H1, the default serial port is 3
// return the version information in the callback if connected to the MCU successfully
int CDioLcAdapter::slotBoardOpenPort(unsigned int devId, unsigned short port)
{
    return m_DIOLC_OpenDevice(port, this->ComOpenCB);
}
// slot to close the device port
int CDioLcAdapter::slotBoardClosePort(unsigned int devId, unsigned short port)
{
    return m_DIOLC_CloseDevice(port, this->ComCloseCB);
}
// slot to check if the port has been opened or not, return 1 when has been opened, otherwize return 0;
int CDioLcAdapter::slotBoardIsDeviceOpened(unsigned char devId)
{
    return m_DIOLC_IsDeviceOpened(3, devId);
}

// slot to read the hardware version and firmware information 
int CDioLcAdapter::slotBoardGetVerInfo(unsigned int devId)
{
    return m_LC_GetVerInfo(devId, this->GetDeviceVerCB);
}

// slot to set the light control parameters to the specified channel
int CDioLcAdapter::slotBoardSetPwmParams(unsigned int devId,
                                         unsigned char ucChIdx,
                                         unsigned char ucPwmMode,
                                         unsigned char ucPwmValue,
                                         unsigned char ucPwmHoldingTime,
                                         unsigned char ucPwmOnOff)
{
    return m_LC_SetPwmParams(devId, ucChIdx, ucPwmMode, ucPwmValue, ucPwmHoldingTime, ucPwmOnOff, SetPwmParamsCB);
}

// slot to read the light control parameters from the according channel.
int CDioLcAdapter::slotBoardGetPwmParams(unsigned int devId, unsigned char ucChIdx)
{
    return m_LC_GetPwmParams(devId, ucChIdx, GetPwmParamsCB);
}


// for the general parameters settings and gettings
int CDioLcAdapter::slotSetGeneralParam(unsigned int devId, unsigned char ucParamId, unsigned char ucParamLen, unsigned int paramValue, unsigned char ucError, unsigned int uiErrorId )
{
    return m_DIOLC_SetParam(devId,ucParamId,ucParamLen,paramValue,SetGeneralParamCB);
    //return 0;

}
int CDioLcAdapter::slotGetGeneralParam(unsigned int devId, unsigned char ucParamId, unsigned char ucParamLen, unsigned int paramValue, unsigned char ucError, unsigned int uiErrorId )
{
    return m_DIOLC_GetParam(devId,ucParamId,ucParamLen,GetGeneralParamCB);
    //return 0;

}

int CDioLcAdapter::slotIapDownload(unsigned int devId, QString imageFile)
{
    std::string str = imageFile.toStdString();
    QByteArray ba = imageFile.toLocal8Bit();
    char *ch = ba.data();
    return m_LC_IAPDownload(devId,ch,IapDownloadCB);
}


// the cycle thread to do the process work
void CDioLcAdapter::run()
{

}


// load dynamic library and initialized the API address
int CDioLcAdapter::pvInit()
{

    QSettings set(QCoreApplication::applicationDirPath() + "/select.ini", QSettings::IniFormat);
    QString filePath = QCoreApplication::applicationDirPath() + set.value("/SELECTED/ConfigPath").toString();
    //QString filePath = "./nkio_config.ini";
    QSettings configSet(filePath, QSettings::IniFormat);
    m_bLcEnabled = configSet.value("/NKLC/Enabled").toBool();
    m_port = configSet.value("/NKLC/PortNum").toUInt();
    m_bDioNum = configSet.value("/NKDIO/DeviceNum").toUInt();
    //filePath.replace(QString("/"), QString("\\"));
    QByteArray ba = filePath.toLocal8Bit();
    char *ch = ba.data();
    //workThread->init(ch);

    int ret = -1;

    // DIO functions
    //DIO_Init = (DIO_Init_t)GetProcAddress(hDIO,"DIO_Init");
    /*-Polling Mode API------------------------------------------------------------------------------*/
    m_DIO_LibraryBaseInit = NKDIO_LibraryInit;
    m_DIO_LibraryBaseDeinit = NKDIO_LibraryDeinit;
    // m_DIO_PollingReadDiBit = DIO_PollingReadDiBit;
    m_DIO_PollingReadDiByte = NKDIO_PollingReadDiByte;
    m_DIO_PollingReadDiWord = NKDIO_PollingReadDiWord;
    // m_DIO_PollingWriteDoBit = DIO_PollingWriteDoBit;
    m_DIO_PollingWriteDoByte = NKDIO_PollingWriteDoByte;
    m_DIO_PollingWriteDoWord = NKDIO_PollingWriteDoWord;

    m_LC_LibraryBaseInit = NKLC_LibraryInit;
    m_LC_LibraryBaseDeinit = NKLC_LibraryDeinit;
    m_DIOLC_Process = NKLC_Process_Async;
#if 0
    m_DIOLC_OpenDevice = NKLC_OpenDevice_Async;
    m_DIOLC_CloseDevice = NKLC_CloseDevice_Async;
    m_DIOLC_IsDeviceOpened = NKLC_IsDeviceOpened_Async;
    m_LC_GetVerInfo = NKLC_GetVerInfo_Async;
    m_LC_SetPwmParams = NKLC_SetPwmParams_Async;
    m_LC_GetPwmParams = NKLC_GetPwmParams_Async;
    m_DIOLC_SetParam = NKLC_SetGeneralParam_Async;
    m_DIOLC_GetParam = NKLC_GetGeneralParam_Async;
    m_LC_IAPDownload = NKLC_IAPDownload_Async;
#endif

#if 1
    m_DIOLC_OpenDevice = NKLC_OpenDevice;
    m_DIOLC_CloseDevice = NKLC_CloseDevice;
    m_DIOLC_IsDeviceOpened = NKLC_IsDeviceOpened;
    m_LC_GetVerInfo = NKLC_GetVerInfo;
    m_LC_SetPwmParams = NKLC_SetPwmParams;
    m_LC_GetPwmParams = NKLC_GetPwmParams;
    m_DIOLC_SetParam = NKLC_SetGeneralParam;
    m_DIOLC_GetParam = NKLC_GetGeneralParam;
    m_LC_IAPDownload = NKLC_IAPDownload;
#endif

    if(m_bDioNum >= 1)
    {
        //iopl(3);
        int dio_ret = NKDIO_LibraryInit(ch);
        if (dio_ret == 0)
        {
            ret = dio_ret;
        }
        else
        {
            QMessageBox::warning(0, tr("Warning"),
                                 tr("Load DIO library Failed!") + QString("ret:%1").arg(dio_ret),
                                 QMessageBox::Ok);
            m_bDioNum = 0;
            ret = dio_ret;
        }
    }

    if(m_bLcEnabled)
    {
        int lc_ret = m_LC_LibraryBaseInit(ch);
        if (lc_ret == 0)
        {

            ret = lc_ret;
        }
        else
        {
            QMessageBox::warning(0, tr("Warning"),
                                 tr("Load LightControl library Failed!")+ QString("ret:%1").arg(lc_ret),
                                 QMessageBox::Ok);
            ret = lc_ret;
        }
    }


    return ret;
}

// called when the port opened successfully
void CDioLcAdapter::ComOpenCB(LC_CALLBACK_ARG_T Arg)
{
    emit pThis->signalComOpenCB(Arg.openComCallbackArg.portNum,
                                Arg.openComCallbackArg.hardwareMajorVer,
                                Arg.openComCallbackArg.hardwareMinorVer,
                                Arg.openComCallbackArg.hardwareRevVer,
                                Arg.openComCallbackArg.firmwareMajorVer,
                                Arg.openComCallbackArg.firmwareMinorVer,
                                Arg.openComCallbackArg.firmwareRevVer,
                                Arg.openComCallbackArg.error,
                                Arg.openComCallbackArg.errorId);
}
// called when the port is closed 
void CDioLcAdapter::ComCloseCB(LC_CALLBACK_ARG_T Arg)
{
    emit pThis->signalComCloseCB(Arg.closeComCallbackArg.error, Arg.closeComCallbackArg.errorId);
}

// called when got the version information successfully
void CDioLcAdapter::GetDeviceVerCB(LC_CALLBACK_ARG_T Arg)
{
    emit pThis->signalGetDeviceVerCB(Arg.getDeviceVerCallbackArg.hardwareMajorVer,
                                     Arg.getDeviceVerCallbackArg.hardwareMinorVer,
                                     Arg.getDeviceVerCallbackArg.hardwareRevVer,
                                     Arg.getDeviceVerCallbackArg.firmwareMajorVer,
                                     Arg.getDeviceVerCallbackArg.firmwareMinorVer,
                                     Arg.getDeviceVerCallbackArg.firmwareRevVer,
                                     Arg.getDeviceVerCallbackArg.error,
                                     Arg.getDeviceVerCallbackArg.errorId);
}

// called when set the light control pararmters successfully
void CDioLcAdapter::SetPwmParamsCB(LC_CALLBACK_ARG_T Arg)
{
    emit pThis->signalSetPwmParamsCB(Arg.setPwmParamsCallbackArg.chIdx, Arg.setPwmParamsCallbackArg.error, Arg.setPwmParamsCallbackArg.errorId);
}

// called when read the light control parameters successfully
void CDioLcAdapter::GetPwmParamsCB(LC_CALLBACK_ARG_T Arg)
{
    emit pThis->signalGetPwmParamsCB(Arg.getPwmParamsCallbackArg.chIdx,
                                     Arg.getPwmParamsCallbackArg.pwmMode,
                                     Arg.getPwmParamsCallbackArg.pwmValue,
                                     Arg.getPwmParamsCallbackArg.pwmHoldingTime,
                                     Arg.getPwmParamsCallbackArg.pwmOnOff,
                                     Arg.getPwmParamsCallbackArg.error,
                                     Arg.getPwmParamsCallbackArg.errorId);
}


void CDioLcAdapter::SetGeneralParamCB(LC_CALLBACK_ARG_T Arg)
{
    emit pThis->signalSetGeneralParamCB(Arg.setGeneralParamCallbackArg.paramId,Arg.setGeneralParamCallbackArg.paramValue,Arg.setGeneralParamCallbackArg.error,Arg.setGeneralParamCallbackArg.errorId);
}
void CDioLcAdapter::GetGeneralParamCB(LC_CALLBACK_ARG_T Arg)
{
    emit pThis->signalGetGeneralParamCB(Arg.getGeneralParamCallbackArg.paramId,Arg.getGeneralParamCallbackArg.paramValue,Arg.getGeneralParamCallbackArg.error,Arg.getGeneralParamCallbackArg.errorId);
}


void CDioLcAdapter::IapDownloadCB(LC_CALLBACK_ARG_T Arg)
{
    emit pThis->signalIapDownloadCB(Arg.iapUpdateCallbackArg.devId,
                                    Arg.iapUpdateCallbackArg.totalFileSize,
                                    Arg.iapUpdateCallbackArg.downloadedSize,
                                    Arg.iapUpdateCallbackArg.error,
                                    Arg.iapUpdateCallbackArg.errorId);
}






