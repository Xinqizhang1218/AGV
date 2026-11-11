
#include <QtSerialPort/QSerialPortInfo>
#include <QtSerialPort/QSerialPort>
#include <qthread.h>
#include <qfiledialog.h>
#include <qtimer.h>
#include "lightControlPage.h"
//#include "PortSerial.h"
#include "qdebug.h"
#include "qmessagebox.h"

#define DEV_ID 0x01





void setTabWidgetStyleSheet(QTabWidget* obj) {
#if 1
	obj->setStyleSheet(
		"QTabWidget{"
		"background-color:transparent;" //transparent
		"}"
		"QTabWidget::pane{"
		"    border:2px;"
		//"    border-color: black;"
		//"border-style: outset;"
		"}"
		"QTabWidget::tab-bar{"
		"    alignment:left;"
		"    border:1px;"
		"    border-color: black;"
		"}"
		"QTabBar::tab{"
		"    background:#E4E4E4;"
		"    border:0px;"
		"    border-color: black;"
		"    color:black;"
		"    min-width:35ex;"
		"    min-height:8ex;"
		"}"
		"QTabBar::tab:hover{"
		"    background:#87CEFA;"
		"color:black;"
		"}"
		"QTabBar::tab:selected{"
		"    border-color: black;"
		"    background:#27A7F8;"
		"    color:black;"
		"}"
	);
#else
	obj->setStyleSheet(
		"QTabWidget::pane{ \
		border:none; \
} \
QTabWidget::tab - bar{ \
		alignment:left; \
} \
QTabBar::tab{ \
	background:transparent; \
	color:white; \
	min - width:30ex; \
	min - height:10ex; \
} \
QTabBar::tab:hover{ \
	background:rgb(255, 255, 255, 100); \
} \
QTabBar::tab : selected{ \
	border - color: white; \
	background:white; \
	color:green; \
}" );
#endif 
}


lightControlPage* lightControlPage::pThis = NULL;

lightControlPage::lightControlPage(CDioLcAdapter * adapter, QWidget *parent)
	: QWidget(parent)
	, m_adapter(adapter)
{
	ui.setupUi(this);
	setTabWidgetStyleSheet(ui.tabWidget);
	pThis = this;
	//s_downloadPercent = 0;
	
	//ui.m_comboBoxBaudRate->hide();
	//ui.m_lblBaudRate->hide();
	//ui.m_lblPort->hide();
	//ui.m_comboBoxPort->hide();
	

	connect(this, SIGNAL(signalBoardOpenPort(unsigned int , unsigned short )), CDioLcAdapter::pThis,SLOT(slotBoardOpenPort(unsigned int, unsigned short)));
	connect(this, SIGNAL(signalBoardClosePort(unsigned int, unsigned short)), CDioLcAdapter::pThis, SLOT(slotBoardClosePort(unsigned int, unsigned short)));

	connect(this, SIGNAL(signalBoardGetVerInfo(unsigned int )), CDioLcAdapter::pThis, SLOT(slotBoardGetVerInfo(unsigned int)));
	connect(this, SIGNAL(signalBoardSetPwmParams(unsigned int ,	unsigned char ,unsigned char ,unsigned char ,unsigned char ,unsigned char )), CDioLcAdapter::pThis, SLOT(slotBoardSetPwmParams(unsigned int, unsigned char, unsigned char, unsigned char, unsigned char, unsigned char)));
	connect(this, SIGNAL(signalBoardGetPwmParams(unsigned int , unsigned char )), CDioLcAdapter::pThis, SLOT(slotBoardGetPwmParams(unsigned int, unsigned char)));
	



	connect(CDioLcAdapter::pThis, SIGNAL(signalComOpenCB(unsigned short, 
		unsigned char, 
		unsigned char , 
		unsigned char,
		unsigned char, 
		unsigned char, 
		unsigned char,
		unsigned char, 
		unsigned int)), this, SLOT(slotComOpenCB(unsigned short, 
			unsigned char, 
			unsigned char,
			unsigned char,
			unsigned char,
			unsigned char,
			unsigned char,
			unsigned char,
			unsigned int)));
	connect(CDioLcAdapter::pThis, SIGNAL(signalComCloseCB(unsigned char, unsigned int)), this, SLOT(slotComCloseCB(unsigned char , unsigned int )));
	connect(CDioLcAdapter::pThis, SIGNAL(signalGetDeviceVerCB(unsigned char,unsigned char,unsigned char,unsigned char,unsigned char,unsigned char,unsigned char,unsigned int)),
		this, SLOT(slotGetDeviceVerCB(unsigned char  ,unsigned char  ,unsigned char  ,unsigned char  ,unsigned char  ,unsigned char  ,unsigned char  ,unsigned int  )));
	connect(CDioLcAdapter::pThis, SIGNAL(signalSetPwmParamsCB(unsigned char, unsigned char, unsigned int)), this, SLOT(slotSetPwmParamsCB(unsigned char , unsigned char , unsigned int )));
	
	connect(CDioLcAdapter::pThis, SIGNAL(signalGetPwmParamsCB(unsigned char  ,
		unsigned char,
		unsigned char,
		unsigned char,
		unsigned char,
		unsigned char,
		unsigned int)), 
		this, SLOT(slotGetPwmParamsCB(unsigned char  ,
		unsigned char  ,
		unsigned char  ,
		unsigned char  ,
		unsigned char  ,
		unsigned char ,
		unsigned int )));


    connect(CDioLcAdapter::pThis, SIGNAL(signalSetGeneralParamCB(unsigned char , unsigned int , unsigned char , unsigned int )),
            this, SLOT(slotSetGeneralParamCB(unsigned char , unsigned int , unsigned char , unsigned int )));
    connect(this, SIGNAL(signalSetGeneralParam(unsigned int , unsigned char , unsigned char , unsigned int , unsigned char , unsigned int  )),
            CDioLcAdapter::pThis, SLOT(slotSetGeneralParam(unsigned int , unsigned char , unsigned char , unsigned int , unsigned char , unsigned int  )));

    connect(CDioLcAdapter::pThis, SIGNAL(signalGetGeneralParamCB(unsigned char , unsigned int , unsigned char , unsigned int )),
            this, SLOT(slotGetGeneralParamCB(unsigned char , unsigned int , unsigned char , unsigned int )));
    connect(this, SIGNAL(signalGetGeneralParam(unsigned int , unsigned char , unsigned char , unsigned int , unsigned char , unsigned int  )),
            CDioLcAdapter::pThis, SLOT(slotGetGeneralParam(unsigned int , unsigned char , unsigned char , unsigned int , unsigned char , unsigned int  )));


    connect(CDioLcAdapter::pThis, SIGNAL(signalIapDownloadCB(unsigned char , unsigned int , unsigned int , unsigned char , unsigned int )),
            this, SLOT(slotIapDownloadCB(unsigned char , unsigned int , unsigned int , unsigned char , unsigned int )));
    connect(this, SIGNAL(signalIapDownload(unsigned int , QString )),
            CDioLcAdapter::pThis, SLOT(slotIapDownload(unsigned int , QString )));


	m_adapter->start();

	initSettings();
	

}

lightControlPage::~lightControlPage()
{
	
}



void lightControlPage::initSettings()
{

    ui.m_progressBarDownload->setValue(0);
    ui.m_filePath->setReadOnly(true);
    m_downloadPercent = 0;
    ui.m_btnDownload->setEnabled(false);
    connect(ui.m_btnDownload, SIGNAL(clicked()), this, SLOT(slotDownloadImageFile()));
	
    ui.m_btnOpenFile->setEnabled(true);
    connect(ui.m_btnOpenFile, SIGNAL(clicked()), this, SLOT(slotOpenImageFile()));
    ui.m_downloadStatus->setText("");


	ui.m_hardwareVer->setText("");
	ui.m_firmwareVer->setText("");

	

	connect_flag = 0;
	ui.tabWidget->setEnabled(false);
	ui.m_connectBtn->setText(tr("Connect"));
	ui.m_connectBtn->setStyleSheet("background-color:red;");



	ui.m_comboBoxPort->clear();
	m_currentPort = new QSerialPort();
	QSerialPortInfo comPortInfo;
	foreach(const QSerialPortInfo &info, QSerialPortInfo::availablePorts())
	{
		comPortInfo = info;
		//ui.m_comboBoxPort->addItem(comPortInfo.portName());
	}
    //ui.m_comboBoxPort->addItem("COM3");
    QString comPort = "COM"+ QString("%1").arg(m_adapter->m_port);
    ui.m_comboBoxPort->addItem(comPort);

	ui.m_comboBoxBaudRate->clear();
	QStringList baudRateList;
	baudRateList << "115200" << "57600" << "38400" << "19200" << "9600";
	ui.m_comboBoxBaudRate->addItems(baudRateList);
	ui.m_comboBoxBaudRate->setCurrentIndex(0);
	QStringList pwmModeList;
    pwmModeList  << "Soft Switch" << "Hard Switch" << "Hard Trigger" << "Soft Trigger";


	ui.m_ch0Mode->clear();
	ui.m_ch0Mode->addItems(pwmModeList);

	ui.m_ch1Mode->clear();
	ui.m_ch1Mode->addItems(pwmModeList);

	ui.m_ch2Mode->clear();
	ui.m_ch2Mode ->addItems(pwmModeList);

	ui.m_ch3Mode->clear();
	ui.m_ch3Mode ->addItems(pwmModeList);

	ui.m_ch0Mode->setCurrentIndex(0);
	ui.m_ch1Mode->setCurrentIndex(0);
	ui.m_ch2Mode->setCurrentIndex(0);
	ui.m_ch3Mode->setCurrentIndex(0);


    QStringList holdingTimeUnitList;
    holdingTimeUnitList << "0:1000ms" << "1:100ms" << "2:10ms" << "3:1ms" << " ";

    ui.m_ch0HoldingTimeUnit->clear();
    ui.m_ch0HoldingTimeUnit->addItems(holdingTimeUnitList);
    ui.m_ch0HoldingTimeUnit->setCurrentIndex(4);

    ui.m_ch1HoldingTimeUnit->clear();
    ui.m_ch1HoldingTimeUnit->addItems(holdingTimeUnitList);
    ui.m_ch1HoldingTimeUnit->setCurrentIndex(4);

    ui.m_ch2HoldingTimeUnit->clear();
    ui.m_ch2HoldingTimeUnit->addItems(holdingTimeUnitList);
    ui.m_ch2HoldingTimeUnit->setCurrentIndex(4);

    ui.m_ch3HoldingTimeUnit->clear();
    ui.m_ch3HoldingTimeUnit->addItems(holdingTimeUnitList);
    ui.m_ch3HoldingTimeUnit->setCurrentIndex(4);

	connect(ui.m_connectBtn, SIGNAL(clicked()), this, SLOT(slotOnConnect()));

	connect(ui.m_ch0ReadBtn, SIGNAL(clicked()), this, SLOT(slotOnReadParamCh0()));
	connect(ui.m_ch0WriteBtn, SIGNAL(clicked()), this, SLOT(slotOnWriteParamCh0()));
	connect(ui.m_ch0Switch, SIGNAL(checkedChanged(bool)), this, SLOT(slotOnTurnOnCh0(bool)));
	connect(ui.m_ch0Slider, SIGNAL(valueChanged(int)), this, SLOT(slotOnWriteParamOnlineCh0(int)));

	connect(ui.m_ch1ReadBtn, SIGNAL(clicked()), this, SLOT(slotOnReadParamCh1()));
	connect(ui.m_ch1WriteBtn, SIGNAL(clicked()), this, SLOT(slotOnWriteParamCh1()));
	connect(ui.m_ch1Switch, SIGNAL(checkedChanged(bool)), this, SLOT(slotOnTurnOnCh1(bool)));
	connect(ui.m_ch1Slider, SIGNAL(valueChanged(int)), this, SLOT(slotOnWriteParamOnlineCh1(int)));

	connect(ui.m_ch2ReadBtn, SIGNAL(clicked()), this, SLOT(slotOnReadParamCh2()));
	connect(ui.m_ch2WriteBtn, SIGNAL(clicked()), this, SLOT(slotOnWriteParamCh2()));
	connect(ui.m_ch2Switch, SIGNAL(checkedChanged(bool)), this, SLOT(slotOnTurnOnCh2(bool)));
	connect(ui.m_ch2Slider, SIGNAL(valueChanged(int)), this, SLOT(slotOnWriteParamOnlineCh2(int)));

	connect(ui.m_ch3ReadBtn, SIGNAL(clicked()), this, SLOT(slotOnReadParamCh3()));
	connect(ui.m_ch3WriteBtn, SIGNAL(clicked()), this, SLOT(slotOnWriteParamCh3()));
	connect(ui.m_ch3Switch, SIGNAL(checkedChanged(bool)), this, SLOT(slotOnTurnOnCh3(bool)));
	connect(ui.m_ch3Slider, SIGNAL(valueChanged(int)), this, SLOT(slotOnWriteParamOnlineCh3(int)));

    connect(ui.m_btnCh0ReadAdvanced, SIGNAL(clicked()),this, SLOT(slotOnReadCh0Advanced()));
    connect(ui.m_btnCh1ReadAdvanced, SIGNAL(clicked()),this, SLOT(slotOnReadCh1Advanced()));
    connect(ui.m_btnCh2ReadAdvanced, SIGNAL(clicked()),this, SLOT(slotOnReadCh2Advanced()));
    connect(ui.m_btnCh3ReadAdvanced, SIGNAL(clicked()),this, SLOT(slotOnReadCh3Advanced()));

    connect(ui.m_btnCh0WriteAdvanced, SIGNAL(clicked()),this, SLOT(slotOnWriteCh0Advanced()));
    connect(ui.m_btnCh1WriteAdvanced, SIGNAL(clicked()),this, SLOT(slotOnWriteCh1Advanced()));
    connect(ui.m_btnCh2WriteAdvanced, SIGNAL(clicked()),this, SLOT(slotOnWriteCh2Advanced()));
    connect(ui.m_btnCh3WriteAdvanced, SIGNAL(clicked()),this, SLOT(slotOnWriteCh3Advanced()));



	// BaudRate
	if (ui.m_comboBoxBaudRate->currentText() == "115200")
	{
		m_currentPort->setBaudRate(QSerialPort::Baud115200, QSerialPort::AllDirections);
		m_baudrate = 115200;
	}
	else if (ui.m_comboBoxBaudRate->currentText() == "9600")
	{
		m_currentPort->setBaudRate(QSerialPort::Baud9600, QSerialPort::AllDirections);
		m_baudrate = 9600;
	}
	else if (ui.m_comboBoxBaudRate->currentText() == "1200")
	{
		m_currentPort->setBaudRate(QSerialPort::Baud1200, QSerialPort::AllDirections);
		m_baudrate = 1200;
	}
	else if (ui.m_comboBoxBaudRate->currentText() == "2400")
	{
		m_currentPort->setBaudRate(QSerialPort::Baud2400, QSerialPort::AllDirections);
		m_baudrate = 2400;
	}
	else if (ui.m_comboBoxBaudRate->currentText() == "4800")
	{
		m_currentPort->setBaudRate(QSerialPort::Baud4800, QSerialPort::AllDirections);
		m_baudrate = 4800;
	}
	else if (ui.m_comboBoxBaudRate->currentText() == "19200")
	{
		m_currentPort->setBaudRate(QSerialPort::Baud19200, QSerialPort::AllDirections);
		m_baudrate = 19200;
	}
	else if (ui.m_comboBoxBaudRate->currentText() == "38400")
	{
		m_currentPort->setBaudRate(QSerialPort::Baud38400, QSerialPort::AllDirections);
		m_baudrate = 38400;
	}
	else if (ui.m_comboBoxBaudRate->currentText() == "57600")
	{
		m_currentPort->setBaudRate(QSerialPort::Baud57600, QSerialPort::AllDirections);
		m_baudrate = 57600;
	}

	m_currentPort->setDataBits(QSerialPort::Data8);
	m_currentPort->setStopBits(QSerialPort::OneStop);
	m_currentPort->setParity(QSerialPort::NoParity);

	
	

}

int lightControlPage::getComPort(QString comName)
{
	int ret = -1;
	QString port = comName;
	//QString pattern("^[+-] ? \\d*[.] ? \\d*$");
	QString pattern("^[1-9]\\d*|0$");
	QRegExp rx(pattern);
	if (port != NULL)
	{
        //
		port = port.replace(QRegExp("[^\\d.\\d]"), "");
		if (rx.exactMatch(port))
		{
			ret = QString(port).toInt();
		}
	}
	return ret;
}

void lightControlPage::slotOnConnect()
{
	
	int retry = 0;
	int writeBytes = 0;
	int readBytes = 0;
	m_port = getComPort(ui.m_comboBoxPort->currentText());
    //m_port = 2;
    m_port = m_port - 1;
	if (connect_flag == 0)
	{
		emit signalBoardOpenPort(DEV_ID, m_port);

	}
	else if(connect_flag == 1)
	{
		emit signalBoardClosePort(DEV_ID, m_port);
	}


}

void lightControlPage::slotOnReadParamCh0()
{
	emit signalBoardGetPwmParams(DEV_ID, 0x01);
}
void lightControlPage::slotOnWriteParamCh0()
{

	emit signalBoardSetPwmParams(DEV_ID, 
		0x01, 
		ui.m_ch0Mode->currentIndex(), 
		ui.m_ch0Slider->value(), 
		ui.m_ch0PwmHoldingTime->value(), 
		(ui.m_ch0Switch->getChecked() == true) ? 1 : 0);

}
void lightControlPage::slotOnTurnOnCh0(bool onoff)
{
	emit signalBoardSetPwmParams(DEV_ID,
		0x01,
		ui.m_ch0Mode->currentIndex(),
		ui.m_ch0Slider->value(),
		ui.m_ch0PwmHoldingTime->value(),
		(onoff == true) ? 1 : 0);
}
void lightControlPage::slotOnWriteParamOnlineCh0(int value)
{
	if (ui.m_ch0Switch->getChecked() == true)
	{
		emit signalBoardSetPwmParams(DEV_ID,
			0x01,
			ui.m_ch0Mode->currentIndex(),
			value,
			ui.m_ch0PwmHoldingTime->value(),
			 1 );
	}
}



void lightControlPage::slotOnReadParamCh1()
{
	emit signalBoardGetPwmParams(DEV_ID, 0x02);
}
void lightControlPage::slotOnWriteParamCh1()
{

	emit signalBoardSetPwmParams(DEV_ID,
		0x02,
		ui.m_ch1Mode->currentIndex(),
		ui.m_ch1Slider->value(),
		ui.m_ch1PwmHoldingTime->value(),
		(ui.m_ch1Switch->getChecked() == true) ? 1 : 0);
 
	
}
void lightControlPage::slotOnTurnOnCh1(bool onoff)
{

	emit signalBoardSetPwmParams(DEV_ID,
		0x02,
		ui.m_ch1Mode->currentIndex(),
		ui.m_ch1Slider->value(),
		ui.m_ch1PwmHoldingTime->value(),
		(onoff == true) ? 1 : 0);

}

void lightControlPage::slotOnWriteParamOnlineCh1(int value)
{
	if (ui.m_ch1Switch->getChecked() == true)
	{
		emit signalBoardSetPwmParams(DEV_ID,
			0x02,
			ui.m_ch1Mode->currentIndex(),
			value,
			ui.m_ch1PwmHoldingTime->value(),
			1);
	}
}

void lightControlPage::slotOnReadParamCh2()
{
	emit signalBoardGetPwmParams(DEV_ID, 0x04);
}
void lightControlPage::slotOnWriteParamCh2()
{

	emit signalBoardSetPwmParams(DEV_ID,
		0x04,
		ui.m_ch2Mode->currentIndex(),
		ui.m_ch2Slider->value(),
		ui.m_ch2PwmHoldingTime->value(),
		(ui.m_ch2Switch->getChecked() == true) ? 1 : 0);

}
void lightControlPage::slotOnTurnOnCh2(bool onoff)
{

	emit signalBoardSetPwmParams(DEV_ID,
		0x04,
		ui.m_ch2Mode->currentIndex(),
		ui.m_ch2Slider->value(),
		ui.m_ch2PwmHoldingTime->value(),
		(onoff == true) ? 1 : 0);

}

void lightControlPage::slotOnWriteParamOnlineCh2(int value)
{
	if (ui.m_ch2Switch->getChecked() == true)
	{
		emit signalBoardSetPwmParams(DEV_ID,
			0x04,
			ui.m_ch2Mode->currentIndex(),
			value,
			ui.m_ch2PwmHoldingTime->value(),
			1);
	}
}

void lightControlPage::slotOnReadParamCh3()
{
	emit signalBoardGetPwmParams(DEV_ID, 0x08);
}
void lightControlPage::slotOnWriteParamCh3()
{

	emit signalBoardSetPwmParams(DEV_ID,
		0x08,
		ui.m_ch3Mode->currentIndex(),
		ui.m_ch3Slider->value(),
		ui.m_ch3PwmHoldingTime->value(),
		(ui.m_ch3Switch->getChecked() == true) ? 1 : 0);

}
void lightControlPage::slotOnTurnOnCh3(bool onoff)
{

	emit signalBoardSetPwmParams(DEV_ID,
		0x08,
		ui.m_ch3Mode->currentIndex(),
		ui.m_ch3Slider->value(),
		ui.m_ch3PwmHoldingTime->value(),
		(onoff == true) ? 1 : 0);

}

void lightControlPage::slotOnWriteParamOnlineCh3(int value)
{
	if (ui.m_ch3Switch->getChecked() == true)
	{
		emit signalBoardSetPwmParams(DEV_ID,
			0x08,
			ui.m_ch3Mode->currentIndex(),
			value,
			ui.m_ch3PwmHoldingTime->value(),
			1);
	}
}


void lightControlPage::slotOnReadCh0Advanced()
{
    unsigned char m_paramId = 10;
    unsigned char m_paramLen = 1;

    emit signalGetGeneralParam(DEV_ID,m_paramId,m_paramLen,0,0,0);
}
void lightControlPage::slotOnReadCh1Advanced()
{
    unsigned char m_paramId = 11;
    unsigned char m_paramLen = 1;


    emit signalGetGeneralParam(DEV_ID,m_paramId,m_paramLen,0,0,0);
}
void lightControlPage::slotOnReadCh2Advanced()
{
    unsigned char m_paramId = 12;
    unsigned char m_paramLen = 1;



    emit signalGetGeneralParam(DEV_ID,m_paramId,m_paramLen,0,0,0);
}
void lightControlPage::slotOnReadCh3Advanced()
{
    unsigned char m_paramId = 13;
    unsigned char m_paramLen = 1;


    emit signalGetGeneralParam(DEV_ID,m_paramId,m_paramLen,0,0,0);
}

void lightControlPage::slotOnWriteCh0Advanced()
{
    unsigned char m_paramId = 10;
    unsigned char m_paramLen = 1;
    unsigned int m_paramValue = ui.m_ch0HoldingTimeUnit->currentIndex();
    if(m_paramValue >= 4)
    {
        m_paramValue = 0;
    }
    emit signalSetGeneralParam(DEV_ID,m_paramId,m_paramLen,m_paramValue,0,0);
}
void lightControlPage::slotOnWriteCh1Advanced()
{
    unsigned char m_paramId = 11;
    unsigned char m_paramLen = 1;
    unsigned int m_paramValue = ui.m_ch1HoldingTimeUnit->currentIndex();
    if(m_paramValue >= 4)
    {
        m_paramValue = 0;
    }
    emit signalSetGeneralParam(DEV_ID,m_paramId,m_paramLen,m_paramValue,0,0);
}
void lightControlPage::slotOnWriteCh2Advanced()
{
    unsigned char m_paramId = 12;
    unsigned char m_paramLen = 1;
    unsigned int m_paramValue = ui.m_ch2HoldingTimeUnit->currentIndex();
    if(m_paramValue >= 4)
    {
        m_paramValue = 0;
    }
    emit signalSetGeneralParam(DEV_ID,m_paramId,m_paramLen,m_paramValue,0,0);
}
void lightControlPage::slotOnWriteCh3Advanced()
{
    unsigned char m_paramId = 13;
    unsigned char m_paramLen = 1;
    unsigned int m_paramValue = ui.m_ch3HoldingTimeUnit->currentIndex();
    if(m_paramValue >= 4)
    {
        m_paramValue = 0;
    }
    emit signalSetGeneralParam(DEV_ID,m_paramId,m_paramLen,m_paramValue,0,0);
}

void lightControlPage::slotOpenImageFile()
{
    m_imageFilePath = QFileDialog::getOpenFileName(this, tr("Open Image File"), "./", tr("Bineary file(*.bin)"));
    if(!m_imageFilePath.isEmpty())
    {
        ui.m_filePath->setText(m_imageFilePath);
        ui.m_btnDownload->setEnabled(true);
        m_downloadPercent = 0;
    }
    else
    {
        m_imageFilePath = "";
        ui.m_btnDownload->setEnabled(true);
    }
}
void lightControlPage::slotDownloadImageFile()
{
    if(!m_imageFilePath.isEmpty())
    {
        ui.m_btnDownload->setEnabled(false);
        ui.m_btnOpenFile->setEnabled(false);
        emit signalIapDownload(DEV_ID, m_imageFilePath);
    }
    else
    {
        ui.m_btnOpenFile->setEnabled(true);
        ui.m_btnDownload->setEnabled(false);
    }
}

void lightControlPage::slotIapDownloadCB(unsigned char ucDevId, unsigned int uiFileTotalSize, unsigned int uiFileSizeDownloaded, unsigned char ucError, unsigned int uiErrorId)
{
    if(ucError)
    {
        ui.m_progressBarDownload->setValue(0);
        QMessageBox::warning(this, tr("Warning"),tr("Update firmware error!"), QMessageBox::Ok);

    }
    else
    {
        int percent = ((uiFileSizeDownloaded) *100)/uiFileTotalSize;
        ui.m_progressBarDownload->setValue(percent);
        if(percent > 99)
        {
            ui.m_btnDownload->setEnabled(true);
            ui.m_btnOpenFile->setEnabled(true);
            ui.m_downloadStatus->setText(tr("Download Successful!"));
        }
        else
        {
            ui.m_downloadStatus->setText(tr("Downloading......"));
        }
    }

}





void lightControlPage::slotComOpenCB(unsigned short portNum, 
	unsigned char hardwareMajorVer,
	unsigned char hardwareMinorVer,
	unsigned char hardwareRevVer,
	unsigned char firmwareMajorVer,
	unsigned char firmwareMinorVer,
	unsigned char firmwareRevVer, 
	unsigned char ucError, 
	unsigned int uiErrorId)
{
	//QMessageBox::information(this, tr("Open Port"), tr("Port Opened"));
	if (ucError)
	{
	}
	else
	{
		connect_flag = 1;
		ui.tabWidget->setEnabled(true);
		ui.m_connectBtn->setText(tr("Disconnect"));
		ui.m_connectBtn->setStyleSheet("background-color:green;");

		ui.m_hardwareVer->setText(QString("%1.%2.%3").arg(hardwareMajorVer).arg(hardwareMinorVer).arg(hardwareRevVer));
		ui.m_firmwareVer->setText(QString("%1.%2.%3").arg(firmwareMajorVer).arg(firmwareMinorVer).arg(firmwareRevVer));

		emit signalBoardGetPwmParams(DEV_ID, 0x01);
		emit signalBoardGetPwmParams(DEV_ID, 0x02);
		emit signalBoardGetPwmParams(DEV_ID, 0x04);
		emit signalBoardGetPwmParams(DEV_ID, 0x08);
	}
	
}
void lightControlPage::slotComCloseCB(unsigned char ucError, unsigned int uiErrorId)
{
	if (ucError)
	{
		ui.m_hardwareVer->setText("x.x.x");
		ui.m_firmwareVer->setText("x.x.x");
	}
	else
	{
		connect_flag = 0;
		ui.tabWidget->setEnabled(false);
		ui.m_connectBtn->setText(tr("Connect"));
		ui.m_connectBtn->setStyleSheet("background-color:red;");

		ui.m_hardwareVer->setText("");
		ui.m_firmwareVer->setText("");

	}
}
void lightControlPage::slotGetDeviceVerCB(
	unsigned char  ucHardwareMajorVer,
	unsigned char  ucHardwareMinorVer,
	unsigned char  ucHardwareRevVer,
	unsigned char  ucFirmwareMajorVer,
	unsigned char  ucFirmwareMinorVer,
	unsigned char  ucFirmwareRevVer,
	unsigned char  ucError,
	unsigned int  uiErrorId)
{
	if (ucError)
	{
		QMessageBox::warning(this, tr("Warning"),
			tr("Get device version Failed!"),
			QMessageBox::Ok);
		ui.m_hardwareVer->setText("x.x.x");
		ui.m_firmwareVer->setText("x.x.x");
	}
	else
	{
		ui.m_hardwareVer->setText(QString("%1.%2.%3").arg(ucHardwareMajorVer).arg(ucHardwareMinorVer).arg(ucHardwareRevVer));
		ui.m_firmwareVer->setText(QString("%1.%2.%3").arg(ucFirmwareMajorVer).arg(ucFirmwareMinorVer).arg(ucFirmwareRevVer));
	}
	
}
void lightControlPage::slotSetPwmParamsCB(unsigned char  ucChIdx, unsigned char ucError, unsigned int uiErrorId)
{

}
void lightControlPage::slotGetPwmParamsCB(unsigned char  ucChIdx,
	unsigned char  ucPwmMode,
	unsigned char  ucPwmValue,
	unsigned char  ucPwmHoldingTime,
	unsigned char  ucPwmOnOff,
	unsigned char ucError,
	unsigned int uiErrorId)
{
	if (ucError)
	{
		QMessageBox::warning(this, tr("Warning"),
			tr("Get Pwm params error!"),
			QMessageBox::Ok);
	}
	else
	{
		switch (ucChIdx)
		{
		case 0x01:

			ui.m_ch0Mode->setCurrentIndex(ucPwmMode);
			ui.m_ch0Slider->setValue(ucPwmValue);
			ui.m_ch0PwmHoldingTime->setValue(ucPwmHoldingTime);
			ui.m_ch0Switch->setChecked((ucPwmOnOff & 0x01) == 0x01 ? true : false);

			break;
		case 0x02:

			ui.m_ch1Mode->setCurrentIndex(ucPwmMode);
			ui.m_ch1Slider->setValue(ucPwmValue);
			ui.m_ch1PwmHoldingTime->setValue(ucPwmHoldingTime);
			ui.m_ch1Switch->setChecked((ucPwmOnOff & 0x01) == 0x01 ? true : false);

			break;
		case 0x04:

			ui.m_ch2Mode->setCurrentIndex(ucPwmMode);
			ui.m_ch2Slider->setValue(ucPwmValue);
			ui.m_ch2PwmHoldingTime->setValue(ucPwmHoldingTime);
			ui.m_ch2Switch->setChecked((ucPwmOnOff & 0x01) == 0x01 ? true : false);

			break;
		case 0x08:

			ui.m_ch3Mode->setCurrentIndex(ucPwmMode);
			ui.m_ch3Slider->setValue(ucPwmValue);
			ui.m_ch3PwmHoldingTime->setValue(ucPwmHoldingTime);
			ui.m_ch3Switch->setChecked((ucPwmOnOff & 0x01) == 0x01 ? true : false);

			break;
		default:
			break;
		}
	}
}



void lightControlPage::slotSetGeneralParamCB(unsigned char paramId, unsigned int paramValue, unsigned char ucError, unsigned int uiErrorId)
{
    if(ucError > 0)
    {
        QMessageBox::warning(this, tr("Warning"), tr("Set Advanced parameter error!"),QMessageBox::Ok);
    }
    else
    {
        unsigned int timeUnit = 1000; // default is 1000 ms
        if((paramId >= 10)&&(paramId < 13))
        {
            switch(paramValue)
            {
            case 0:
                timeUnit = 1000;
                break;
            case 1:
                timeUnit = 100;
                break;
            case 2:
                timeUnit = 10;
                break;
            case 3:
                timeUnit = 1;
                break;
            default:
                timeUnit = 1000;
                break;

            }
        }
        switch (paramId)
        {
        case 10:
            ui.m_ch0CurrentTimeUnit->setText(QString::number(timeUnit) + "ms");
            break;
        case 11:
            ui.m_ch1CurrentTimeUnit->setText(QString::number(timeUnit) + "ms");
            break;
        case 12:
            ui.m_ch2CurrentTimeUnit->setText(QString::number(timeUnit) + "ms");
            break;
        case 13:
            ui.m_ch3CurrentTimeUnit->setText(QString::number(timeUnit) + "ms");
            break;
        default:
            break;
        }
    }

}
void lightControlPage::slotGetGeneralParamCB(unsigned char paramId, unsigned int paramValue, unsigned char ucError, unsigned int uiErrorId)
{
    if(ucError > 0)
    {
        QMessageBox::warning(this, tr("Warning"), tr("Get Advanced parameter error!"),QMessageBox::Ok);

    }
    else
    {
        unsigned int timeUnit = 1000; // default is 1000 ms
        if((paramId >= 10)&&(paramId < 13))
        {
            switch(paramValue)
            {
            case 0:
                timeUnit = 1000;
                break;
            case 1:
                timeUnit = 100;
                break;
            case 2:
                timeUnit = 10;
                break;
            case 3:
                timeUnit = 1;
                break;
            default:
                timeUnit = 1000;
                break;

            }
        }
        switch (paramId)
        {
        case 10:
            ui.m_ch0HoldingTimeUnit->setCurrentIndex(paramValue);
            ui.m_ch0CurrentTimeUnit->setText(QString::number(timeUnit) + "ms");
            break;
        case 11:
            ui.m_ch1HoldingTimeUnit->setCurrentIndex(paramValue);
            ui.m_ch1CurrentTimeUnit->setText(QString::number(timeUnit) + "ms");
            break;
        case 12:
            ui.m_ch2HoldingTimeUnit->setCurrentIndex(paramValue);
            ui.m_ch2CurrentTimeUnit->setText(QString::number(timeUnit) + "ms");
            break;
        case 13:
            ui.m_ch3HoldingTimeUnit->setCurrentIndex(paramValue);
            ui.m_ch3CurrentTimeUnit->setText(QString::number(timeUnit) + "ms");
            break;
        default:
            break;
        }

    }

}



