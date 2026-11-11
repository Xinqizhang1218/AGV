/********************************************************************************
** Form generated from reading UI file 'dioTestPage.ui'
**
** Created by: Qt User Interface Compiler version 5.13.2
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_DIOTESTPAGE_H
#define UI_DIOTESTPAGE_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QGridLayout>
#include <QtWidgets/QGroupBox>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QLabel>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QSpacerItem>
#include <QtWidgets/QVBoxLayout>
#include <QtWidgets/QWidget>
#include "ledWidget.h"
#include "switchButton.h"

QT_BEGIN_NAMESPACE

class Ui_dioTestPage
{
public:
    QVBoxLayout *verticalLayout;
    QHBoxLayout *horizontalLayout;
    QPushButton *m_StartStopBtn;
    QSpacerItem *horizontalSpacer;
    QGroupBox *groupBoxDI;
    QGridLayout *gridLayout;
    QVBoxLayout *verticalLayout_2;
    ledWidget *m_led0;
    QLabel *m_led0Label;
    QVBoxLayout *verticalLayout_3;
    ledWidget *m_led1;
    QLabel *m_led1Label;
    QVBoxLayout *verticalLayout_4;
    ledWidget *m_led2;
    QLabel *m_led2Label;
    QVBoxLayout *verticalLayout_5;
    ledWidget *m_led3;
    QLabel *m_led3Label;
    QVBoxLayout *verticalLayout_6;
    ledWidget *m_led4;
    QLabel *m_led4Label;
    QVBoxLayout *verticalLayout_7;
    ledWidget *m_led5;
    QLabel *m_led5Label;
    QVBoxLayout *verticalLayout_8;
    ledWidget *m_led6;
    QLabel *m_led6Label;
    QVBoxLayout *verticalLayout_9;
    ledWidget *m_led7;
    QLabel *m_led7Label;
    QVBoxLayout *verticalLayout_10;
    ledWidget *m_led8;
    QLabel *m_led8Label;
    QVBoxLayout *verticalLayout_11;
    ledWidget *m_led9;
    QLabel *m_led9Label;
    QVBoxLayout *verticalLayout_12;
    ledWidget *m_led10;
    QLabel *m_led10Label;
    QVBoxLayout *verticalLayout_13;
    ledWidget *m_led11;
    QLabel *m_led11Label;
    QVBoxLayout *verticalLayout_14;
    ledWidget *m_led12;
    QLabel *m_led12Label;
    QVBoxLayout *verticalLayout_15;
    ledWidget *m_led13;
    QLabel *m_led13Label;
    QVBoxLayout *verticalLayout_16;
    ledWidget *m_led14;
    QLabel *m_led14Label;
    QVBoxLayout *verticalLayout_17;
    ledWidget *m_led15;
    QLabel *m_led15Label;
    QGroupBox *groupBoxDO;
    QGridLayout *gridLayout_2;
    QVBoxLayout *verticalLayout_18;
    switchButton *m_DO0;
    QLabel *m_DO0Label;
    QVBoxLayout *verticalLayout_19;
    switchButton *m_DO1;
    QLabel *m_DO1Label;
    QVBoxLayout *verticalLayout_20;
    switchButton *m_DO2;
    QLabel *m_DO2Label;
    QVBoxLayout *verticalLayout_21;
    switchButton *m_DO3;
    QLabel *m_DO3Label;
    QVBoxLayout *verticalLayout_22;
    switchButton *m_DO4;
    QLabel *m_DO4Label;
    QVBoxLayout *verticalLayout_23;
    switchButton *m_DO5;
    QLabel *m_DO5Label;
    QVBoxLayout *verticalLayout_24;
    switchButton *m_DO6;
    QLabel *m_DO6Label;
    QVBoxLayout *verticalLayout_25;
    switchButton *m_DO7;
    QLabel *m_DO7Label;
    QVBoxLayout *verticalLayout_26;
    switchButton *m_DO8;
    QLabel *m_DO8Label;
    QVBoxLayout *verticalLayout_27;
    switchButton *m_DO9;
    QLabel *m_DO9Label;
    QVBoxLayout *verticalLayout_28;
    switchButton *m_DO10;
    QLabel *m_DO10Label;
    QVBoxLayout *verticalLayout_29;
    switchButton *m_DO11;
    QLabel *m_DO11Label;
    QVBoxLayout *verticalLayout_30;
    switchButton *m_DO12;
    QLabel *m_DO12Label;
    QVBoxLayout *verticalLayout_31;
    switchButton *m_DO13;
    QLabel *m_DO13Label;
    QVBoxLayout *verticalLayout_32;
    switchButton *m_DO14;
    QLabel *m_DO14Label;
    QVBoxLayout *verticalLayout_33;
    switchButton *m_DO15;
    QLabel *m_DO15Label;
    QVBoxLayout *verticalLayout_34;
    switchButton *m_DOALL;
    QLabel *m_DOAllLabel;
    QSpacerItem *horizontalSpacer_2;
    QGroupBox *groupBox;

    void setupUi(QWidget *dioTestPage)
    {
        if (dioTestPage->objectName().isEmpty())
            dioTestPage->setObjectName(QString::fromUtf8("dioTestPage"));
        dioTestPage->resize(830, 604);
        verticalLayout = new QVBoxLayout(dioTestPage);
        verticalLayout->setSpacing(6);
        verticalLayout->setContentsMargins(11, 11, 11, 11);
        verticalLayout->setObjectName(QString::fromUtf8("verticalLayout"));
        horizontalLayout = new QHBoxLayout();
        horizontalLayout->setSpacing(6);
        horizontalLayout->setObjectName(QString::fromUtf8("horizontalLayout"));
        m_StartStopBtn = new QPushButton(dioTestPage);
        m_StartStopBtn->setObjectName(QString::fromUtf8("m_StartStopBtn"));

        horizontalLayout->addWidget(m_StartStopBtn);

        horizontalSpacer = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout->addItem(horizontalSpacer);


        verticalLayout->addLayout(horizontalLayout);

        groupBoxDI = new QGroupBox(dioTestPage);
        groupBoxDI->setObjectName(QString::fromUtf8("groupBoxDI"));
        gridLayout = new QGridLayout(groupBoxDI);
        gridLayout->setSpacing(6);
        gridLayout->setContentsMargins(11, 11, 11, 11);
        gridLayout->setObjectName(QString::fromUtf8("gridLayout"));
        gridLayout->setHorizontalSpacing(10);
        verticalLayout_2 = new QVBoxLayout();
        verticalLayout_2->setSpacing(6);
        verticalLayout_2->setObjectName(QString::fromUtf8("verticalLayout_2"));
        m_led0 = new ledWidget(groupBoxDI);
        m_led0->setObjectName(QString::fromUtf8("m_led0"));
        m_led0->setMinimumSize(QSize(20, 20));

        verticalLayout_2->addWidget(m_led0);

        m_led0Label = new QLabel(groupBoxDI);
        m_led0Label->setObjectName(QString::fromUtf8("m_led0Label"));
        m_led0Label->setMinimumSize(QSize(20, 20));
        m_led0Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_2->addWidget(m_led0Label);


        gridLayout->addLayout(verticalLayout_2, 0, 0, 1, 1);

        verticalLayout_3 = new QVBoxLayout();
        verticalLayout_3->setSpacing(6);
        verticalLayout_3->setObjectName(QString::fromUtf8("verticalLayout_3"));
        m_led1 = new ledWidget(groupBoxDI);
        m_led1->setObjectName(QString::fromUtf8("m_led1"));
        m_led1->setMinimumSize(QSize(20, 20));

        verticalLayout_3->addWidget(m_led1);

        m_led1Label = new QLabel(groupBoxDI);
        m_led1Label->setObjectName(QString::fromUtf8("m_led1Label"));
        m_led1Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_3->addWidget(m_led1Label);


        gridLayout->addLayout(verticalLayout_3, 0, 1, 1, 1);

        verticalLayout_4 = new QVBoxLayout();
        verticalLayout_4->setSpacing(6);
        verticalLayout_4->setObjectName(QString::fromUtf8("verticalLayout_4"));
        m_led2 = new ledWidget(groupBoxDI);
        m_led2->setObjectName(QString::fromUtf8("m_led2"));
        m_led2->setMinimumSize(QSize(20, 20));

        verticalLayout_4->addWidget(m_led2);

        m_led2Label = new QLabel(groupBoxDI);
        m_led2Label->setObjectName(QString::fromUtf8("m_led2Label"));
        m_led2Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_4->addWidget(m_led2Label);


        gridLayout->addLayout(verticalLayout_4, 0, 2, 1, 1);

        verticalLayout_5 = new QVBoxLayout();
        verticalLayout_5->setSpacing(6);
        verticalLayout_5->setObjectName(QString::fromUtf8("verticalLayout_5"));
        m_led3 = new ledWidget(groupBoxDI);
        m_led3->setObjectName(QString::fromUtf8("m_led3"));
        m_led3->setMinimumSize(QSize(20, 20));

        verticalLayout_5->addWidget(m_led3);

        m_led3Label = new QLabel(groupBoxDI);
        m_led3Label->setObjectName(QString::fromUtf8("m_led3Label"));
        m_led3Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_5->addWidget(m_led3Label);


        gridLayout->addLayout(verticalLayout_5, 0, 3, 1, 1);

        verticalLayout_6 = new QVBoxLayout();
        verticalLayout_6->setSpacing(6);
        verticalLayout_6->setObjectName(QString::fromUtf8("verticalLayout_6"));
        m_led4 = new ledWidget(groupBoxDI);
        m_led4->setObjectName(QString::fromUtf8("m_led4"));
        m_led4->setMinimumSize(QSize(20, 20));

        verticalLayout_6->addWidget(m_led4);

        m_led4Label = new QLabel(groupBoxDI);
        m_led4Label->setObjectName(QString::fromUtf8("m_led4Label"));
        m_led4Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_6->addWidget(m_led4Label);


        gridLayout->addLayout(verticalLayout_6, 0, 4, 1, 1);

        verticalLayout_7 = new QVBoxLayout();
        verticalLayout_7->setSpacing(6);
        verticalLayout_7->setObjectName(QString::fromUtf8("verticalLayout_7"));
        m_led5 = new ledWidget(groupBoxDI);
        m_led5->setObjectName(QString::fromUtf8("m_led5"));
        m_led5->setMinimumSize(QSize(20, 20));

        verticalLayout_7->addWidget(m_led5);

        m_led5Label = new QLabel(groupBoxDI);
        m_led5Label->setObjectName(QString::fromUtf8("m_led5Label"));
        m_led5Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_7->addWidget(m_led5Label);


        gridLayout->addLayout(verticalLayout_7, 0, 5, 1, 1);

        verticalLayout_8 = new QVBoxLayout();
        verticalLayout_8->setSpacing(6);
        verticalLayout_8->setObjectName(QString::fromUtf8("verticalLayout_8"));
        m_led6 = new ledWidget(groupBoxDI);
        m_led6->setObjectName(QString::fromUtf8("m_led6"));
        m_led6->setMinimumSize(QSize(20, 20));

        verticalLayout_8->addWidget(m_led6);

        m_led6Label = new QLabel(groupBoxDI);
        m_led6Label->setObjectName(QString::fromUtf8("m_led6Label"));
        m_led6Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_8->addWidget(m_led6Label);


        gridLayout->addLayout(verticalLayout_8, 0, 6, 1, 1);

        verticalLayout_9 = new QVBoxLayout();
        verticalLayout_9->setSpacing(6);
        verticalLayout_9->setObjectName(QString::fromUtf8("verticalLayout_9"));
        m_led7 = new ledWidget(groupBoxDI);
        m_led7->setObjectName(QString::fromUtf8("m_led7"));
        m_led7->setMinimumSize(QSize(20, 20));

        verticalLayout_9->addWidget(m_led7);

        m_led7Label = new QLabel(groupBoxDI);
        m_led7Label->setObjectName(QString::fromUtf8("m_led7Label"));
        m_led7Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_9->addWidget(m_led7Label);


        gridLayout->addLayout(verticalLayout_9, 0, 7, 1, 1);

        verticalLayout_10 = new QVBoxLayout();
        verticalLayout_10->setSpacing(6);
        verticalLayout_10->setObjectName(QString::fromUtf8("verticalLayout_10"));
        m_led8 = new ledWidget(groupBoxDI);
        m_led8->setObjectName(QString::fromUtf8("m_led8"));
        m_led8->setMinimumSize(QSize(20, 20));

        verticalLayout_10->addWidget(m_led8);

        m_led8Label = new QLabel(groupBoxDI);
        m_led8Label->setObjectName(QString::fromUtf8("m_led8Label"));
        m_led8Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_10->addWidget(m_led8Label);


        gridLayout->addLayout(verticalLayout_10, 1, 0, 1, 1);

        verticalLayout_11 = new QVBoxLayout();
        verticalLayout_11->setSpacing(6);
        verticalLayout_11->setObjectName(QString::fromUtf8("verticalLayout_11"));
        m_led9 = new ledWidget(groupBoxDI);
        m_led9->setObjectName(QString::fromUtf8("m_led9"));
        m_led9->setMinimumSize(QSize(20, 20));

        verticalLayout_11->addWidget(m_led9);

        m_led9Label = new QLabel(groupBoxDI);
        m_led9Label->setObjectName(QString::fromUtf8("m_led9Label"));
        m_led9Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_11->addWidget(m_led9Label);


        gridLayout->addLayout(verticalLayout_11, 1, 1, 1, 1);

        verticalLayout_12 = new QVBoxLayout();
        verticalLayout_12->setSpacing(6);
        verticalLayout_12->setObjectName(QString::fromUtf8("verticalLayout_12"));
        m_led10 = new ledWidget(groupBoxDI);
        m_led10->setObjectName(QString::fromUtf8("m_led10"));
        m_led10->setMinimumSize(QSize(20, 20));

        verticalLayout_12->addWidget(m_led10);

        m_led10Label = new QLabel(groupBoxDI);
        m_led10Label->setObjectName(QString::fromUtf8("m_led10Label"));
        m_led10Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_12->addWidget(m_led10Label);


        gridLayout->addLayout(verticalLayout_12, 1, 2, 1, 1);

        verticalLayout_13 = new QVBoxLayout();
        verticalLayout_13->setSpacing(6);
        verticalLayout_13->setObjectName(QString::fromUtf8("verticalLayout_13"));
        m_led11 = new ledWidget(groupBoxDI);
        m_led11->setObjectName(QString::fromUtf8("m_led11"));
        m_led11->setMinimumSize(QSize(20, 20));

        verticalLayout_13->addWidget(m_led11);

        m_led11Label = new QLabel(groupBoxDI);
        m_led11Label->setObjectName(QString::fromUtf8("m_led11Label"));
        m_led11Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_13->addWidget(m_led11Label);


        gridLayout->addLayout(verticalLayout_13, 1, 3, 1, 1);

        verticalLayout_14 = new QVBoxLayout();
        verticalLayout_14->setSpacing(6);
        verticalLayout_14->setObjectName(QString::fromUtf8("verticalLayout_14"));
        m_led12 = new ledWidget(groupBoxDI);
        m_led12->setObjectName(QString::fromUtf8("m_led12"));
        m_led12->setMinimumSize(QSize(20, 20));

        verticalLayout_14->addWidget(m_led12);

        m_led12Label = new QLabel(groupBoxDI);
        m_led12Label->setObjectName(QString::fromUtf8("m_led12Label"));
        m_led12Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_14->addWidget(m_led12Label);


        gridLayout->addLayout(verticalLayout_14, 1, 4, 1, 1);

        verticalLayout_15 = new QVBoxLayout();
        verticalLayout_15->setSpacing(6);
        verticalLayout_15->setObjectName(QString::fromUtf8("verticalLayout_15"));
        m_led13 = new ledWidget(groupBoxDI);
        m_led13->setObjectName(QString::fromUtf8("m_led13"));
        m_led13->setMinimumSize(QSize(20, 20));

        verticalLayout_15->addWidget(m_led13);

        m_led13Label = new QLabel(groupBoxDI);
        m_led13Label->setObjectName(QString::fromUtf8("m_led13Label"));
        m_led13Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_15->addWidget(m_led13Label);


        gridLayout->addLayout(verticalLayout_15, 1, 5, 1, 1);

        verticalLayout_16 = new QVBoxLayout();
        verticalLayout_16->setSpacing(6);
        verticalLayout_16->setObjectName(QString::fromUtf8("verticalLayout_16"));
        m_led14 = new ledWidget(groupBoxDI);
        m_led14->setObjectName(QString::fromUtf8("m_led14"));
        m_led14->setMinimumSize(QSize(20, 20));

        verticalLayout_16->addWidget(m_led14);

        m_led14Label = new QLabel(groupBoxDI);
        m_led14Label->setObjectName(QString::fromUtf8("m_led14Label"));
        m_led14Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_16->addWidget(m_led14Label);


        gridLayout->addLayout(verticalLayout_16, 1, 6, 1, 1);

        verticalLayout_17 = new QVBoxLayout();
        verticalLayout_17->setSpacing(6);
        verticalLayout_17->setObjectName(QString::fromUtf8("verticalLayout_17"));
        m_led15 = new ledWidget(groupBoxDI);
        m_led15->setObjectName(QString::fromUtf8("m_led15"));
        m_led15->setMinimumSize(QSize(20, 20));

        verticalLayout_17->addWidget(m_led15);

        m_led15Label = new QLabel(groupBoxDI);
        m_led15Label->setObjectName(QString::fromUtf8("m_led15Label"));
        m_led15Label->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignVCenter);

        verticalLayout_17->addWidget(m_led15Label);


        gridLayout->addLayout(verticalLayout_17, 1, 7, 1, 1);


        verticalLayout->addWidget(groupBoxDI);

        groupBoxDO = new QGroupBox(dioTestPage);
        groupBoxDO->setObjectName(QString::fromUtf8("groupBoxDO"));
        gridLayout_2 = new QGridLayout(groupBoxDO);
        gridLayout_2->setSpacing(6);
        gridLayout_2->setContentsMargins(11, 11, 11, 11);
        gridLayout_2->setObjectName(QString::fromUtf8("gridLayout_2"));
        gridLayout_2->setHorizontalSpacing(10);
        verticalLayout_18 = new QVBoxLayout();
        verticalLayout_18->setSpacing(6);
        verticalLayout_18->setObjectName(QString::fromUtf8("verticalLayout_18"));
        m_DO0 = new switchButton(groupBoxDO);
        m_DO0->setObjectName(QString::fromUtf8("m_DO0"));
        m_DO0->setMinimumSize(QSize(20, 10));

        verticalLayout_18->addWidget(m_DO0);

        m_DO0Label = new QLabel(groupBoxDO);
        m_DO0Label->setObjectName(QString::fromUtf8("m_DO0Label"));
        m_DO0Label->setAlignment(Qt::AlignCenter);

        verticalLayout_18->addWidget(m_DO0Label);


        gridLayout_2->addLayout(verticalLayout_18, 0, 0, 1, 1);

        verticalLayout_19 = new QVBoxLayout();
        verticalLayout_19->setSpacing(6);
        verticalLayout_19->setObjectName(QString::fromUtf8("verticalLayout_19"));
        m_DO1 = new switchButton(groupBoxDO);
        m_DO1->setObjectName(QString::fromUtf8("m_DO1"));
        m_DO1->setMinimumSize(QSize(20, 10));

        verticalLayout_19->addWidget(m_DO1);

        m_DO1Label = new QLabel(groupBoxDO);
        m_DO1Label->setObjectName(QString::fromUtf8("m_DO1Label"));
        m_DO1Label->setAlignment(Qt::AlignCenter);

        verticalLayout_19->addWidget(m_DO1Label);


        gridLayout_2->addLayout(verticalLayout_19, 0, 1, 1, 1);

        verticalLayout_20 = new QVBoxLayout();
        verticalLayout_20->setSpacing(6);
        verticalLayout_20->setObjectName(QString::fromUtf8("verticalLayout_20"));
        m_DO2 = new switchButton(groupBoxDO);
        m_DO2->setObjectName(QString::fromUtf8("m_DO2"));
        m_DO2->setMinimumSize(QSize(20, 10));

        verticalLayout_20->addWidget(m_DO2);

        m_DO2Label = new QLabel(groupBoxDO);
        m_DO2Label->setObjectName(QString::fromUtf8("m_DO2Label"));
        m_DO2Label->setAlignment(Qt::AlignCenter);

        verticalLayout_20->addWidget(m_DO2Label);


        gridLayout_2->addLayout(verticalLayout_20, 0, 2, 1, 1);

        verticalLayout_21 = new QVBoxLayout();
        verticalLayout_21->setSpacing(6);
        verticalLayout_21->setObjectName(QString::fromUtf8("verticalLayout_21"));
        m_DO3 = new switchButton(groupBoxDO);
        m_DO3->setObjectName(QString::fromUtf8("m_DO3"));
        m_DO3->setMinimumSize(QSize(20, 10));

        verticalLayout_21->addWidget(m_DO3);

        m_DO3Label = new QLabel(groupBoxDO);
        m_DO3Label->setObjectName(QString::fromUtf8("m_DO3Label"));
        m_DO3Label->setAlignment(Qt::AlignCenter);

        verticalLayout_21->addWidget(m_DO3Label);


        gridLayout_2->addLayout(verticalLayout_21, 0, 3, 1, 1);

        verticalLayout_22 = new QVBoxLayout();
        verticalLayout_22->setSpacing(6);
        verticalLayout_22->setObjectName(QString::fromUtf8("verticalLayout_22"));
        m_DO4 = new switchButton(groupBoxDO);
        m_DO4->setObjectName(QString::fromUtf8("m_DO4"));
        m_DO4->setMinimumSize(QSize(20, 10));

        verticalLayout_22->addWidget(m_DO4);

        m_DO4Label = new QLabel(groupBoxDO);
        m_DO4Label->setObjectName(QString::fromUtf8("m_DO4Label"));
        m_DO4Label->setAlignment(Qt::AlignCenter);

        verticalLayout_22->addWidget(m_DO4Label);


        gridLayout_2->addLayout(verticalLayout_22, 0, 4, 1, 1);

        verticalLayout_23 = new QVBoxLayout();
        verticalLayout_23->setSpacing(6);
        verticalLayout_23->setObjectName(QString::fromUtf8("verticalLayout_23"));
        m_DO5 = new switchButton(groupBoxDO);
        m_DO5->setObjectName(QString::fromUtf8("m_DO5"));
        m_DO5->setMinimumSize(QSize(20, 10));

        verticalLayout_23->addWidget(m_DO5);

        m_DO5Label = new QLabel(groupBoxDO);
        m_DO5Label->setObjectName(QString::fromUtf8("m_DO5Label"));
        m_DO5Label->setAlignment(Qt::AlignCenter);

        verticalLayout_23->addWidget(m_DO5Label);


        gridLayout_2->addLayout(verticalLayout_23, 0, 5, 1, 1);

        verticalLayout_24 = new QVBoxLayout();
        verticalLayout_24->setSpacing(6);
        verticalLayout_24->setObjectName(QString::fromUtf8("verticalLayout_24"));
        m_DO6 = new switchButton(groupBoxDO);
        m_DO6->setObjectName(QString::fromUtf8("m_DO6"));
        m_DO6->setMinimumSize(QSize(20, 10));

        verticalLayout_24->addWidget(m_DO6);

        m_DO6Label = new QLabel(groupBoxDO);
        m_DO6Label->setObjectName(QString::fromUtf8("m_DO6Label"));
        m_DO6Label->setAlignment(Qt::AlignCenter);

        verticalLayout_24->addWidget(m_DO6Label);


        gridLayout_2->addLayout(verticalLayout_24, 0, 6, 1, 1);

        verticalLayout_25 = new QVBoxLayout();
        verticalLayout_25->setSpacing(6);
        verticalLayout_25->setObjectName(QString::fromUtf8("verticalLayout_25"));
        m_DO7 = new switchButton(groupBoxDO);
        m_DO7->setObjectName(QString::fromUtf8("m_DO7"));
        m_DO7->setMinimumSize(QSize(20, 10));

        verticalLayout_25->addWidget(m_DO7);

        m_DO7Label = new QLabel(groupBoxDO);
        m_DO7Label->setObjectName(QString::fromUtf8("m_DO7Label"));
        m_DO7Label->setAlignment(Qt::AlignCenter);

        verticalLayout_25->addWidget(m_DO7Label);


        gridLayout_2->addLayout(verticalLayout_25, 0, 7, 1, 1);

        verticalLayout_26 = new QVBoxLayout();
        verticalLayout_26->setSpacing(6);
        verticalLayout_26->setObjectName(QString::fromUtf8("verticalLayout_26"));
        m_DO8 = new switchButton(groupBoxDO);
        m_DO8->setObjectName(QString::fromUtf8("m_DO8"));
        m_DO8->setMinimumSize(QSize(20, 10));

        verticalLayout_26->addWidget(m_DO8);

        m_DO8Label = new QLabel(groupBoxDO);
        m_DO8Label->setObjectName(QString::fromUtf8("m_DO8Label"));
        m_DO8Label->setAlignment(Qt::AlignCenter);

        verticalLayout_26->addWidget(m_DO8Label);


        gridLayout_2->addLayout(verticalLayout_26, 1, 0, 1, 1);

        verticalLayout_27 = new QVBoxLayout();
        verticalLayout_27->setSpacing(6);
        verticalLayout_27->setObjectName(QString::fromUtf8("verticalLayout_27"));
        m_DO9 = new switchButton(groupBoxDO);
        m_DO9->setObjectName(QString::fromUtf8("m_DO9"));
        m_DO9->setMinimumSize(QSize(20, 10));

        verticalLayout_27->addWidget(m_DO9);

        m_DO9Label = new QLabel(groupBoxDO);
        m_DO9Label->setObjectName(QString::fromUtf8("m_DO9Label"));
        m_DO9Label->setAlignment(Qt::AlignCenter);

        verticalLayout_27->addWidget(m_DO9Label);


        gridLayout_2->addLayout(verticalLayout_27, 1, 1, 1, 1);

        verticalLayout_28 = new QVBoxLayout();
        verticalLayout_28->setSpacing(6);
        verticalLayout_28->setObjectName(QString::fromUtf8("verticalLayout_28"));
        m_DO10 = new switchButton(groupBoxDO);
        m_DO10->setObjectName(QString::fromUtf8("m_DO10"));
        m_DO10->setMinimumSize(QSize(20, 10));

        verticalLayout_28->addWidget(m_DO10);

        m_DO10Label = new QLabel(groupBoxDO);
        m_DO10Label->setObjectName(QString::fromUtf8("m_DO10Label"));
        m_DO10Label->setAlignment(Qt::AlignCenter);

        verticalLayout_28->addWidget(m_DO10Label);


        gridLayout_2->addLayout(verticalLayout_28, 1, 2, 1, 1);

        verticalLayout_29 = new QVBoxLayout();
        verticalLayout_29->setSpacing(6);
        verticalLayout_29->setObjectName(QString::fromUtf8("verticalLayout_29"));
        m_DO11 = new switchButton(groupBoxDO);
        m_DO11->setObjectName(QString::fromUtf8("m_DO11"));
        m_DO11->setMinimumSize(QSize(20, 10));

        verticalLayout_29->addWidget(m_DO11);

        m_DO11Label = new QLabel(groupBoxDO);
        m_DO11Label->setObjectName(QString::fromUtf8("m_DO11Label"));
        m_DO11Label->setAlignment(Qt::AlignCenter);

        verticalLayout_29->addWidget(m_DO11Label);


        gridLayout_2->addLayout(verticalLayout_29, 1, 3, 1, 1);

        verticalLayout_30 = new QVBoxLayout();
        verticalLayout_30->setSpacing(6);
        verticalLayout_30->setObjectName(QString::fromUtf8("verticalLayout_30"));
        m_DO12 = new switchButton(groupBoxDO);
        m_DO12->setObjectName(QString::fromUtf8("m_DO12"));
        m_DO12->setMinimumSize(QSize(20, 10));

        verticalLayout_30->addWidget(m_DO12);

        m_DO12Label = new QLabel(groupBoxDO);
        m_DO12Label->setObjectName(QString::fromUtf8("m_DO12Label"));
        m_DO12Label->setAlignment(Qt::AlignCenter);

        verticalLayout_30->addWidget(m_DO12Label);


        gridLayout_2->addLayout(verticalLayout_30, 1, 4, 1, 1);

        verticalLayout_31 = new QVBoxLayout();
        verticalLayout_31->setSpacing(6);
        verticalLayout_31->setObjectName(QString::fromUtf8("verticalLayout_31"));
        m_DO13 = new switchButton(groupBoxDO);
        m_DO13->setObjectName(QString::fromUtf8("m_DO13"));
        m_DO13->setMinimumSize(QSize(20, 10));

        verticalLayout_31->addWidget(m_DO13);

        m_DO13Label = new QLabel(groupBoxDO);
        m_DO13Label->setObjectName(QString::fromUtf8("m_DO13Label"));
        m_DO13Label->setAlignment(Qt::AlignCenter);

        verticalLayout_31->addWidget(m_DO13Label);


        gridLayout_2->addLayout(verticalLayout_31, 1, 5, 1, 1);

        verticalLayout_32 = new QVBoxLayout();
        verticalLayout_32->setSpacing(6);
        verticalLayout_32->setObjectName(QString::fromUtf8("verticalLayout_32"));
        m_DO14 = new switchButton(groupBoxDO);
        m_DO14->setObjectName(QString::fromUtf8("m_DO14"));
        m_DO14->setMinimumSize(QSize(20, 10));

        verticalLayout_32->addWidget(m_DO14);

        m_DO14Label = new QLabel(groupBoxDO);
        m_DO14Label->setObjectName(QString::fromUtf8("m_DO14Label"));
        m_DO14Label->setAlignment(Qt::AlignCenter);

        verticalLayout_32->addWidget(m_DO14Label);


        gridLayout_2->addLayout(verticalLayout_32, 1, 6, 1, 1);

        verticalLayout_33 = new QVBoxLayout();
        verticalLayout_33->setSpacing(6);
        verticalLayout_33->setObjectName(QString::fromUtf8("verticalLayout_33"));
        m_DO15 = new switchButton(groupBoxDO);
        m_DO15->setObjectName(QString::fromUtf8("m_DO15"));
        m_DO15->setMinimumSize(QSize(20, 10));

        verticalLayout_33->addWidget(m_DO15);

        m_DO15Label = new QLabel(groupBoxDO);
        m_DO15Label->setObjectName(QString::fromUtf8("m_DO15Label"));
        m_DO15Label->setAlignment(Qt::AlignCenter);

        verticalLayout_33->addWidget(m_DO15Label);


        gridLayout_2->addLayout(verticalLayout_33, 1, 7, 1, 1);

        verticalLayout_34 = new QVBoxLayout();
        verticalLayout_34->setSpacing(6);
        verticalLayout_34->setObjectName(QString::fromUtf8("verticalLayout_34"));
        m_DOALL = new switchButton(groupBoxDO);
        m_DOALL->setObjectName(QString::fromUtf8("m_DOALL"));
        m_DOALL->setMinimumSize(QSize(20, 10));

        verticalLayout_34->addWidget(m_DOALL);

        m_DOAllLabel = new QLabel(groupBoxDO);
        m_DOAllLabel->setObjectName(QString::fromUtf8("m_DOAllLabel"));
        m_DOAllLabel->setAlignment(Qt::AlignCenter);

        verticalLayout_34->addWidget(m_DOAllLabel);


        gridLayout_2->addLayout(verticalLayout_34, 2, 0, 1, 1);

        horizontalSpacer_2 = new QSpacerItem(188, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        gridLayout_2->addItem(horizontalSpacer_2, 2, 1, 1, 2);


        verticalLayout->addWidget(groupBoxDO);

        groupBox = new QGroupBox(dioTestPage);
        groupBox->setObjectName(QString::fromUtf8("groupBox"));

        verticalLayout->addWidget(groupBox);


        retranslateUi(dioTestPage);

        QMetaObject::connectSlotsByName(dioTestPage);
    } // setupUi

    void retranslateUi(QWidget *dioTestPage)
    {
        dioTestPage->setWindowTitle(QCoreApplication::translate("dioTestPage", "dioTestPage", nullptr));
        m_StartStopBtn->setText(QCoreApplication::translate("dioTestPage", "Start", nullptr));
        groupBoxDI->setTitle(QCoreApplication::translate("dioTestPage", "DI", nullptr));
        m_led0Label->setText(QCoreApplication::translate("dioTestPage", "DI_0", nullptr));
        m_led1Label->setText(QCoreApplication::translate("dioTestPage", "DI_1", nullptr));
        m_led2Label->setText(QCoreApplication::translate("dioTestPage", "DI_2", nullptr));
        m_led3Label->setText(QCoreApplication::translate("dioTestPage", "DI_3", nullptr));
        m_led4Label->setText(QCoreApplication::translate("dioTestPage", "DI_4", nullptr));
        m_led5Label->setText(QCoreApplication::translate("dioTestPage", "DI_5", nullptr));
        m_led6Label->setText(QCoreApplication::translate("dioTestPage", "DI_6", nullptr));
        m_led7Label->setText(QCoreApplication::translate("dioTestPage", "DI_7", nullptr));
        m_led8Label->setText(QCoreApplication::translate("dioTestPage", "DI_8", nullptr));
        m_led9Label->setText(QCoreApplication::translate("dioTestPage", "DI_9", nullptr));
        m_led10Label->setText(QCoreApplication::translate("dioTestPage", "DI_10", nullptr));
        m_led11Label->setText(QCoreApplication::translate("dioTestPage", "DI_11", nullptr));
        m_led12Label->setText(QCoreApplication::translate("dioTestPage", "DI_12", nullptr));
        m_led13Label->setText(QCoreApplication::translate("dioTestPage", "DI_13", nullptr));
        m_led14Label->setText(QCoreApplication::translate("dioTestPage", "DI_14", nullptr));
        m_led15Label->setText(QCoreApplication::translate("dioTestPage", "DI_15", nullptr));
        groupBoxDO->setTitle(QCoreApplication::translate("dioTestPage", "DO", nullptr));
        m_DO0Label->setText(QCoreApplication::translate("dioTestPage", "DO_0", nullptr));
        m_DO1Label->setText(QCoreApplication::translate("dioTestPage", "DO_1", nullptr));
        m_DO2Label->setText(QCoreApplication::translate("dioTestPage", "DO_2", nullptr));
        m_DO3Label->setText(QCoreApplication::translate("dioTestPage", "DO_3", nullptr));
        m_DO4Label->setText(QCoreApplication::translate("dioTestPage", "DO_4", nullptr));
        m_DO5Label->setText(QCoreApplication::translate("dioTestPage", "DO_5", nullptr));
        m_DO6Label->setText(QCoreApplication::translate("dioTestPage", "DO_6", nullptr));
        m_DO7Label->setText(QCoreApplication::translate("dioTestPage", "DO_7", nullptr));
        m_DO8Label->setText(QCoreApplication::translate("dioTestPage", "DO_8", nullptr));
        m_DO9Label->setText(QCoreApplication::translate("dioTestPage", "DO_9", nullptr));
        m_DO10Label->setText(QCoreApplication::translate("dioTestPage", "DO_10", nullptr));
        m_DO11Label->setText(QCoreApplication::translate("dioTestPage", "DO_11", nullptr));
        m_DO12Label->setText(QCoreApplication::translate("dioTestPage", "DO_12", nullptr));
        m_DO13Label->setText(QCoreApplication::translate("dioTestPage", "DO_13", nullptr));
        m_DO14Label->setText(QCoreApplication::translate("dioTestPage", "DO_14", nullptr));
        m_DO15Label->setText(QCoreApplication::translate("dioTestPage", "DO_15", nullptr));
        m_DOAllLabel->setText(QCoreApplication::translate("dioTestPage", "DOAll", nullptr));
        groupBox->setTitle(QCoreApplication::translate("dioTestPage", "Other", nullptr));
    } // retranslateUi

};

namespace Ui {
    class dioTestPage: public Ui_dioTestPage {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_DIOTESTPAGE_H
