#include "mainWindow.h"
#include <QApplication>
#include <qdesktopwidget.h>
#include <QLibrary>
#include <qtranslator.h>
#include <qfile.h>
#include <QDebug>
#include "loginDialog.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    qApp->setStyleSheet("QTabWidget{background-color: gray}");

    loginDialog *pLoginDialog = new loginDialog();
    if (pLoginDialog->exec() == QDialog::Accepted)
    {
        mainWindow *w = new mainWindow();
        w->setFixedSize(1024, 768);
        w->move((QApplication::desktop()->width() - w->width()) / 2,
            (QApplication::desktop()->height() - w->height()) / 2);
        w->setWindowIcon(QIcon(":/resources/logo.svg"));
        w->show();

        return a.exec();
    }
    else
    {
        delete pLoginDialog;
        return 0;
    }
}
