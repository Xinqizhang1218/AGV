/********************************************************************************
** Form generated from reading UI file 'lightControlPage.ui'
**
** Created by: Qt User Interface Compiler version 5.13.2
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_LIGHTCONTROLPAGE_H
#define UI_LIGHTCONTROLPAGE_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QGroupBox>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QLabel>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QProgressBar>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QSlider>
#include <QtWidgets/QSpacerItem>
#include <QtWidgets/QSpinBox>
#include <QtWidgets/QTabWidget>
#include <QtWidgets/QVBoxLayout>
#include <QtWidgets/QWidget>
#include "switchButton.h"

QT_BEGIN_NAMESPACE

class Ui_lightControlPage
{
public:
    QVBoxLayout *verticalLayout_19;
    QVBoxLayout *verticalLayout_14;
    QGroupBox *groupBox_6;
    QVBoxLayout *verticalLayout_18;
    QHBoxLayout *horizontalLayout_27;
    QHBoxLayout *horizontalLayout_25;
    QLabel *m_lblPort;
    QComboBox *m_comboBoxPort;
    QHBoxLayout *horizontalLayout_26;
    QLabel *m_lblBaudRate;
    QComboBox *m_comboBoxBaudRate;
    QSpacerItem *horizontalSpacer_5;
    QPushButton *m_connectBtn;
    QSpacerItem *horizontalSpacer_6;
    QTabWidget *tabWidget;
    QWidget *tabLightControl;
    QVBoxLayout *verticalLayout;
    QGroupBox *groupBox;
    QVBoxLayout *verticalLayout_10;
    QHBoxLayout *horizontalLayout_21;
    QVBoxLayout *verticalLayout_2;
    QHBoxLayout *horizontalLayout_13;
    QSlider *m_ch0Slider;
    QSpinBox *m_ch0SpinBox;
    QHBoxLayout *horizontalLayout_17;
    QHBoxLayout *horizontalLayout_14;
    QLabel *m_ch0ModeLabel;
    QComboBox *m_ch0Mode;
    QHBoxLayout *horizontalLayout_15;
    QLabel *m_ch0PwmHoldingTimeLabel;
    QSpinBox *m_ch0PwmHoldingTime;
    QHBoxLayout *horizontalLayout_16;
    QPushButton *m_ch0ReadBtn;
    QPushButton *m_ch0WriteBtn;
    QSpacerItem *horizontalSpacer;
    QVBoxLayout *verticalLayout_6;
    QSpacerItem *verticalSpacer;
    switchButton *m_ch0Switch;
    QSpacerItem *verticalSpacer_2;
    QGroupBox *groupBox_2;
    QVBoxLayout *verticalLayout_11;
    QHBoxLayout *horizontalLayout_22;
    QVBoxLayout *verticalLayout_3;
    QHBoxLayout *horizontalLayout_9;
    QSlider *m_ch1Slider;
    QSpinBox *m_ch1SpinBox;
    QHBoxLayout *horizontalLayout_18;
    QHBoxLayout *horizontalLayout_10;
    QLabel *m_ch1ModeLabel;
    QComboBox *m_ch1Mode;
    QHBoxLayout *horizontalLayout_11;
    QLabel *m_ch1PwmHoldingTimeLabel;
    QSpinBox *m_ch1PwmHoldingTime;
    QHBoxLayout *horizontalLayout_12;
    QPushButton *m_ch1ReadBtn;
    QPushButton *m_ch1WriteBtn;
    QSpacerItem *horizontalSpacer_2;
    QVBoxLayout *verticalLayout_7;
    QSpacerItem *verticalSpacer_3;
    switchButton *m_ch1Switch;
    QSpacerItem *verticalSpacer_4;
    QGroupBox *groupBox_3;
    QVBoxLayout *verticalLayout_12;
    QHBoxLayout *horizontalLayout_23;
    QVBoxLayout *verticalLayout_4;
    QHBoxLayout *horizontalLayout_5;
    QSlider *m_ch2Slider;
    QSpinBox *m_ch2SpinBox;
    QHBoxLayout *horizontalLayout_19;
    QHBoxLayout *horizontalLayout_6;
    QLabel *m_ch2ModeLabel;
    QComboBox *m_ch2Mode;
    QHBoxLayout *horizontalLayout_7;
    QLabel *m_ch2PwmHoldingTimeLabel;
    QSpinBox *m_ch2PwmHoldingTime;
    QHBoxLayout *horizontalLayout_8;
    QPushButton *m_ch2ReadBtn;
    QPushButton *m_ch2WriteBtn;
    QSpacerItem *horizontalSpacer_3;
    QVBoxLayout *verticalLayout_8;
    QSpacerItem *verticalSpacer_5;
    switchButton *m_ch2Switch;
    QSpacerItem *verticalSpacer_6;
    QGroupBox *groupBox_4;
    QVBoxLayout *verticalLayout_13;
    QHBoxLayout *horizontalLayout_24;
    QVBoxLayout *verticalLayout_5;
    QHBoxLayout *horizontalLayout;
    QSlider *m_ch3Slider;
    QSpinBox *m_ch3SpinBox;
    QHBoxLayout *horizontalLayout_20;
    QHBoxLayout *horizontalLayout_2;
    QLabel *m_ch3ModeLabel;
    QComboBox *m_ch3Mode;
    QHBoxLayout *horizontalLayout_3;
    QLabel *m_ch3PwmHoldingTimeLabel;
    QSpinBox *m_ch3PwmHoldingTime;
    QHBoxLayout *horizontalLayout_4;
    QPushButton *m_ch3ReadBtn;
    QPushButton *m_ch3WriteBtn;
    QSpacerItem *horizontalSpacer_4;
    QVBoxLayout *verticalLayout_9;
    QSpacerItem *verticalSpacer_7;
    switchButton *m_ch3Switch;
    QSpacerItem *verticalSpacer_8;
    QWidget *tabAdvanced;
    QVBoxLayout *verticalLayout_34;
    QVBoxLayout *verticalLayout_33;
    QGroupBox *groupBox_5;
    QVBoxLayout *verticalLayout_20;
    QHBoxLayout *horizontalLayout_31;
    QGroupBox *groupBox_10;
    QVBoxLayout *verticalLayout_16;
    QVBoxLayout *verticalLayout_15;
    QComboBox *m_ch0HoldingTimeUnit;
    QLabel *m_ch0CurrentTimeUnit;
    QSpacerItem *horizontalSpacer_9;
    QVBoxLayout *verticalLayout_17;
    QPushButton *m_btnCh0ReadAdvanced;
    QSpacerItem *verticalSpacer_9;
    QPushButton *m_btnCh0WriteAdvanced;
    QGroupBox *groupBox_7;
    QVBoxLayout *verticalLayout_21;
    QHBoxLayout *horizontalLayout_32;
    QGroupBox *groupBox_11;
    QVBoxLayout *verticalLayout_22;
    QVBoxLayout *verticalLayout_23;
    QComboBox *m_ch1HoldingTimeUnit;
    QLabel *m_ch1CurrentTimeUnit;
    QSpacerItem *horizontalSpacer_10;
    QVBoxLayout *verticalLayout_24;
    QPushButton *m_btnCh1ReadAdvanced;
    QSpacerItem *verticalSpacer_10;
    QPushButton *m_btnCh1WriteAdvanced;
    QGroupBox *groupBox_8;
    QVBoxLayout *verticalLayout_25;
    QHBoxLayout *horizontalLayout_33;
    QGroupBox *groupBox_12;
    QVBoxLayout *verticalLayout_26;
    QVBoxLayout *verticalLayout_27;
    QComboBox *m_ch2HoldingTimeUnit;
    QLabel *m_ch2CurrentTimeUnit;
    QSpacerItem *horizontalSpacer_11;
    QVBoxLayout *verticalLayout_28;
    QPushButton *m_btnCh2ReadAdvanced;
    QSpacerItem *verticalSpacer_11;
    QPushButton *m_btnCh2WriteAdvanced;
    QGroupBox *groupBox_9;
    QVBoxLayout *verticalLayout_29;
    QHBoxLayout *horizontalLayout_34;
    QGroupBox *groupBox_13;
    QVBoxLayout *verticalLayout_30;
    QVBoxLayout *verticalLayout_31;
    QComboBox *m_ch3HoldingTimeUnit;
    QLabel *m_ch3CurrentTimeUnit;
    QSpacerItem *horizontalSpacer_12;
    QVBoxLayout *verticalLayout_32;
    QPushButton *m_btnCh3ReadAdvanced;
    QSpacerItem *verticalSpacer_12;
    QPushButton *m_btnCh3WriteAdvanced;
    QWidget *tabFirmwareUpdate;
    QVBoxLayout *verticalLayout_38;
    QVBoxLayout *verticalLayout_37;
    QGroupBox *groupBox_14;
    QVBoxLayout *verticalLayout_36;
    QVBoxLayout *verticalLayout_35;
    QHBoxLayout *horizontalLayout_35;
    QLineEdit *m_filePath;
    QPushButton *m_btnOpenFile;
    QHBoxLayout *horizontalLayout_36;
    QProgressBar *m_progressBarDownload;
    QPushButton *m_btnDownload;
    QSpacerItem *verticalSpacer_13;
    QLabel *m_downloadStatus;
    QSpacerItem *verticalSpacer_14;
    QHBoxLayout *horizontalLayout_30;
    QHBoxLayout *horizontalLayout_28;
    QLabel *label_3;
    QLabel *m_hardwareVer;
    QSpacerItem *horizontalSpacer_7;
    QHBoxLayout *horizontalLayout_29;
    QLabel *label_4;
    QLabel *m_firmwareVer;
    QSpacerItem *horizontalSpacer_8;

    void setupUi(QWidget *lightControlPage)
    {
        if (lightControlPage->objectName().isEmpty())
            lightControlPage->setObjectName(QString::fromUtf8("lightControlPage"));
        lightControlPage->resize(960, 760);
        verticalLayout_19 = new QVBoxLayout(lightControlPage);
        verticalLayout_19->setSpacing(6);
        verticalLayout_19->setContentsMargins(11, 11, 11, 11);
        verticalLayout_19->setObjectName(QString::fromUtf8("verticalLayout_19"));
        verticalLayout_14 = new QVBoxLayout();
        verticalLayout_14->setSpacing(6);
        verticalLayout_14->setObjectName(QString::fromUtf8("verticalLayout_14"));
        groupBox_6 = new QGroupBox(lightControlPage);
        groupBox_6->setObjectName(QString::fromUtf8("groupBox_6"));
        verticalLayout_18 = new QVBoxLayout(groupBox_6);
        verticalLayout_18->setSpacing(6);
        verticalLayout_18->setContentsMargins(11, 11, 11, 11);
        verticalLayout_18->setObjectName(QString::fromUtf8("verticalLayout_18"));
        horizontalLayout_27 = new QHBoxLayout();
        horizontalLayout_27->setSpacing(20);
        horizontalLayout_27->setObjectName(QString::fromUtf8("horizontalLayout_27"));
        horizontalLayout_25 = new QHBoxLayout();
        horizontalLayout_25->setSpacing(6);
        horizontalLayout_25->setObjectName(QString::fromUtf8("horizontalLayout_25"));
        m_lblPort = new QLabel(groupBox_6);
        m_lblPort->setObjectName(QString::fromUtf8("m_lblPort"));

        horizontalLayout_25->addWidget(m_lblPort);

        m_comboBoxPort = new QComboBox(groupBox_6);
        m_comboBoxPort->setObjectName(QString::fromUtf8("m_comboBoxPort"));
        m_comboBoxPort->setMinimumSize(QSize(80, 0));

        horizontalLayout_25->addWidget(m_comboBoxPort);


        horizontalLayout_27->addLayout(horizontalLayout_25);

        horizontalLayout_26 = new QHBoxLayout();
        horizontalLayout_26->setSpacing(6);
        horizontalLayout_26->setObjectName(QString::fromUtf8("horizontalLayout_26"));
        m_lblBaudRate = new QLabel(groupBox_6);
        m_lblBaudRate->setObjectName(QString::fromUtf8("m_lblBaudRate"));

        horizontalLayout_26->addWidget(m_lblBaudRate);

        m_comboBoxBaudRate = new QComboBox(groupBox_6);
        m_comboBoxBaudRate->setObjectName(QString::fromUtf8("m_comboBoxBaudRate"));
        m_comboBoxBaudRate->setMinimumSize(QSize(100, 0));

        horizontalLayout_26->addWidget(m_comboBoxBaudRate);


        horizontalLayout_27->addLayout(horizontalLayout_26);

        horizontalSpacer_5 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_27->addItem(horizontalSpacer_5);

        m_connectBtn = new QPushButton(groupBox_6);
        m_connectBtn->setObjectName(QString::fromUtf8("m_connectBtn"));
        m_connectBtn->setStyleSheet(QString::fromUtf8(""));

        horizontalLayout_27->addWidget(m_connectBtn);

        horizontalSpacer_6 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_27->addItem(horizontalSpacer_6);


        verticalLayout_18->addLayout(horizontalLayout_27);


        verticalLayout_14->addWidget(groupBox_6);

        tabWidget = new QTabWidget(lightControlPage);
        tabWidget->setObjectName(QString::fromUtf8("tabWidget"));
        tabWidget->setStyleSheet(QString::fromUtf8(""));
        tabWidget->setTabShape(QTabWidget::Rounded);
        tabLightControl = new QWidget();
        tabLightControl->setObjectName(QString::fromUtf8("tabLightControl"));
        verticalLayout = new QVBoxLayout(tabLightControl);
        verticalLayout->setSpacing(6);
        verticalLayout->setContentsMargins(11, 11, 11, 11);
        verticalLayout->setObjectName(QString::fromUtf8("verticalLayout"));
        groupBox = new QGroupBox(tabLightControl);
        groupBox->setObjectName(QString::fromUtf8("groupBox"));
        verticalLayout_10 = new QVBoxLayout(groupBox);
        verticalLayout_10->setSpacing(6);
        verticalLayout_10->setContentsMargins(11, 11, 11, 11);
        verticalLayout_10->setObjectName(QString::fromUtf8("verticalLayout_10"));
        horizontalLayout_21 = new QHBoxLayout();
        horizontalLayout_21->setSpacing(6);
        horizontalLayout_21->setObjectName(QString::fromUtf8("horizontalLayout_21"));
        verticalLayout_2 = new QVBoxLayout();
        verticalLayout_2->setSpacing(6);
        verticalLayout_2->setObjectName(QString::fromUtf8("verticalLayout_2"));
        horizontalLayout_13 = new QHBoxLayout();
        horizontalLayout_13->setSpacing(6);
        horizontalLayout_13->setObjectName(QString::fromUtf8("horizontalLayout_13"));
        m_ch0Slider = new QSlider(groupBox);
        m_ch0Slider->setObjectName(QString::fromUtf8("m_ch0Slider"));
        m_ch0Slider->setMinimumSize(QSize(500, 0));
        m_ch0Slider->setMouseTracking(true);
        m_ch0Slider->setMaximum(100);
        m_ch0Slider->setOrientation(Qt::Horizontal);
        m_ch0Slider->setTickPosition(QSlider::TicksBelow);
        m_ch0Slider->setTickInterval(5);

        horizontalLayout_13->addWidget(m_ch0Slider);

        m_ch0SpinBox = new QSpinBox(groupBox);
        m_ch0SpinBox->setObjectName(QString::fromUtf8("m_ch0SpinBox"));
        m_ch0SpinBox->setMinimumSize(QSize(50, 0));
        m_ch0SpinBox->setMaximumSize(QSize(50, 16777215));
        m_ch0SpinBox->setMaximum(100);

        horizontalLayout_13->addWidget(m_ch0SpinBox);


        verticalLayout_2->addLayout(horizontalLayout_13);

        horizontalLayout_17 = new QHBoxLayout();
        horizontalLayout_17->setSpacing(6);
        horizontalLayout_17->setObjectName(QString::fromUtf8("horizontalLayout_17"));
        horizontalLayout_14 = new QHBoxLayout();
        horizontalLayout_14->setSpacing(6);
        horizontalLayout_14->setObjectName(QString::fromUtf8("horizontalLayout_14"));
        m_ch0ModeLabel = new QLabel(groupBox);
        m_ch0ModeLabel->setObjectName(QString::fromUtf8("m_ch0ModeLabel"));

        horizontalLayout_14->addWidget(m_ch0ModeLabel);

        m_ch0Mode = new QComboBox(groupBox);
        m_ch0Mode->setObjectName(QString::fromUtf8("m_ch0Mode"));
        m_ch0Mode->setMinimumSize(QSize(150, 0));

        horizontalLayout_14->addWidget(m_ch0Mode);


        horizontalLayout_17->addLayout(horizontalLayout_14);

        horizontalLayout_15 = new QHBoxLayout();
        horizontalLayout_15->setSpacing(6);
        horizontalLayout_15->setObjectName(QString::fromUtf8("horizontalLayout_15"));
        m_ch0PwmHoldingTimeLabel = new QLabel(groupBox);
        m_ch0PwmHoldingTimeLabel->setObjectName(QString::fromUtf8("m_ch0PwmHoldingTimeLabel"));
        m_ch0PwmHoldingTimeLabel->setScaledContents(true);
        m_ch0PwmHoldingTimeLabel->setWordWrap(false);

        horizontalLayout_15->addWidget(m_ch0PwmHoldingTimeLabel);

        m_ch0PwmHoldingTime = new QSpinBox(groupBox);
        m_ch0PwmHoldingTime->setObjectName(QString::fromUtf8("m_ch0PwmHoldingTime"));
        m_ch0PwmHoldingTime->setMinimumSize(QSize(100, 0));
        m_ch0PwmHoldingTime->setMaximumSize(QSize(100, 16777215));
        m_ch0PwmHoldingTime->setMaximum(255);

        horizontalLayout_15->addWidget(m_ch0PwmHoldingTime);


        horizontalLayout_17->addLayout(horizontalLayout_15);

        horizontalLayout_16 = new QHBoxLayout();
        horizontalLayout_16->setSpacing(6);
        horizontalLayout_16->setObjectName(QString::fromUtf8("horizontalLayout_16"));
        m_ch0ReadBtn = new QPushButton(groupBox);
        m_ch0ReadBtn->setObjectName(QString::fromUtf8("m_ch0ReadBtn"));
        m_ch0ReadBtn->setMinimumSize(QSize(100, 0));
        m_ch0ReadBtn->setMaximumSize(QSize(100, 16777215));

        horizontalLayout_16->addWidget(m_ch0ReadBtn);

        m_ch0WriteBtn = new QPushButton(groupBox);
        m_ch0WriteBtn->setObjectName(QString::fromUtf8("m_ch0WriteBtn"));
        m_ch0WriteBtn->setMinimumSize(QSize(100, 0));
        m_ch0WriteBtn->setMaximumSize(QSize(100, 16777215));

        horizontalLayout_16->addWidget(m_ch0WriteBtn);


        horizontalLayout_17->addLayout(horizontalLayout_16);


        verticalLayout_2->addLayout(horizontalLayout_17);


        horizontalLayout_21->addLayout(verticalLayout_2);

        horizontalSpacer = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_21->addItem(horizontalSpacer);

        verticalLayout_6 = new QVBoxLayout();
        verticalLayout_6->setSpacing(6);
        verticalLayout_6->setObjectName(QString::fromUtf8("verticalLayout_6"));
        verticalSpacer = new QSpacerItem(20, 18, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_6->addItem(verticalSpacer);

        m_ch0Switch = new switchButton(groupBox);
        m_ch0Switch->setObjectName(QString::fromUtf8("m_ch0Switch"));
        m_ch0Switch->setMinimumSize(QSize(100, 40));

        verticalLayout_6->addWidget(m_ch0Switch);

        verticalSpacer_2 = new QSpacerItem(20, 18, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_6->addItem(verticalSpacer_2);


        horizontalLayout_21->addLayout(verticalLayout_6);


        verticalLayout_10->addLayout(horizontalLayout_21);


        verticalLayout->addWidget(groupBox);

        groupBox_2 = new QGroupBox(tabLightControl);
        groupBox_2->setObjectName(QString::fromUtf8("groupBox_2"));
        verticalLayout_11 = new QVBoxLayout(groupBox_2);
        verticalLayout_11->setSpacing(6);
        verticalLayout_11->setContentsMargins(11, 11, 11, 11);
        verticalLayout_11->setObjectName(QString::fromUtf8("verticalLayout_11"));
        horizontalLayout_22 = new QHBoxLayout();
        horizontalLayout_22->setSpacing(6);
        horizontalLayout_22->setObjectName(QString::fromUtf8("horizontalLayout_22"));
        verticalLayout_3 = new QVBoxLayout();
        verticalLayout_3->setSpacing(6);
        verticalLayout_3->setObjectName(QString::fromUtf8("verticalLayout_3"));
        horizontalLayout_9 = new QHBoxLayout();
        horizontalLayout_9->setSpacing(6);
        horizontalLayout_9->setObjectName(QString::fromUtf8("horizontalLayout_9"));
        m_ch1Slider = new QSlider(groupBox_2);
        m_ch1Slider->setObjectName(QString::fromUtf8("m_ch1Slider"));
        m_ch1Slider->setMinimumSize(QSize(500, 0));
        m_ch1Slider->setMouseTracking(true);
        m_ch1Slider->setMaximum(100);
        m_ch1Slider->setOrientation(Qt::Horizontal);
        m_ch1Slider->setTickPosition(QSlider::TicksBelow);
        m_ch1Slider->setTickInterval(5);

        horizontalLayout_9->addWidget(m_ch1Slider);

        m_ch1SpinBox = new QSpinBox(groupBox_2);
        m_ch1SpinBox->setObjectName(QString::fromUtf8("m_ch1SpinBox"));
        m_ch1SpinBox->setMinimumSize(QSize(50, 0));
        m_ch1SpinBox->setMaximumSize(QSize(50, 16777215));
        m_ch1SpinBox->setMaximum(100);

        horizontalLayout_9->addWidget(m_ch1SpinBox);


        verticalLayout_3->addLayout(horizontalLayout_9);

        horizontalLayout_18 = new QHBoxLayout();
        horizontalLayout_18->setSpacing(6);
        horizontalLayout_18->setObjectName(QString::fromUtf8("horizontalLayout_18"));
        horizontalLayout_10 = new QHBoxLayout();
        horizontalLayout_10->setSpacing(6);
        horizontalLayout_10->setObjectName(QString::fromUtf8("horizontalLayout_10"));
        m_ch1ModeLabel = new QLabel(groupBox_2);
        m_ch1ModeLabel->setObjectName(QString::fromUtf8("m_ch1ModeLabel"));

        horizontalLayout_10->addWidget(m_ch1ModeLabel);

        m_ch1Mode = new QComboBox(groupBox_2);
        m_ch1Mode->setObjectName(QString::fromUtf8("m_ch1Mode"));
        m_ch1Mode->setMinimumSize(QSize(150, 0));

        horizontalLayout_10->addWidget(m_ch1Mode);


        horizontalLayout_18->addLayout(horizontalLayout_10);

        horizontalLayout_11 = new QHBoxLayout();
        horizontalLayout_11->setSpacing(6);
        horizontalLayout_11->setObjectName(QString::fromUtf8("horizontalLayout_11"));
        m_ch1PwmHoldingTimeLabel = new QLabel(groupBox_2);
        m_ch1PwmHoldingTimeLabel->setObjectName(QString::fromUtf8("m_ch1PwmHoldingTimeLabel"));
        m_ch1PwmHoldingTimeLabel->setScaledContents(true);
        m_ch1PwmHoldingTimeLabel->setWordWrap(false);

        horizontalLayout_11->addWidget(m_ch1PwmHoldingTimeLabel);

        m_ch1PwmHoldingTime = new QSpinBox(groupBox_2);
        m_ch1PwmHoldingTime->setObjectName(QString::fromUtf8("m_ch1PwmHoldingTime"));
        m_ch1PwmHoldingTime->setMinimumSize(QSize(100, 0));
        m_ch1PwmHoldingTime->setMaximumSize(QSize(100, 16777215));
        m_ch1PwmHoldingTime->setMaximum(255);

        horizontalLayout_11->addWidget(m_ch1PwmHoldingTime);


        horizontalLayout_18->addLayout(horizontalLayout_11);

        horizontalLayout_12 = new QHBoxLayout();
        horizontalLayout_12->setSpacing(6);
        horizontalLayout_12->setObjectName(QString::fromUtf8("horizontalLayout_12"));
        m_ch1ReadBtn = new QPushButton(groupBox_2);
        m_ch1ReadBtn->setObjectName(QString::fromUtf8("m_ch1ReadBtn"));
        m_ch1ReadBtn->setMinimumSize(QSize(100, 0));
        m_ch1ReadBtn->setMaximumSize(QSize(100, 16777215));

        horizontalLayout_12->addWidget(m_ch1ReadBtn);

        m_ch1WriteBtn = new QPushButton(groupBox_2);
        m_ch1WriteBtn->setObjectName(QString::fromUtf8("m_ch1WriteBtn"));
        m_ch1WriteBtn->setMinimumSize(QSize(100, 0));
        m_ch1WriteBtn->setMaximumSize(QSize(100, 16777215));

        horizontalLayout_12->addWidget(m_ch1WriteBtn);


        horizontalLayout_18->addLayout(horizontalLayout_12);


        verticalLayout_3->addLayout(horizontalLayout_18);


        horizontalLayout_22->addLayout(verticalLayout_3);

        horizontalSpacer_2 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_22->addItem(horizontalSpacer_2);

        verticalLayout_7 = new QVBoxLayout();
        verticalLayout_7->setSpacing(6);
        verticalLayout_7->setObjectName(QString::fromUtf8("verticalLayout_7"));
        verticalSpacer_3 = new QSpacerItem(20, 17, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_7->addItem(verticalSpacer_3);

        m_ch1Switch = new switchButton(groupBox_2);
        m_ch1Switch->setObjectName(QString::fromUtf8("m_ch1Switch"));
        m_ch1Switch->setMinimumSize(QSize(100, 40));

        verticalLayout_7->addWidget(m_ch1Switch);

        verticalSpacer_4 = new QSpacerItem(20, 17, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_7->addItem(verticalSpacer_4);


        horizontalLayout_22->addLayout(verticalLayout_7);


        verticalLayout_11->addLayout(horizontalLayout_22);


        verticalLayout->addWidget(groupBox_2);

        groupBox_3 = new QGroupBox(tabLightControl);
        groupBox_3->setObjectName(QString::fromUtf8("groupBox_3"));
        verticalLayout_12 = new QVBoxLayout(groupBox_3);
        verticalLayout_12->setSpacing(6);
        verticalLayout_12->setContentsMargins(11, 11, 11, 11);
        verticalLayout_12->setObjectName(QString::fromUtf8("verticalLayout_12"));
        horizontalLayout_23 = new QHBoxLayout();
        horizontalLayout_23->setSpacing(6);
        horizontalLayout_23->setObjectName(QString::fromUtf8("horizontalLayout_23"));
        verticalLayout_4 = new QVBoxLayout();
        verticalLayout_4->setSpacing(6);
        verticalLayout_4->setObjectName(QString::fromUtf8("verticalLayout_4"));
        horizontalLayout_5 = new QHBoxLayout();
        horizontalLayout_5->setSpacing(6);
        horizontalLayout_5->setObjectName(QString::fromUtf8("horizontalLayout_5"));
        m_ch2Slider = new QSlider(groupBox_3);
        m_ch2Slider->setObjectName(QString::fromUtf8("m_ch2Slider"));
        m_ch2Slider->setMinimumSize(QSize(500, 0));
        m_ch2Slider->setMaximum(100);
        m_ch2Slider->setOrientation(Qt::Horizontal);
        m_ch2Slider->setTickPosition(QSlider::TicksBelow);
        m_ch2Slider->setTickInterval(5);

        horizontalLayout_5->addWidget(m_ch2Slider);

        m_ch2SpinBox = new QSpinBox(groupBox_3);
        m_ch2SpinBox->setObjectName(QString::fromUtf8("m_ch2SpinBox"));
        m_ch2SpinBox->setMinimumSize(QSize(50, 0));
        m_ch2SpinBox->setMaximumSize(QSize(50, 16777215));
        m_ch2SpinBox->setMaximum(100);

        horizontalLayout_5->addWidget(m_ch2SpinBox);


        verticalLayout_4->addLayout(horizontalLayout_5);

        horizontalLayout_19 = new QHBoxLayout();
        horizontalLayout_19->setSpacing(6);
        horizontalLayout_19->setObjectName(QString::fromUtf8("horizontalLayout_19"));
        horizontalLayout_6 = new QHBoxLayout();
        horizontalLayout_6->setSpacing(6);
        horizontalLayout_6->setObjectName(QString::fromUtf8("horizontalLayout_6"));
        m_ch2ModeLabel = new QLabel(groupBox_3);
        m_ch2ModeLabel->setObjectName(QString::fromUtf8("m_ch2ModeLabel"));

        horizontalLayout_6->addWidget(m_ch2ModeLabel);

        m_ch2Mode = new QComboBox(groupBox_3);
        m_ch2Mode->setObjectName(QString::fromUtf8("m_ch2Mode"));
        m_ch2Mode->setMinimumSize(QSize(150, 0));

        horizontalLayout_6->addWidget(m_ch2Mode);


        horizontalLayout_19->addLayout(horizontalLayout_6);

        horizontalLayout_7 = new QHBoxLayout();
        horizontalLayout_7->setSpacing(6);
        horizontalLayout_7->setObjectName(QString::fromUtf8("horizontalLayout_7"));
        m_ch2PwmHoldingTimeLabel = new QLabel(groupBox_3);
        m_ch2PwmHoldingTimeLabel->setObjectName(QString::fromUtf8("m_ch2PwmHoldingTimeLabel"));
        m_ch2PwmHoldingTimeLabel->setScaledContents(true);

        horizontalLayout_7->addWidget(m_ch2PwmHoldingTimeLabel);

        m_ch2PwmHoldingTime = new QSpinBox(groupBox_3);
        m_ch2PwmHoldingTime->setObjectName(QString::fromUtf8("m_ch2PwmHoldingTime"));
        m_ch2PwmHoldingTime->setMinimumSize(QSize(100, 0));
        m_ch2PwmHoldingTime->setMaximumSize(QSize(100, 16777215));
        m_ch2PwmHoldingTime->setMaximum(255);

        horizontalLayout_7->addWidget(m_ch2PwmHoldingTime);


        horizontalLayout_19->addLayout(horizontalLayout_7);

        horizontalLayout_8 = new QHBoxLayout();
        horizontalLayout_8->setSpacing(6);
        horizontalLayout_8->setObjectName(QString::fromUtf8("horizontalLayout_8"));
        m_ch2ReadBtn = new QPushButton(groupBox_3);
        m_ch2ReadBtn->setObjectName(QString::fromUtf8("m_ch2ReadBtn"));
        m_ch2ReadBtn->setMinimumSize(QSize(100, 0));
        m_ch2ReadBtn->setMaximumSize(QSize(100, 16777215));

        horizontalLayout_8->addWidget(m_ch2ReadBtn);

        m_ch2WriteBtn = new QPushButton(groupBox_3);
        m_ch2WriteBtn->setObjectName(QString::fromUtf8("m_ch2WriteBtn"));
        m_ch2WriteBtn->setMinimumSize(QSize(100, 0));
        m_ch2WriteBtn->setMaximumSize(QSize(100, 16777215));

        horizontalLayout_8->addWidget(m_ch2WriteBtn);


        horizontalLayout_19->addLayout(horizontalLayout_8);


        verticalLayout_4->addLayout(horizontalLayout_19);


        horizontalLayout_23->addLayout(verticalLayout_4);

        horizontalSpacer_3 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_23->addItem(horizontalSpacer_3);

        verticalLayout_8 = new QVBoxLayout();
        verticalLayout_8->setSpacing(6);
        verticalLayout_8->setObjectName(QString::fromUtf8("verticalLayout_8"));
        verticalSpacer_5 = new QSpacerItem(20, 18, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_8->addItem(verticalSpacer_5);

        m_ch2Switch = new switchButton(groupBox_3);
        m_ch2Switch->setObjectName(QString::fromUtf8("m_ch2Switch"));
        m_ch2Switch->setMinimumSize(QSize(100, 40));

        verticalLayout_8->addWidget(m_ch2Switch);

        verticalSpacer_6 = new QSpacerItem(20, 18, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_8->addItem(verticalSpacer_6);


        horizontalLayout_23->addLayout(verticalLayout_8);


        verticalLayout_12->addLayout(horizontalLayout_23);


        verticalLayout->addWidget(groupBox_3);

        groupBox_4 = new QGroupBox(tabLightControl);
        groupBox_4->setObjectName(QString::fromUtf8("groupBox_4"));
        verticalLayout_13 = new QVBoxLayout(groupBox_4);
        verticalLayout_13->setSpacing(6);
        verticalLayout_13->setContentsMargins(11, 11, 11, 11);
        verticalLayout_13->setObjectName(QString::fromUtf8("verticalLayout_13"));
        horizontalLayout_24 = new QHBoxLayout();
        horizontalLayout_24->setSpacing(6);
        horizontalLayout_24->setObjectName(QString::fromUtf8("horizontalLayout_24"));
        verticalLayout_5 = new QVBoxLayout();
        verticalLayout_5->setSpacing(6);
        verticalLayout_5->setObjectName(QString::fromUtf8("verticalLayout_5"));
        horizontalLayout = new QHBoxLayout();
        horizontalLayout->setSpacing(6);
        horizontalLayout->setObjectName(QString::fromUtf8("horizontalLayout"));
        m_ch3Slider = new QSlider(groupBox_4);
        m_ch3Slider->setObjectName(QString::fromUtf8("m_ch3Slider"));
        m_ch3Slider->setMinimumSize(QSize(500, 0));
        m_ch3Slider->setMaximum(100);
        m_ch3Slider->setOrientation(Qt::Horizontal);
        m_ch3Slider->setTickPosition(QSlider::TicksBelow);
        m_ch3Slider->setTickInterval(5);

        horizontalLayout->addWidget(m_ch3Slider);

        m_ch3SpinBox = new QSpinBox(groupBox_4);
        m_ch3SpinBox->setObjectName(QString::fromUtf8("m_ch3SpinBox"));
        m_ch3SpinBox->setMinimumSize(QSize(50, 0));
        m_ch3SpinBox->setMaximumSize(QSize(50, 16777215));
        m_ch3SpinBox->setMaximum(100);

        horizontalLayout->addWidget(m_ch3SpinBox);


        verticalLayout_5->addLayout(horizontalLayout);

        horizontalLayout_20 = new QHBoxLayout();
        horizontalLayout_20->setSpacing(6);
        horizontalLayout_20->setObjectName(QString::fromUtf8("horizontalLayout_20"));
        horizontalLayout_2 = new QHBoxLayout();
        horizontalLayout_2->setSpacing(6);
        horizontalLayout_2->setObjectName(QString::fromUtf8("horizontalLayout_2"));
        m_ch3ModeLabel = new QLabel(groupBox_4);
        m_ch3ModeLabel->setObjectName(QString::fromUtf8("m_ch3ModeLabel"));

        horizontalLayout_2->addWidget(m_ch3ModeLabel);

        m_ch3Mode = new QComboBox(groupBox_4);
        m_ch3Mode->setObjectName(QString::fromUtf8("m_ch3Mode"));
        m_ch3Mode->setMinimumSize(QSize(150, 0));

        horizontalLayout_2->addWidget(m_ch3Mode);


        horizontalLayout_20->addLayout(horizontalLayout_2);

        horizontalLayout_3 = new QHBoxLayout();
        horizontalLayout_3->setSpacing(6);
        horizontalLayout_3->setObjectName(QString::fromUtf8("horizontalLayout_3"));
        m_ch3PwmHoldingTimeLabel = new QLabel(groupBox_4);
        m_ch3PwmHoldingTimeLabel->setObjectName(QString::fromUtf8("m_ch3PwmHoldingTimeLabel"));
        m_ch3PwmHoldingTimeLabel->setScaledContents(true);

        horizontalLayout_3->addWidget(m_ch3PwmHoldingTimeLabel);

        m_ch3PwmHoldingTime = new QSpinBox(groupBox_4);
        m_ch3PwmHoldingTime->setObjectName(QString::fromUtf8("m_ch3PwmHoldingTime"));
        m_ch3PwmHoldingTime->setMinimumSize(QSize(100, 0));
        m_ch3PwmHoldingTime->setMaximumSize(QSize(100, 16777215));
        m_ch3PwmHoldingTime->setMaximum(255);

        horizontalLayout_3->addWidget(m_ch3PwmHoldingTime);


        horizontalLayout_20->addLayout(horizontalLayout_3);

        horizontalLayout_4 = new QHBoxLayout();
        horizontalLayout_4->setSpacing(6);
        horizontalLayout_4->setObjectName(QString::fromUtf8("horizontalLayout_4"));
        m_ch3ReadBtn = new QPushButton(groupBox_4);
        m_ch3ReadBtn->setObjectName(QString::fromUtf8("m_ch3ReadBtn"));
        m_ch3ReadBtn->setMinimumSize(QSize(100, 0));
        m_ch3ReadBtn->setMaximumSize(QSize(100, 16777215));

        horizontalLayout_4->addWidget(m_ch3ReadBtn);

        m_ch3WriteBtn = new QPushButton(groupBox_4);
        m_ch3WriteBtn->setObjectName(QString::fromUtf8("m_ch3WriteBtn"));
        m_ch3WriteBtn->setMinimumSize(QSize(100, 0));
        m_ch3WriteBtn->setMaximumSize(QSize(100, 16777215));

        horizontalLayout_4->addWidget(m_ch3WriteBtn);


        horizontalLayout_20->addLayout(horizontalLayout_4);


        verticalLayout_5->addLayout(horizontalLayout_20);


        horizontalLayout_24->addLayout(verticalLayout_5);

        horizontalSpacer_4 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_24->addItem(horizontalSpacer_4);

        verticalLayout_9 = new QVBoxLayout();
        verticalLayout_9->setSpacing(6);
        verticalLayout_9->setObjectName(QString::fromUtf8("verticalLayout_9"));
        verticalSpacer_7 = new QSpacerItem(20, 18, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_9->addItem(verticalSpacer_7);

        m_ch3Switch = new switchButton(groupBox_4);
        m_ch3Switch->setObjectName(QString::fromUtf8("m_ch3Switch"));
        m_ch3Switch->setMinimumSize(QSize(100, 40));

        verticalLayout_9->addWidget(m_ch3Switch);

        verticalSpacer_8 = new QSpacerItem(20, 18, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_9->addItem(verticalSpacer_8);


        horizontalLayout_24->addLayout(verticalLayout_9);


        verticalLayout_13->addLayout(horizontalLayout_24);


        verticalLayout->addWidget(groupBox_4);

        tabWidget->addTab(tabLightControl, QString());
        tabAdvanced = new QWidget();
        tabAdvanced->setObjectName(QString::fromUtf8("tabAdvanced"));
        verticalLayout_34 = new QVBoxLayout(tabAdvanced);
        verticalLayout_34->setSpacing(6);
        verticalLayout_34->setContentsMargins(11, 11, 11, 11);
        verticalLayout_34->setObjectName(QString::fromUtf8("verticalLayout_34"));
        verticalLayout_33 = new QVBoxLayout();
        verticalLayout_33->setSpacing(6);
        verticalLayout_33->setObjectName(QString::fromUtf8("verticalLayout_33"));
        groupBox_5 = new QGroupBox(tabAdvanced);
        groupBox_5->setObjectName(QString::fromUtf8("groupBox_5"));
        verticalLayout_20 = new QVBoxLayout(groupBox_5);
        verticalLayout_20->setSpacing(6);
        verticalLayout_20->setContentsMargins(11, 11, 11, 11);
        verticalLayout_20->setObjectName(QString::fromUtf8("verticalLayout_20"));
        horizontalLayout_31 = new QHBoxLayout();
        horizontalLayout_31->setSpacing(6);
        horizontalLayout_31->setObjectName(QString::fromUtf8("horizontalLayout_31"));
        groupBox_10 = new QGroupBox(groupBox_5);
        groupBox_10->setObjectName(QString::fromUtf8("groupBox_10"));
        verticalLayout_16 = new QVBoxLayout(groupBox_10);
        verticalLayout_16->setSpacing(6);
        verticalLayout_16->setContentsMargins(11, 11, 11, 11);
        verticalLayout_16->setObjectName(QString::fromUtf8("verticalLayout_16"));
        verticalLayout_15 = new QVBoxLayout();
        verticalLayout_15->setSpacing(6);
        verticalLayout_15->setObjectName(QString::fromUtf8("verticalLayout_15"));
        m_ch0HoldingTimeUnit = new QComboBox(groupBox_10);
        m_ch0HoldingTimeUnit->setObjectName(QString::fromUtf8("m_ch0HoldingTimeUnit"));

        verticalLayout_15->addWidget(m_ch0HoldingTimeUnit);

        m_ch0CurrentTimeUnit = new QLabel(groupBox_10);
        m_ch0CurrentTimeUnit->setObjectName(QString::fromUtf8("m_ch0CurrentTimeUnit"));

        verticalLayout_15->addWidget(m_ch0CurrentTimeUnit);


        verticalLayout_16->addLayout(verticalLayout_15);


        horizontalLayout_31->addWidget(groupBox_10);

        horizontalSpacer_9 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_31->addItem(horizontalSpacer_9);

        verticalLayout_17 = new QVBoxLayout();
        verticalLayout_17->setSpacing(6);
        verticalLayout_17->setObjectName(QString::fromUtf8("verticalLayout_17"));
        m_btnCh0ReadAdvanced = new QPushButton(groupBox_5);
        m_btnCh0ReadAdvanced->setObjectName(QString::fromUtf8("m_btnCh0ReadAdvanced"));

        verticalLayout_17->addWidget(m_btnCh0ReadAdvanced);

        verticalSpacer_9 = new QSpacerItem(20, 40, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_17->addItem(verticalSpacer_9);

        m_btnCh0WriteAdvanced = new QPushButton(groupBox_5);
        m_btnCh0WriteAdvanced->setObjectName(QString::fromUtf8("m_btnCh0WriteAdvanced"));

        verticalLayout_17->addWidget(m_btnCh0WriteAdvanced);


        horizontalLayout_31->addLayout(verticalLayout_17);


        verticalLayout_20->addLayout(horizontalLayout_31);


        verticalLayout_33->addWidget(groupBox_5);

        groupBox_7 = new QGroupBox(tabAdvanced);
        groupBox_7->setObjectName(QString::fromUtf8("groupBox_7"));
        verticalLayout_21 = new QVBoxLayout(groupBox_7);
        verticalLayout_21->setSpacing(6);
        verticalLayout_21->setContentsMargins(11, 11, 11, 11);
        verticalLayout_21->setObjectName(QString::fromUtf8("verticalLayout_21"));
        horizontalLayout_32 = new QHBoxLayout();
        horizontalLayout_32->setSpacing(6);
        horizontalLayout_32->setObjectName(QString::fromUtf8("horizontalLayout_32"));
        groupBox_11 = new QGroupBox(groupBox_7);
        groupBox_11->setObjectName(QString::fromUtf8("groupBox_11"));
        verticalLayout_22 = new QVBoxLayout(groupBox_11);
        verticalLayout_22->setSpacing(6);
        verticalLayout_22->setContentsMargins(11, 11, 11, 11);
        verticalLayout_22->setObjectName(QString::fromUtf8("verticalLayout_22"));
        verticalLayout_23 = new QVBoxLayout();
        verticalLayout_23->setSpacing(6);
        verticalLayout_23->setObjectName(QString::fromUtf8("verticalLayout_23"));
        m_ch1HoldingTimeUnit = new QComboBox(groupBox_11);
        m_ch1HoldingTimeUnit->setObjectName(QString::fromUtf8("m_ch1HoldingTimeUnit"));

        verticalLayout_23->addWidget(m_ch1HoldingTimeUnit);

        m_ch1CurrentTimeUnit = new QLabel(groupBox_11);
        m_ch1CurrentTimeUnit->setObjectName(QString::fromUtf8("m_ch1CurrentTimeUnit"));

        verticalLayout_23->addWidget(m_ch1CurrentTimeUnit);


        verticalLayout_22->addLayout(verticalLayout_23);


        horizontalLayout_32->addWidget(groupBox_11);

        horizontalSpacer_10 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_32->addItem(horizontalSpacer_10);

        verticalLayout_24 = new QVBoxLayout();
        verticalLayout_24->setSpacing(6);
        verticalLayout_24->setObjectName(QString::fromUtf8("verticalLayout_24"));
        m_btnCh1ReadAdvanced = new QPushButton(groupBox_7);
        m_btnCh1ReadAdvanced->setObjectName(QString::fromUtf8("m_btnCh1ReadAdvanced"));

        verticalLayout_24->addWidget(m_btnCh1ReadAdvanced);

        verticalSpacer_10 = new QSpacerItem(20, 40, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_24->addItem(verticalSpacer_10);

        m_btnCh1WriteAdvanced = new QPushButton(groupBox_7);
        m_btnCh1WriteAdvanced->setObjectName(QString::fromUtf8("m_btnCh1WriteAdvanced"));

        verticalLayout_24->addWidget(m_btnCh1WriteAdvanced);


        horizontalLayout_32->addLayout(verticalLayout_24);


        verticalLayout_21->addLayout(horizontalLayout_32);


        verticalLayout_33->addWidget(groupBox_7);

        groupBox_8 = new QGroupBox(tabAdvanced);
        groupBox_8->setObjectName(QString::fromUtf8("groupBox_8"));
        verticalLayout_25 = new QVBoxLayout(groupBox_8);
        verticalLayout_25->setSpacing(6);
        verticalLayout_25->setContentsMargins(11, 11, 11, 11);
        verticalLayout_25->setObjectName(QString::fromUtf8("verticalLayout_25"));
        horizontalLayout_33 = new QHBoxLayout();
        horizontalLayout_33->setSpacing(6);
        horizontalLayout_33->setObjectName(QString::fromUtf8("horizontalLayout_33"));
        groupBox_12 = new QGroupBox(groupBox_8);
        groupBox_12->setObjectName(QString::fromUtf8("groupBox_12"));
        verticalLayout_26 = new QVBoxLayout(groupBox_12);
        verticalLayout_26->setSpacing(6);
        verticalLayout_26->setContentsMargins(11, 11, 11, 11);
        verticalLayout_26->setObjectName(QString::fromUtf8("verticalLayout_26"));
        verticalLayout_27 = new QVBoxLayout();
        verticalLayout_27->setSpacing(6);
        verticalLayout_27->setObjectName(QString::fromUtf8("verticalLayout_27"));
        m_ch2HoldingTimeUnit = new QComboBox(groupBox_12);
        m_ch2HoldingTimeUnit->setObjectName(QString::fromUtf8("m_ch2HoldingTimeUnit"));

        verticalLayout_27->addWidget(m_ch2HoldingTimeUnit);

        m_ch2CurrentTimeUnit = new QLabel(groupBox_12);
        m_ch2CurrentTimeUnit->setObjectName(QString::fromUtf8("m_ch2CurrentTimeUnit"));

        verticalLayout_27->addWidget(m_ch2CurrentTimeUnit);


        verticalLayout_26->addLayout(verticalLayout_27);


        horizontalLayout_33->addWidget(groupBox_12);

        horizontalSpacer_11 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_33->addItem(horizontalSpacer_11);

        verticalLayout_28 = new QVBoxLayout();
        verticalLayout_28->setSpacing(6);
        verticalLayout_28->setObjectName(QString::fromUtf8("verticalLayout_28"));
        m_btnCh2ReadAdvanced = new QPushButton(groupBox_8);
        m_btnCh2ReadAdvanced->setObjectName(QString::fromUtf8("m_btnCh2ReadAdvanced"));

        verticalLayout_28->addWidget(m_btnCh2ReadAdvanced);

        verticalSpacer_11 = new QSpacerItem(20, 40, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_28->addItem(verticalSpacer_11);

        m_btnCh2WriteAdvanced = new QPushButton(groupBox_8);
        m_btnCh2WriteAdvanced->setObjectName(QString::fromUtf8("m_btnCh2WriteAdvanced"));

        verticalLayout_28->addWidget(m_btnCh2WriteAdvanced);


        horizontalLayout_33->addLayout(verticalLayout_28);


        verticalLayout_25->addLayout(horizontalLayout_33);


        verticalLayout_33->addWidget(groupBox_8);

        groupBox_9 = new QGroupBox(tabAdvanced);
        groupBox_9->setObjectName(QString::fromUtf8("groupBox_9"));
        verticalLayout_29 = new QVBoxLayout(groupBox_9);
        verticalLayout_29->setSpacing(6);
        verticalLayout_29->setContentsMargins(11, 11, 11, 11);
        verticalLayout_29->setObjectName(QString::fromUtf8("verticalLayout_29"));
        horizontalLayout_34 = new QHBoxLayout();
        horizontalLayout_34->setSpacing(6);
        horizontalLayout_34->setObjectName(QString::fromUtf8("horizontalLayout_34"));
        groupBox_13 = new QGroupBox(groupBox_9);
        groupBox_13->setObjectName(QString::fromUtf8("groupBox_13"));
        verticalLayout_30 = new QVBoxLayout(groupBox_13);
        verticalLayout_30->setSpacing(6);
        verticalLayout_30->setContentsMargins(11, 11, 11, 11);
        verticalLayout_30->setObjectName(QString::fromUtf8("verticalLayout_30"));
        verticalLayout_31 = new QVBoxLayout();
        verticalLayout_31->setSpacing(6);
        verticalLayout_31->setObjectName(QString::fromUtf8("verticalLayout_31"));
        m_ch3HoldingTimeUnit = new QComboBox(groupBox_13);
        m_ch3HoldingTimeUnit->setObjectName(QString::fromUtf8("m_ch3HoldingTimeUnit"));

        verticalLayout_31->addWidget(m_ch3HoldingTimeUnit);

        m_ch3CurrentTimeUnit = new QLabel(groupBox_13);
        m_ch3CurrentTimeUnit->setObjectName(QString::fromUtf8("m_ch3CurrentTimeUnit"));

        verticalLayout_31->addWidget(m_ch3CurrentTimeUnit);


        verticalLayout_30->addLayout(verticalLayout_31);


        horizontalLayout_34->addWidget(groupBox_13);

        horizontalSpacer_12 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_34->addItem(horizontalSpacer_12);

        verticalLayout_32 = new QVBoxLayout();
        verticalLayout_32->setSpacing(6);
        verticalLayout_32->setObjectName(QString::fromUtf8("verticalLayout_32"));
        m_btnCh3ReadAdvanced = new QPushButton(groupBox_9);
        m_btnCh3ReadAdvanced->setObjectName(QString::fromUtf8("m_btnCh3ReadAdvanced"));

        verticalLayout_32->addWidget(m_btnCh3ReadAdvanced);

        verticalSpacer_12 = new QSpacerItem(20, 40, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_32->addItem(verticalSpacer_12);

        m_btnCh3WriteAdvanced = new QPushButton(groupBox_9);
        m_btnCh3WriteAdvanced->setObjectName(QString::fromUtf8("m_btnCh3WriteAdvanced"));

        verticalLayout_32->addWidget(m_btnCh3WriteAdvanced);


        horizontalLayout_34->addLayout(verticalLayout_32);


        verticalLayout_29->addLayout(horizontalLayout_34);


        verticalLayout_33->addWidget(groupBox_9);


        verticalLayout_34->addLayout(verticalLayout_33);

        tabWidget->addTab(tabAdvanced, QString());
        tabFirmwareUpdate = new QWidget();
        tabFirmwareUpdate->setObjectName(QString::fromUtf8("tabFirmwareUpdate"));
        verticalLayout_38 = new QVBoxLayout(tabFirmwareUpdate);
        verticalLayout_38->setSpacing(6);
        verticalLayout_38->setContentsMargins(11, 11, 11, 11);
        verticalLayout_38->setObjectName(QString::fromUtf8("verticalLayout_38"));
        verticalLayout_37 = new QVBoxLayout();
        verticalLayout_37->setSpacing(6);
        verticalLayout_37->setObjectName(QString::fromUtf8("verticalLayout_37"));
        groupBox_14 = new QGroupBox(tabFirmwareUpdate);
        groupBox_14->setObjectName(QString::fromUtf8("groupBox_14"));
        verticalLayout_36 = new QVBoxLayout(groupBox_14);
        verticalLayout_36->setSpacing(6);
        verticalLayout_36->setContentsMargins(11, 11, 11, 11);
        verticalLayout_36->setObjectName(QString::fromUtf8("verticalLayout_36"));
        verticalLayout_35 = new QVBoxLayout();
        verticalLayout_35->setSpacing(6);
        verticalLayout_35->setObjectName(QString::fromUtf8("verticalLayout_35"));
        horizontalLayout_35 = new QHBoxLayout();
        horizontalLayout_35->setSpacing(6);
        horizontalLayout_35->setObjectName(QString::fromUtf8("horizontalLayout_35"));
        m_filePath = new QLineEdit(groupBox_14);
        m_filePath->setObjectName(QString::fromUtf8("m_filePath"));

        horizontalLayout_35->addWidget(m_filePath);

        m_btnOpenFile = new QPushButton(groupBox_14);
        m_btnOpenFile->setObjectName(QString::fromUtf8("m_btnOpenFile"));

        horizontalLayout_35->addWidget(m_btnOpenFile);


        verticalLayout_35->addLayout(horizontalLayout_35);

        horizontalLayout_36 = new QHBoxLayout();
        horizontalLayout_36->setSpacing(6);
        horizontalLayout_36->setObjectName(QString::fromUtf8("horizontalLayout_36"));
        m_progressBarDownload = new QProgressBar(groupBox_14);
        m_progressBarDownload->setObjectName(QString::fromUtf8("m_progressBarDownload"));
        m_progressBarDownload->setValue(24);

        horizontalLayout_36->addWidget(m_progressBarDownload);

        m_btnDownload = new QPushButton(groupBox_14);
        m_btnDownload->setObjectName(QString::fromUtf8("m_btnDownload"));

        horizontalLayout_36->addWidget(m_btnDownload);


        verticalLayout_35->addLayout(horizontalLayout_36);


        verticalLayout_36->addLayout(verticalLayout_35);


        verticalLayout_37->addWidget(groupBox_14);

        verticalSpacer_13 = new QSpacerItem(20, 40, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_37->addItem(verticalSpacer_13);

        m_downloadStatus = new QLabel(tabFirmwareUpdate);
        m_downloadStatus->setObjectName(QString::fromUtf8("m_downloadStatus"));
        QFont font;
        font.setPointSize(16);
        font.setBold(true);
        font.setWeight(75);
        m_downloadStatus->setFont(font);
        m_downloadStatus->setAlignment(Qt::AlignCenter);

        verticalLayout_37->addWidget(m_downloadStatus);

        verticalSpacer_14 = new QSpacerItem(20, 40, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_37->addItem(verticalSpacer_14);


        verticalLayout_38->addLayout(verticalLayout_37);

        tabWidget->addTab(tabFirmwareUpdate, QString());

        verticalLayout_14->addWidget(tabWidget);

        horizontalLayout_30 = new QHBoxLayout();
        horizontalLayout_30->setSpacing(6);
        horizontalLayout_30->setObjectName(QString::fromUtf8("horizontalLayout_30"));
        horizontalLayout_28 = new QHBoxLayout();
        horizontalLayout_28->setSpacing(6);
        horizontalLayout_28->setObjectName(QString::fromUtf8("horizontalLayout_28"));
        label_3 = new QLabel(lightControlPage);
        label_3->setObjectName(QString::fromUtf8("label_3"));

        horizontalLayout_28->addWidget(label_3);

        m_hardwareVer = new QLabel(lightControlPage);
        m_hardwareVer->setObjectName(QString::fromUtf8("m_hardwareVer"));

        horizontalLayout_28->addWidget(m_hardwareVer);


        horizontalLayout_30->addLayout(horizontalLayout_28);

        horizontalSpacer_7 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_30->addItem(horizontalSpacer_7);

        horizontalLayout_29 = new QHBoxLayout();
        horizontalLayout_29->setSpacing(6);
        horizontalLayout_29->setObjectName(QString::fromUtf8("horizontalLayout_29"));
        label_4 = new QLabel(lightControlPage);
        label_4->setObjectName(QString::fromUtf8("label_4"));

        horizontalLayout_29->addWidget(label_4);

        m_firmwareVer = new QLabel(lightControlPage);
        m_firmwareVer->setObjectName(QString::fromUtf8("m_firmwareVer"));

        horizontalLayout_29->addWidget(m_firmwareVer);

        horizontalSpacer_8 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_29->addItem(horizontalSpacer_8);


        horizontalLayout_30->addLayout(horizontalLayout_29);


        verticalLayout_14->addLayout(horizontalLayout_30);


        verticalLayout_19->addLayout(verticalLayout_14);


        retranslateUi(lightControlPage);
        QObject::connect(m_ch0Slider, SIGNAL(valueChanged(int)), m_ch0SpinBox, SLOT(setValue(int)));
        QObject::connect(m_ch3SpinBox, SIGNAL(valueChanged(int)), m_ch3Slider, SLOT(setValue(int)));
        QObject::connect(m_ch2SpinBox, SIGNAL(valueChanged(int)), m_ch2Slider, SLOT(setValue(int)));
        QObject::connect(m_ch3Slider, SIGNAL(valueChanged(int)), m_ch3SpinBox, SLOT(setValue(int)));
        QObject::connect(m_ch0SpinBox, SIGNAL(valueChanged(int)), m_ch0Slider, SLOT(setValue(int)));
        QObject::connect(m_ch2Slider, SIGNAL(valueChanged(int)), m_ch2SpinBox, SLOT(setValue(int)));
        QObject::connect(m_ch1Slider, SIGNAL(valueChanged(int)), m_ch1SpinBox, SLOT(setValue(int)));
        QObject::connect(m_ch1SpinBox, SIGNAL(valueChanged(int)), m_ch1Slider, SLOT(setValue(int)));

        tabWidget->setCurrentIndex(0);


        QMetaObject::connectSlotsByName(lightControlPage);
    } // setupUi

    void retranslateUi(QWidget *lightControlPage)
    {
        lightControlPage->setWindowTitle(QCoreApplication::translate("lightControlPage", "lightControlPage", nullptr));
        groupBox_6->setTitle(QCoreApplication::translate("lightControlPage", "Com", nullptr));
        m_lblPort->setText(QCoreApplication::translate("lightControlPage", "Port:", nullptr));
        m_lblBaudRate->setText(QCoreApplication::translate("lightControlPage", "BaudRate:", nullptr));
        m_connectBtn->setText(QCoreApplication::translate("lightControlPage", "Connect", nullptr));
        groupBox->setTitle(QCoreApplication::translate("lightControlPage", "CH0", nullptr));
        m_ch0ModeLabel->setText(QCoreApplication::translate("lightControlPage", "Mode:", nullptr));
        m_ch0PwmHoldingTimeLabel->setText(QCoreApplication::translate("lightControlPage", "HoldingTime:", nullptr));
        m_ch0PwmHoldingTime->setSuffix(QString());
        m_ch0ReadBtn->setText(QCoreApplication::translate("lightControlPage", "Read", nullptr));
        m_ch0WriteBtn->setText(QCoreApplication::translate("lightControlPage", "Write", nullptr));
        groupBox_2->setTitle(QCoreApplication::translate("lightControlPage", "CH1", nullptr));
        m_ch1ModeLabel->setText(QCoreApplication::translate("lightControlPage", "Mode:", nullptr));
        m_ch1PwmHoldingTimeLabel->setText(QCoreApplication::translate("lightControlPage", "HoldingTime:", nullptr));
        m_ch1PwmHoldingTime->setSuffix(QString());
        m_ch1PwmHoldingTime->setPrefix(QString());
        m_ch1ReadBtn->setText(QCoreApplication::translate("lightControlPage", "Read", nullptr));
        m_ch1WriteBtn->setText(QCoreApplication::translate("lightControlPage", "Write", nullptr));
        groupBox_3->setTitle(QCoreApplication::translate("lightControlPage", "CH2", nullptr));
        m_ch2ModeLabel->setText(QCoreApplication::translate("lightControlPage", "Mode:", nullptr));
        m_ch2PwmHoldingTimeLabel->setText(QCoreApplication::translate("lightControlPage", "HoldingTime:", nullptr));
        m_ch2PwmHoldingTime->setSuffix(QString());
        m_ch2ReadBtn->setText(QCoreApplication::translate("lightControlPage", "Read", nullptr));
        m_ch2WriteBtn->setText(QCoreApplication::translate("lightControlPage", "Write", nullptr));
        groupBox_4->setTitle(QCoreApplication::translate("lightControlPage", "CH3", nullptr));
        m_ch3ModeLabel->setText(QCoreApplication::translate("lightControlPage", "Mode:", nullptr));
        m_ch3PwmHoldingTimeLabel->setText(QCoreApplication::translate("lightControlPage", "HoldingTime:", nullptr));
        m_ch3PwmHoldingTime->setSuffix(QString());
        m_ch3ReadBtn->setText(QCoreApplication::translate("lightControlPage", "Read", nullptr));
        m_ch3WriteBtn->setText(QCoreApplication::translate("lightControlPage", "Write", nullptr));
        tabWidget->setTabText(tabWidget->indexOf(tabLightControl), QCoreApplication::translate("lightControlPage", "Light Control", nullptr));
        groupBox_5->setTitle(QCoreApplication::translate("lightControlPage", "CH0", nullptr));
        groupBox_10->setTitle(QCoreApplication::translate("lightControlPage", "HoldingTimeUnit", nullptr));
        m_ch0CurrentTimeUnit->setText(QString());
        m_btnCh0ReadAdvanced->setText(QCoreApplication::translate("lightControlPage", "Read", nullptr));
        m_btnCh0WriteAdvanced->setText(QCoreApplication::translate("lightControlPage", "Write", nullptr));
        groupBox_7->setTitle(QCoreApplication::translate("lightControlPage", "CH1", nullptr));
        groupBox_11->setTitle(QCoreApplication::translate("lightControlPage", "HoldingTimeUnit", nullptr));
        m_ch1CurrentTimeUnit->setText(QString());
        m_btnCh1ReadAdvanced->setText(QCoreApplication::translate("lightControlPage", "Read", nullptr));
        m_btnCh1WriteAdvanced->setText(QCoreApplication::translate("lightControlPage", "Write", nullptr));
        groupBox_8->setTitle(QCoreApplication::translate("lightControlPage", "CH2", nullptr));
        groupBox_12->setTitle(QCoreApplication::translate("lightControlPage", "HoldingTimeUnit", nullptr));
        m_ch2CurrentTimeUnit->setText(QString());
        m_btnCh2ReadAdvanced->setText(QCoreApplication::translate("lightControlPage", "Read", nullptr));
        m_btnCh2WriteAdvanced->setText(QCoreApplication::translate("lightControlPage", "Write", nullptr));
        groupBox_9->setTitle(QCoreApplication::translate("lightControlPage", "CH3", nullptr));
        groupBox_13->setTitle(QCoreApplication::translate("lightControlPage", "HoldingTimeUnit", nullptr));
        m_ch3CurrentTimeUnit->setText(QString());
        m_btnCh3ReadAdvanced->setText(QCoreApplication::translate("lightControlPage", "Read", nullptr));
        m_btnCh3WriteAdvanced->setText(QCoreApplication::translate("lightControlPage", "Write", nullptr));
        tabWidget->setTabText(tabWidget->indexOf(tabAdvanced), QCoreApplication::translate("lightControlPage", "Advanced", nullptr));
        groupBox_14->setTitle(QCoreApplication::translate("lightControlPage", "Firmware Update", nullptr));
        m_btnOpenFile->setText(QCoreApplication::translate("lightControlPage", "Open", nullptr));
        m_btnDownload->setText(QCoreApplication::translate("lightControlPage", "Download", nullptr));
        m_downloadStatus->setText(QCoreApplication::translate("lightControlPage", "TextLabel", nullptr));
        tabWidget->setTabText(tabWidget->indexOf(tabFirmwareUpdate), QCoreApplication::translate("lightControlPage", "FirmwareUpdate", nullptr));
        label_3->setText(QCoreApplication::translate("lightControlPage", "HardwareVer:", nullptr));
        m_hardwareVer->setText(QCoreApplication::translate("lightControlPage", "TextLabel", nullptr));
        label_4->setText(QCoreApplication::translate("lightControlPage", "FirmwareVer:", nullptr));
        m_firmwareVer->setText(QCoreApplication::translate("lightControlPage", "TextLabel", nullptr));
    } // retranslateUi

};

namespace Ui {
    class lightControlPage: public Ui_lightControlPage {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_LIGHTCONTROLPAGE_H
