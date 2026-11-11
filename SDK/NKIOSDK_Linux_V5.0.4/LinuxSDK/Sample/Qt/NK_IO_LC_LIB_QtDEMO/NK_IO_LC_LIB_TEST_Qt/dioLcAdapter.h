#pragma once
//#include<Windows.h>
#include <qthread.h>
#include <qtimer.h>
#include "NKLCLIB.h"
#include "NKIOLIB.h"

typedef int (*LC_LibraryBaseInit_t)(const char *configFile);
typedef int  (*DIOLC_OpenDevice_t)(unsigned short port, pLcCallbackFunc pCallBackFun);
typedef int  (*DIOLC_CloseDevice_t)(unsigned short port, pLcCallbackFunc pCallBackFun);
typedef int  (*DIOLC_IsDeviceOpened_t)(unsigned short port, unsigned int devId);
typedef int  (*DIOLC_Process_t)(void);
typedef int (*LC_LibraryBaseDeinit_t)();


typedef int(*LC_GetVerInfo_t)(unsigned int devId, pLcCallbackFunc pCallBackFun);

typedef int(*LC_SetPwmParams_t)(unsigned int devId,
	unsigned char ucChIdx,
	unsigned char ucPwmMode,
	unsigned char ucPwmValue,
	unsigned char ucPwmHoldingTime,
	unsigned char ucPwmOnOff,
	pLcCallbackFunc pCallBackFun);

typedef int(*LC_GetPwmParams_t)(unsigned int devId,
	unsigned char ucChIdx,
	pLcCallbackFunc pCallBackFun);


// for the general params settings and gettings
typedef int (*DIOLC_SetParam_t)(unsigned int devId,
    unsigned char ucParamId,
    unsigned char ucParamLen,
    unsigned int uiParamValue,
    pLcCallbackFunc pCallBackFun);

typedef int (*DIOLC_GetParam_t)(unsigned int devId,
    unsigned char ucParamId,
    unsigned char ucParamLen,
    pLcCallbackFunc pCallBackFun);



// DIO Functions

// Read and Write DIO in polling mode
/*-Polling Mode API------------------------------------------------------------------------------*/

typedef int (*DIO_LibraryBaseInit_t)(const char *configFile);
typedef void (*DIO_LibraryBaseDeInit_t)(void);
//typedef BOOL (*DIO_PollingReadDiBit_t)(BYTE diByteIndex, BYTE diBitIndex);
typedef int (*DIO_PollingReadDiByte_t)(unsigned char diByteIndex,unsigned char *pByteValue);
typedef int (*DIO_PollingReadDiWord_t)(unsigned char diWordIndex, unsigned short *pWordValue);
//typedef VOID (*DIO_PollingWriteDoBit_t)(BYTE doByteIndex, BYTE doBitIndex, BYTE doBitValue);
typedef int (*DIO_PollingWriteDoByte_t)(unsigned char doByteIndex, unsigned char doByteValue);
typedef int (*DIO_PollingWriteDoWord_t)(unsigned char doWordIndex, unsigned short doWordValue);


typedef int (*LC_IAPDownload_t)(unsigned int devId,
                                const char *imageFile,
                                pLcCallbackFunc pCallBackFun);


class CDioLcAdapter :
	public QThread
{
	Q_OBJECT
public:
	CDioLcAdapter(QObject *parent = nullptr);
	~CDioLcAdapter();
	static CDioLcAdapter *pThis;



public slots:

    void slotTimeout();

	int slotBoardOpenPort(unsigned int devId, unsigned short port);
	int slotBoardClosePort(unsigned int devId, unsigned short port);
	int slotBoardIsDeviceOpened(unsigned char devId);

	int slotBoardGetVerInfo(unsigned int devId);

	int slotBoardSetPwmParams(unsigned int devId,
		unsigned char ucChIdx,
		unsigned char ucPwmMode,
		unsigned char ucPwmValue,
		unsigned char ucPwmHoldingTime,
		unsigned char ucPwmOnOff);

	int slotBoardGetPwmParams(unsigned int devId, unsigned char ucChIdx);

    // for the general parameters settings and gettings command
    int slotSetGeneralParam(unsigned int devId, unsigned char ucParamId, unsigned char ucParamLen, unsigned int paramValue, unsigned char ucError, unsigned int uiErrorId );
    int slotGetGeneralParam(unsigned int devId, unsigned char ucParamId, unsigned char ucParamLen, unsigned int paramValue, unsigned char ucError, unsigned int uiErrorId );

    int slotIapDownload(unsigned int devId, QString imageFile);

signals:
	void signalComOpenCB(unsigned short portNum, 
		unsigned char  ucHardwareMajorVer,
		unsigned char  ucHardwareMinorVer,
		unsigned char  ucHardwareRevVer,
		unsigned char  ucFirmwareMajorVer,
		unsigned char  ucFirmwareMinorVer,
		unsigned char  ucFirmwareRevVer, 
		unsigned char ucError, 
		unsigned int uiErrorId);
	void signalComCloseCB(unsigned char ucError, unsigned int uiErrorId);
	void signalGetDeviceVerCB(
		unsigned char  ucHardwareMajorVer,
		unsigned char  ucHardwareMinorVer,
		unsigned char  ucHardwareRevVer,
		unsigned char  ucFirmwareMajorVer,
		unsigned char  ucFirmwareMinorVer,
		unsigned char  ucFirmwareRevVer,
		unsigned char  ucError,
		unsigned int  uiErrorId);
	void signalSetPwmParamsCB(unsigned char  ucChIdx, unsigned char ucError, unsigned int uiErrorId);
	void signalGetPwmParamsCB(unsigned char  ucChIdx,
		unsigned char  ucPwmMode,
		unsigned char  ucPwmValue,
		unsigned char  ucPwmHoldingTime,
		unsigned char  ucPwmOnOff,
		unsigned char ucError,
		unsigned int uiErrorId);
	
    // for the general parameters settings and gettings
    void signalSetGeneralParamCB(unsigned char paramId, unsigned int paramValue, unsigned char ucError, unsigned int uiErrorId);
    void signalGetGeneralParamCB(unsigned char paramId, unsigned int paramValue, unsigned char ucError, unsigned int uiErrorId);


    void signalIapDownloadCB(unsigned char ucDevId, unsigned int uiFileTotalSize, unsigned int uiFileSizeDownloaded, unsigned char ucError, unsigned int uiErrorId);


public:
    LC_LibraryBaseInit_t m_LC_LibraryBaseInit;
    LC_LibraryBaseDeinit_t   m_LC_LibraryBaseDeinit;
    DIOLC_Process_t m_DIOLC_Process;
    DIOLC_OpenDevice_t   m_DIOLC_OpenDevice;
    DIOLC_CloseDevice_t  m_DIOLC_CloseDevice;
    DIOLC_IsDeviceOpened_t m_DIOLC_IsDeviceOpened;

    LC_GetVerInfo_t m_LC_GetVerInfo;
    LC_SetPwmParams_t m_LC_SetPwmParams;
    LC_GetPwmParams_t m_LC_GetPwmParams;

    DIOLC_SetParam_t m_DIOLC_SetParam;
    DIOLC_GetParam_t m_DIOLC_GetParam;

	bool m_bLcEnabled;
	bool m_bAioEnabled;
    unsigned short m_bDioNum;

	// DIO functions
	/*-Polling Mode API------------------------------------------------------------------------------*/
    DIO_LibraryBaseInit_t m_DIO_LibraryBaseInit;
    DIO_LibraryBaseDeInit_t   m_DIO_LibraryBaseDeinit;
    //DIO_PollingReadDiBit_t m_DIO_PollingReadDiBit;
    DIO_PollingReadDiByte_t m_DIO_PollingReadDiByte;
    DIO_PollingReadDiWord_t m_DIO_PollingReadDiWord;
   //DIO_PollingWriteDoBit_t m_DIO_PollingWriteDoBit;
    DIO_PollingWriteDoByte_t m_DIO_PollingWriteDoByte;
    DIO_PollingWriteDoWord_t m_DIO_PollingWriteDoWord;

    LC_IAPDownload_t m_LC_IAPDownload;

    unsigned short m_port;

protected:
	void run();

private:

	int pvInit();


	// Light control CALL backs
	static void ComOpenCB(LC_CALLBACK_ARG_T Arg);
	static void ComCloseCB(LC_CALLBACK_ARG_T Arg);
	static void GetDeviceVerCB(LC_CALLBACK_ARG_T Arg);
	static void SetPwmParamsCB(LC_CALLBACK_ARG_T Arg);
	static void GetPwmParamsCB(LC_CALLBACK_ARG_T Arg);

    static void SetGeneralParamCB(LC_CALLBACK_ARG_T Arg);
    static void GetGeneralParamCB(LC_CALLBACK_ARG_T Arg);

    static void IapDownloadCB(LC_CALLBACK_ARG_T Arg);

    //HMODULE          hDIO;
    //int             m_bLoaded;

    QTimer *m_xtimer;

};

