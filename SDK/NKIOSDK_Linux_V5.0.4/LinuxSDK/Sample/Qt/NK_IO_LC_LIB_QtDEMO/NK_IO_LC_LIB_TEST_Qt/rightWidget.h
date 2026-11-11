#pragma once

#include <QWidget>
#include <QStackedLayout>
#include"dioTestPage.h"
#include "lightControlPage.h"




//#include "ui_rightWidget.h"

class rightWidget : public QWidget
{
	Q_OBJECT

public:
	rightWidget(CDioLcAdapter *adapter, QWidget *parent = Q_NULLPTR);
	~rightWidget();
	QStackedLayout *m_layout;

protected:
	void paintEvent(QPaintEvent *);
private:
	//Ui::rightWidget ui;

	dioTestPage *m_dioTestPage;
	lightControlPage *m_lightControlPage;


	CDioLcAdapter *m_adapter;
	
};
