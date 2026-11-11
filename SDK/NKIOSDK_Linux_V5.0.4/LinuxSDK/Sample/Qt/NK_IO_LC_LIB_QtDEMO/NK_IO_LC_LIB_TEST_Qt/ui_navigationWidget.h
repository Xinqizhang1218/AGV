/********************************************************************************
** Form generated from reading UI file 'navigationWidget.ui'
**
** Created by: Qt User Interface Compiler version 5.13.2
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_NAVIGATIONWIDGET_H
#define UI_NAVIGATIONWIDGET_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_navigationWidget
{
public:

    void setupUi(QWidget *navigationWidget)
    {
        if (navigationWidget->objectName().isEmpty())
            navigationWidget->setObjectName(QString::fromUtf8("navigationWidget"));
        navigationWidget->resize(400, 300);

        retranslateUi(navigationWidget);

        QMetaObject::connectSlotsByName(navigationWidget);
    } // setupUi

    void retranslateUi(QWidget *navigationWidget)
    {
        navigationWidget->setWindowTitle(QCoreApplication::translate("navigationWidget", "navigationWidget", nullptr));
    } // retranslateUi

};

namespace Ui {
    class navigationWidget: public Ui_navigationWidget {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_NAVIGATIONWIDGET_H
