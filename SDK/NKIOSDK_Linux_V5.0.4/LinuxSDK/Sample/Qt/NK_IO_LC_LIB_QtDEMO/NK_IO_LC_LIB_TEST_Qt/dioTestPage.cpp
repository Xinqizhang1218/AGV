#include "dioTestPage.h"
#include <qlayout.h>
#include <qgroupbox.h>
#include <qlabel.h>
#include <qmessagebox.h>
#include <qtimer.h>


dioTestPage::dioTestPage(CDioLcAdapter* adapter, QWidget *parent)
	: QWidget(parent)
	, m_adapter(adapter)
{
	ui.setupUi(this);
	startFlag = 0;
	ui.m_StartStopBtn->setText(tr("Start"));
	connect(ui.m_StartStopBtn, SIGNAL(clicked()), this, SLOT(onStartClicked()));

	ui.m_DO0->setEnabled(false);
	ui.m_DO1->setEnabled(false);
	ui.m_DO2->setEnabled(false);
	ui.m_DO3->setEnabled(false);

	ui.m_DO4->setEnabled(false);
	ui.m_DO5->setEnabled(false);
	ui.m_DO6->setEnabled(false);
	ui.m_DO7->setEnabled(false);

	ui.m_DO8->setEnabled(false);
	ui.m_DO9->setEnabled(false);
	ui.m_DO10->setEnabled(false);
	ui.m_DO11->setEnabled(false);

	ui.m_DO12->setEnabled(false);
	ui.m_DO13->setEnabled(false);
	ui.m_DO14->setEnabled(false);
	ui.m_DO15->setEnabled(false);
	
	ui.m_DOALL->setEnabled(false);

	connect(ui.m_DO0, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO1, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO2, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO3, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO4, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO5, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO6, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO7, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));

	connect(ui.m_DO8, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO9, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO10, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO11, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO12, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO13, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO14, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));
	connect(ui.m_DO15, SIGNAL(checkedChanged(bool)), this, SLOT(onDOChecked(bool)));

	connect(ui.m_DOALL, SIGNAL(checkedChanged(bool)),this,SLOT(onDOAllChecked(bool)));

	timer = new QTimer(this);
	connect(timer, SIGNAL(timeout()), this, SLOT(onTimeout()));
	timer->start(10);
}

dioTestPage::~dioTestPage()
{
}


bool dioTestPage::openDevice()
{
	bool ret = false;
//#ifdef Q_OS_WIN64
#if 0
#ifdef WIN64
	hDIO = GetModuleHandle(TEXT("./NKDIOLIBx64.dll"));
	if (hDIO == NULL)
	{
		hDIO = LoadLibrary(TEXT("./NKDIOLIBx64.dll"));
	}
#else ifdef WIN32
	hDIO = GetModuleHandle(TEXT("./NKDIOLIBx86.dll"));
	if (hDIO == NULL)
	{
		hDIO = LoadLibrary(TEXT("./NKDIOLIBx86.dll"));
	}
#endif
#endif

    //if (hDIO == NULL)
    //	return false;
    return true;
}

quint16 dioTestPage::getButtonStatus()
{
	return 0;
}
void dioTestPage::setLedStatus(quint16 status)
{

}

void dioTestPage::onTimeout()
{
	if (startFlag == 0)
	{

		ui.m_StartStopBtn->setText(tr("Start"));

		diValue = 0;
		ui.m_led0->turnOff();
		ui.m_led1->turnOff();
		ui.m_led2->turnOff();
		ui.m_led3->turnOff();
		ui.m_led4->turnOff();
		ui.m_led5->turnOff();
		ui.m_led6->turnOff();
		ui.m_led7->turnOff();
		ui.m_led8->turnOff();
		ui.m_led9->turnOff();
		ui.m_led10->turnOff();
		ui.m_led11->turnOff();
		ui.m_led12->turnOff();
		ui.m_led13->turnOff();
		ui.m_led14->turnOff();
		ui.m_led15->turnOff();

#if 0
		ui.m_DO0->setChecked(false);
		ui.m_DO1->setChecked(false);
		ui.m_DO2->setChecked(false);
		ui.m_DO3->setChecked(false);
		ui.m_DO4->setChecked(false);
		ui.m_DO5->setChecked(false);
		ui.m_DO6->setChecked(false);
		ui.m_DO7->setChecked(false);
		ui.m_DO8->setChecked(false);
		ui.m_DO9->setChecked(false);
		ui.m_DO10->setChecked(false);
		ui.m_DO11->setChecked(false);
		ui.m_DO12->setChecked(false);
		ui.m_DO13->setChecked(false);
		ui.m_DO14->setChecked(false);
		ui.m_DO15->setChecked(false);
#endif 
	}
	else
	{

		ui.m_StartStopBtn->setText(tr("Stop")); 

		//diValue = ~diValue;
        quint8 diByteValueL = 0x0;
        m_adapter->m_DIO_PollingReadDiByte(0,&diByteValueL);
        quint8 diByteValueH = 0x0;
        m_adapter->m_DIO_PollingReadDiByte(1,&diByteValueH);

		diValue = (diByteValueH << 8) + diByteValueL;

		if ((diValue & 0x01) == 0x01)
		{
			ui.m_led0->turnOn();
		}
		else
		{
			ui.m_led0->turnOff();
		}

		if ((diValue & 0x02) == 0x02)
		{
			ui.m_led1->turnOn();
		}
		else
		{
			ui.m_led1->turnOff();
		}

		if ((diValue & 0x04) == 0x04)
		{
			ui.m_led2->turnOn();
		}
		else
		{
			ui.m_led2->turnOff();
		}

		if ((diValue & 0x08) == 0x08)
		{
			//ui.label_DI3->setStyleSheet(QString("background-color:") + "green");
			ui.m_led3->turnOn();
		}
		else
		{
			//ui.label_DI3->setStyleSheet(QString("background-color:") + " ");
			ui.m_led3->turnOff();
		}

		if ((diValue & 0x10) == 0x10)
		{
			//ui.label_DI4->setStyleSheet(QString("background-color:") + "green");
			ui.m_led4->turnOn();
		}
		else
		{
			//ui.label_DI4->setStyleSheet(QString("background-color:") + " ");
			ui.m_led4->turnOff();
		}

		if ((diValue & 0x20) == 0x20)
		{
			ui.m_led5->turnOn();
		}
		else
		{
			ui.m_led5->turnOff();
		}

		if ((diValue & 0x40) == 0x40)
		{
			ui.m_led6->turnOn();
		}
		else
		{
			ui.m_led6->turnOff();
		}

		if ((diValue & 0x80) == 0x80)
		{
			ui.m_led7->turnOn();
		}
		else
		{
			ui.m_led7->turnOff();
		}

		if ((diValue & 0x0100) == 0x0100)
		{
			ui.m_led8->turnOn();
		}
		else
		{
			ui.m_led8->turnOff();
		}

		if ((diValue & 0x0200) == 0x0200)
		{
			ui.m_led9->turnOn();
		}
		else
		{
			ui.m_led9->turnOff();
		}

		if ((diValue & 0x0400) == 0x0400)
		{
			ui.m_led10->turnOn();
		}
		else
		{
			ui.m_led10->turnOff();
		}

		if ((diValue & 0x0800) == 0x0800)
		{
			ui.m_led11->turnOn();
		}
		else
		{
			ui.m_led11->turnOff();
		}

		if ((diValue & 0x1000) == 0x1000)
		{
			ui.m_led12->turnOn();
		}
		else
		{
			ui.m_led12->turnOff();
		}

		if ((diValue & 0x2000) == 0x2000)
		{
			ui.m_led13->turnOn();
		}
		else
		{
			ui.m_led13->turnOff();
		}

		if ((diValue & 0x4000) == 0x4000)
		{
			ui.m_led14->turnOn();
		}
		else
		{
			ui.m_led14->turnOff();
		}

		if ((diValue & 0x8000) == 0x8000)
		{
			ui.m_led15->turnOn();
		}
		else
		{
			ui.m_led15->turnOff();
		}
	}
}
void dioTestPage::onStartClicked()
{
	if (startFlag == 0)
	{
		startFlag = 1;
		ui.m_DO0->setEnabled(true);
		ui.m_DO1->setEnabled(true);
		ui.m_DO2->setEnabled(true);
		ui.m_DO3->setEnabled(true);

		ui.m_DO4->setEnabled(true);
		ui.m_DO5->setEnabled(true);
		ui.m_DO6->setEnabled(true);
		ui.m_DO7->setEnabled(true);

		ui.m_DO8->setEnabled(true);
		ui.m_DO9->setEnabled(true);
		ui.m_DO10->setEnabled(true);
		ui.m_DO11->setEnabled(true);

		ui.m_DO12->setEnabled(true);
		ui.m_DO13->setEnabled(true);
		ui.m_DO14->setEnabled(true);
		ui.m_DO15->setEnabled(true);
		ui.m_DOALL->setEnabled(true);
	}
	else
	{
		startFlag = 0;

		ui.m_DO0->setEnabled(false);
		ui.m_DO1->setEnabled(false);
		ui.m_DO2->setEnabled(false);
		ui.m_DO3->setEnabled(false);

		ui.m_DO4->setEnabled(false);
		ui.m_DO5->setEnabled(false);
		ui.m_DO6->setEnabled(false);
		ui.m_DO7->setEnabled(false);

		ui.m_DO8->setEnabled(false);
		ui.m_DO9->setEnabled(false);
		ui.m_DO10->setEnabled(false);
		ui.m_DO11->setEnabled(false);

		ui.m_DO12->setEnabled(false);
		ui.m_DO13->setEnabled(false);
		ui.m_DO14->setEnabled(false);
		ui.m_DO15->setEnabled(false);
		ui.m_DOALL->setEnabled(false);
	}
}
void dioTestPage::onDOChecked( bool checked)
{
	if (ui.m_DO0->getChecked())
	{
		doValue &= (~0x01);
	}
	else
	{
		doValue |= 0x01;
	}

	if (ui.m_DO1->getChecked())
	{
		doValue &= (~0x02);

	}
	else
	{
		doValue |= 0x02;
	}

	if (ui.m_DO2->getChecked())
	{
		doValue &= (~0x04);
	}
	else
	{
		doValue |= 0x04;

	}

	if (ui.m_DO3->getChecked())
	{
		doValue &= (~0x08);
	}
	else
	{
		doValue |= 0x08;

	}

	if (ui.m_DO4->getChecked())
	{
		doValue &= (~0x10);
	}
	else
	{

		doValue |= 0x10;
	}

	if (ui.m_DO5->getChecked())
	{
		doValue &= (~0x20);
	}
	else
	{
		doValue |= 0x20;

	}

	if (ui.m_DO6->getChecked())
	{
		doValue &= (~0x40);
	}
	else
	{
		doValue |= 0x40;

	}

	if (ui.m_DO7->getChecked())
	{
		doValue &= (~0x80);
	}
	else
	{
		doValue |= 0x80;

	}
	//
	if (ui.m_DO8->getChecked())
	{
		doValue &= (~0x0100);
	}
	else
	{
		doValue |= 0x0100;
	}

	if (ui.m_DO9->getChecked())
	{
		doValue &= (~0x0200);

	}
	else
	{
		doValue |= 0x0200;
	}

	if (ui.m_DO10->getChecked())
	{
		doValue &= (~0x0400);
	}
	else
	{
		doValue |= 0x0400;

	}

	if (ui.m_DO11->getChecked())
	{
		doValue &= (~0x0800);
	}
	else
	{
		doValue |= 0x0800;

	}

	if (ui.m_DO12->getChecked())
	{
		doValue &= (~0x1000);
	}
	else
	{

		doValue |= 0x1000;
	}

	if (ui.m_DO13->getChecked())
	{
		doValue &= (~0x2000);
	}
	else
	{
		doValue |= 0x2000;

	}

	if (ui.m_DO14->getChecked())
	{
		doValue &= (~0x4000);
	}
	else
	{
		doValue |= 0x4000;

	}

	if (ui.m_DO15->getChecked())
	{
		doValue &= (~0x8000);
	}
	else
	{
		doValue |= 0x8000;

	}

	if (startFlag == 1)
	{
        m_adapter->m_DIO_PollingWriteDoByte(0, (unsigned char)doValue);
        m_adapter->m_DIO_PollingWriteDoByte(1, (unsigned char)(doValue >> 8));
	}
}

void dioTestPage::onDOAllChecked(bool checked)
{
	if (checked)
	{
		ui.m_DO0->setChecked(true);
		ui.m_DO1->setChecked(true);
		ui.m_DO2->setChecked(true);
		ui.m_DO3->setChecked(true);
		ui.m_DO4->setChecked(true);
		ui.m_DO5->setChecked(true);
		ui.m_DO6->setChecked(true);
		ui.m_DO7->setChecked(true);
		ui.m_DO8->setChecked(true);
		ui.m_DO9->setChecked(true);
		ui.m_DO10->setChecked(true);
		ui.m_DO11->setChecked(true);
		ui.m_DO12->setChecked(true);
		ui.m_DO13->setChecked(true);
		ui.m_DO14->setChecked(true);
		ui.m_DO15->setChecked(true);
	}
	else
	{
		ui.m_DO0->setChecked(false);
		ui.m_DO1->setChecked(false);
		ui.m_DO2->setChecked(false);
		ui.m_DO3->setChecked(false);
		ui.m_DO4->setChecked(false);
		ui.m_DO5->setChecked(false);
		ui.m_DO6->setChecked(false);
		ui.m_DO7->setChecked(false);
		ui.m_DO8->setChecked(false);
		ui.m_DO9->setChecked(false);
		ui.m_DO10->setChecked(false);
		ui.m_DO11->setChecked(false);
		ui.m_DO12->setChecked(false);
		ui.m_DO13->setChecked(false);
		ui.m_DO14->setChecked(false);
		ui.m_DO15->setChecked(false);
	}

}
