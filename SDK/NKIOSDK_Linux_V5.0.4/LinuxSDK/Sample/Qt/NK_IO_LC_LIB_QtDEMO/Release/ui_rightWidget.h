/********************************************************************************
** Form generated from reading UI file 'rightWidget.ui'
**
** Created by: Qt User Interface Compiler version 5.13.2
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_RIGHTWIDGET_H
#define UI_RIGHTWIDGET_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_rightWidget
{
public:

    void setupUi(QWidget *rightWidget)
    {
        if (rightWidget->objectName().isEmpty())
            rightWidget->setObjectName(QString::fromUtf8("rightWidget"));
        rightWidget->resize(400, 300);

        retranslateUi(rightWidget);

        QMetaObject::connectSlotsByName(rightWidget);
    } // setupUi

    void retranslateUi(QWidget *rightWidget)
    {
        rightWidget->setWindowTitle(QCoreApplication::translate("rightWidget", "rightWidget", nullptr));
    } // retranslateUi

};

namespace Ui {
    class rightWidget: public Ui_rightWidget {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_RIGHTWIDGET_H
