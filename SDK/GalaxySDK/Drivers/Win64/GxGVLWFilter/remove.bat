@echo off
set base_dir=%~dp0
%base_dir:~0,2%
pushd %base_dir% 1>nul 2>&1

SETLOCAL ENABLEEXTENSIONS
SETLOCAL ENABLEDELAYEDEXPANSION

takeown /f "%systemroot%\system32\DriverStore\FileRepository\GxGVLWFilter*" 1>nul 2>&1 && icacls "%systemroot%\system32\DriverStore\FileRepository\GxGVLWFilter*" /grant administrators:F 
takeown /f "%systemroot%\system32\DriverStore\FileRepository\GxGVLWFilter*" /r /d y 1>nul 2>&1 && icacls "%systemroot%\system32\DriverStore\FileRepository\GxGVLWFilter*" /grant administrators:F /t 

dir %systemroot%\system32\DriverStore\FileRepository\GxGVLWFilter* /b >"%cd%\dellist.txt" 2>nul
for /F "usebackq delims=" %%A in ("%cd%\dellist.txt") do (
    RD /S /q %systemroot%\system32\DriverStore\FileRepository\%%A
)

DEL /Q "%cd%\dellist.txt"

ENDLOCAL

@ping 127.0.0.1 -n 3 1>nul 2>&1