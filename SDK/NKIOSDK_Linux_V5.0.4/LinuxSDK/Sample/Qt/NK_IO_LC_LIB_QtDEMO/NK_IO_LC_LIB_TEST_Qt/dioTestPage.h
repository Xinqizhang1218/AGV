#pragma once

//#include <windows.h>
#include <QWidget>
#include <qlabel.h>
#include "ui_dioTestPage.h"
#include "switchButton.h"
#include "ledWidget.h"
#include "dioLcAdapter.h"


class dioTestPage : public QWidget
{
	Q_OBJECT

public:
	dioTestPage(CDioLcAdapter * adapter, QWidget *parent = Q_NULLPTR);
	~dioTestPage();


protected slots:
	void onTimeout();
	void onStartClicked();
	void onDOChecked(bool);
	void onDOAllChecked(bool);

private:

	bool openDevice();
	quint16 getButtonStatus();
	void setLedStatus(quint16 status);
private:
	Ui::dioTestPage ui;
	
	
    //HMODULE          hDIO;
	bool             m_bLoaded;

	quint16 diValue;
	quint16 doValue;

	quint32 startFlag;
	QTimer *timer;

	CDioLcAdapter *m_adapter;
	


};
