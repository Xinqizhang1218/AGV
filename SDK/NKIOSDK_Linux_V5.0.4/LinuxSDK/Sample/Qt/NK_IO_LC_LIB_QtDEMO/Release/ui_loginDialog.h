/********************************************************************************
** Form generated from reading UI file 'loginDialog.ui'
**
** Created by: Qt User Interface Compiler version 5.13.2
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_LOGINDIALOG_H
#define UI_LOGINDIALOG_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QDialog>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QLabel>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QSpacerItem>
#include <QtWidgets/QVBoxLayout>

QT_BEGIN_NAMESPACE

class Ui_loginDialog
{
public:
    QVBoxLayout *verticalLayout_2;
    QVBoxLayout *verticalLayout;
    QLabel *label_2;
    QSpacerItem *verticalSpacer_2;
    QHBoxLayout *horizontalLayout;
    QLabel *label;
    QComboBox *comboBox;
    QSpacerItem *verticalSpacer;
    QHBoxLayout *horizontalLayout_2;
    QPushButton *m_btnExit;
    QSpacerItem *horizontalSpacer_2;
    QPushButton *m_btnAccept;

    void setupUi(QDialog *loginDialog)
    {
        if (loginDialog->objectName().isEmpty())
            loginDialog->setObjectName(QString::fromUtf8("loginDialog"));
        loginDialog->setWindowModality(Qt::ApplicationModal);
        loginDialog->resize(400, 200);
        loginDialog->setMinimumSize(QSize(400, 200));
        loginDialog->setMaximumSize(QSize(400, 200));
        loginDialog->setStyleSheet(QString::fromUtf8("background-color: rgb(85, 170, 255);"));
        verticalLayout_2 = new QVBoxLayout(loginDialog);
        verticalLayout_2->setSpacing(6);
        verticalLayout_2->setContentsMargins(11, 11, 11, 11);
        verticalLayout_2->setObjectName(QString::fromUtf8("verticalLayout_2"));
        verticalLayout = new QVBoxLayout();
        verticalLayout->setSpacing(6);
        verticalLayout->setObjectName(QString::fromUtf8("verticalLayout"));
        label_2 = new QLabel(loginDialog);
        label_2->setObjectName(QString::fromUtf8("label_2"));
        QFont font;
        font.setPointSize(20);
        font.setBold(true);
        font.setWeight(75);
        label_2->setFont(font);
        label_2->setAlignment(Qt::AlignCenter);

        verticalLayout->addWidget(label_2);

        verticalSpacer_2 = new QSpacerItem(20, 40, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout->addItem(verticalSpacer_2);

        horizontalLayout = new QHBoxLayout();
        horizontalLayout->setSpacing(6);
        horizontalLayout->setObjectName(QString::fromUtf8("horizontalLayout"));
        label = new QLabel(loginDialog);
        label->setObjectName(QString::fromUtf8("label"));
        label->setMinimumSize(QSize(100, 0));
        label->setMaximumSize(QSize(100, 16777215));
        QFont font1;
        font1.setPointSize(14);
        font1.setBold(true);
        font1.setWeight(75);
        label->setFont(font1);
        label->setStyleSheet(QString::fromUtf8(""));

        horizontalLayout->addWidget(label);

        comboBox = new QComboBox(loginDialog);
        comboBox->setObjectName(QString::fromUtf8("comboBox"));
        QFont font2;
        font2.setPointSize(14);
        comboBox->setFont(font2);
        comboBox->setStyleSheet(QString::fromUtf8("\n"
"background-color: rgb(255, 255, 255);"));

        horizontalLayout->addWidget(comboBox);


        verticalLayout->addLayout(horizontalLayout);

        verticalSpacer = new QSpacerItem(20, 40, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout->addItem(verticalSpacer);

        horizontalLayout_2 = new QHBoxLayout();
        horizontalLayout_2->setSpacing(6);
        horizontalLayout_2->setObjectName(QString::fromUtf8("horizontalLayout_2"));
        m_btnExit = new QPushButton(loginDialog);
        m_btnExit->setObjectName(QString::fromUtf8("m_btnExit"));
        m_btnExit->setFont(font2);
        m_btnExit->setStyleSheet(QString::fromUtf8("background-color: rgb(255, 255, 255);"));
        m_btnExit->setAutoDefault(false);

        horizontalLayout_2->addWidget(m_btnExit);

        horizontalSpacer_2 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_2->addItem(horizontalSpacer_2);

        m_btnAccept = new QPushButton(loginDialog);
        m_btnAccept->setObjectName(QString::fromUtf8("m_btnAccept"));
        m_btnAccept->setFont(font2);
        m_btnAccept->setStyleSheet(QString::fromUtf8("background-color: rgb(255, 255, 255);"));

        horizontalLayout_2->addWidget(m_btnAccept);


        verticalLayout->addLayout(horizontalLayout_2);


        verticalLayout_2->addLayout(verticalLayout);


        retranslateUi(loginDialog);

        QMetaObject::connectSlotsByName(loginDialog);
    } // setupUi

    void retranslateUi(QDialog *loginDialog)
    {
        loginDialog->setWindowTitle(QCoreApplication::translate("loginDialog", "Select Product", nullptr));
        label_2->setText(QCoreApplication::translate("loginDialog", "NODKA NP-61xx Series", nullptr));
        label->setText(QCoreApplication::translate("loginDialog", "Product:", nullptr));
        m_btnExit->setText(QCoreApplication::translate("loginDialog", "&Exit", nullptr));
        m_btnAccept->setText(QCoreApplication::translate("loginDialog", "&Accept", nullptr));
    } // retranslateUi

};

namespace Ui {
    class loginDialog: public Ui_loginDialog {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_LOGINDIALOG_H
