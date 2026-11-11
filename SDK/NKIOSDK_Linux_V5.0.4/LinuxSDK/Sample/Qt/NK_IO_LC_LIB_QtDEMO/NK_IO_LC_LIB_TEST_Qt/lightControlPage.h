#pragma once
//#include <windows.h>
#include <QWidget>
#include <QtSerialPort/qserialport.h>
#include <qslider.h>
#include <qthread.h>
#include "ui_lightControlPage.h"
#include "dioLcAdapter.h"


class lightControlPage : public QWidget
{
	Q_OBJECT

public:

	lightControlPage(CDioLcAdapter * adapter, QWidget *parent = Q_NULLPTR);
	~lightControlPage();

signals:
	int signalBoardOpenPort(unsigned int devId, unsigned short port);
	int signalBoardClosePort(unsigned int devId, unsigned short port);
	int signalBoardIsDeviceOpened(unsigned char devId);

	int signalBoardGetVerInfo(unsigned int devId);

	int signalBoardSetPwmParams(unsigned int devId,
		unsigned char ucChIdx,
		unsigned char ucPwmMode,
		unsigned char ucPwmValue,
		unsigned char ucPwmHoldingTime,
		unsigned char ucPwmOnOff);

	int signalBoardGetPwmParams(unsigned int devId, unsigned char ucChIdx);

    int signalSetGeneralParam(unsigned int devId, unsigned char ucParamId, unsigned char ucParamLen, unsigned int paramValue, unsigned char ucError, unsigned int uiErrorId );
    int signalGetGeneralParam(unsigned int devId, unsigned char ucParamId, unsigned char ucParamLen, unsigned int paramValue, unsigned char ucError, unsigned int uiErrorId );

     int signalIapDownload(unsigned int devId, QString imageFile);

protected slots:

	void slotOnConnect();

	void slotOnReadParamCh0();
	void slotOnWriteParamCh0();
	void slotOnTurnOnCh0(bool onoff);
	void slotOnWriteParamOnlineCh0(int value);

	void slotOnReadParamCh1();
	void slotOnWriteParamCh1();
	void slotOnTurnOnCh1(bool onoff);
	void slotOnWriteParamOnlineCh1(int value);

	void slotOnReadParamCh2();
	void slotOnWriteParamCh2();
	void slotOnTurnOnCh2(bool onoff);
	void slotOnWriteParamOnlineCh2(int value);

	void slotOnReadParamCh3();
	void slotOnWriteParamCh3();
	void slotOnTurnOnCh3(bool onoff);
	void slotOnWriteParamOnlineCh3(int value);

    void slotOnReadCh0Advanced();
    void slotOnReadCh1Advanced();
    void slotOnReadCh2Advanced();
    void slotOnReadCh3Advanced();

    void slotOnWriteCh0Advanced();
    void slotOnWriteCh1Advanced();
    void slotOnWriteCh2Advanced();
    void slotOnWriteCh3Advanced();


	void slotComOpenCB(unsigned short portNum, 
		unsigned char hardwareMajorVer,
		unsigned char hardwareMinorVer,
		unsigned char hardwareRevVer,
		unsigned char firmwareMajorVer,
		unsigned char firmwareMinorVer,
		unsigned char firmwareRevVer,
		unsigned char ucError, unsigned int uiErrorId);
	void slotComCloseCB(unsigned char ucError, unsigned int uiErrorId);
	void slotGetDeviceVerCB(
		unsigned char  ucHardwareMajorVer,
		unsigned char  ucHardwareMinorVer,
		unsigned char  ucHardwareRevVer,
		unsigned char  ucFirmwareMajorVer,
		unsigned char  ucFirmwareMinorVer,
		unsigned char  ucFirmwareRevVer,
		unsigned char  ucError,
		unsigned int  uiErrorId);
	void slotSetPwmParamsCB(unsigned char  ucChIdx, unsigned char ucError, unsigned int uiErrorId);
	void slotGetPwmParamsCB(unsigned char  ucChIdx,
		unsigned char  ucPwmMode,
		unsigned char  ucPwmValue,
		unsigned char  ucPwmHoldingTime,
		unsigned char  ucPwmOnOff,
		unsigned char ucError,
		unsigned int uiErrorId);
	

    // for the general parameters settings and gettings
    void slotSetGeneralParamCB(unsigned char paramId, unsigned int paramValue, unsigned char ucError, unsigned int uiErrorId);
    void slotGetGeneralParamCB(unsigned char paramId, unsigned int paramValue, unsigned char ucError, unsigned int uiErrorId);

    void slotOpenImageFile();
    void slotDownloadImageFile();
    void slotIapDownloadCB(unsigned char ucDevId, unsigned int uiFileTotalSize, unsigned int uiFileSizeDownloaded, unsigned char ucError, unsigned int uiErrorId);

private:
	void initSettings();

	int getComPort(QString comName);

	
private:
	Ui::lightControlPage ui;
	static lightControlPage *pThis;
    unsigned int m_downloadPercent;

    QString m_imageFilePath;

	QSerialPort *m_currentPort;
	int m_port;
	uint m_baudrate;
	int m_databits;

	int connect_flag;

	//lightControlServer *m_pServerThreadHdl;
	CDioLcAdapter *m_adapter;



};
