
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include "NKLCLIB.h"
#include "NKIOLIB.h"

// Light control callbacks
static void openPortCB(LC_CALLBACK_ARG_T arg)
{
	if (arg.openComCallbackArg.error)
	{
		printf("Open port error\n\r");
	}
	else
	{
		printf("Open port success\n\r");
		printf("Hardware ver: %d.%d.%d\n\r", arg.openComCallbackArg.hardwareMajorVer,
			   arg.openComCallbackArg.hardwareMinorVer,
			   arg.openComCallbackArg.hardwareRevVer);
		printf("Hardware ver: %d.%d.%d\n\r", arg.openComCallbackArg.firmwareMajorVer,
			   arg.openComCallbackArg.firmwareMinorVer,
			   arg.openComCallbackArg.firmwareRevVer);
	}
}

static void closePortCB(LC_CALLBACK_ARG_T arg)
{
}

static void getPwmParamsCB(LC_CALLBACK_ARG_T arg)
{
	if (arg.getPwmParamsCallbackArg.error)
	{
		printf("get pwm params error\n");
	}
	else
	{
		printf("get pwm params success\n\r");
		switch (arg.getPwmParamsCallbackArg.chIdx)
		{
		case 0x1:
			printf("Ch0:pwmMode:%d pwmHoldingTime:%d pwmValue:%d Status:%d\n",
				   arg.getPwmParamsCallbackArg.pwmMode,
				   arg.getPwmParamsCallbackArg.pwmHoldingTime,
				   arg.getPwmParamsCallbackArg.pwmValue,
				   arg.getPwmParamsCallbackArg.pwmOnOff);
			break;
		case 0x2:
			printf("Ch1:pwmMode:%d pwmHoldingTime:%d pwmValue:%d Status:%d\n",
				   arg.getPwmParamsCallbackArg.pwmMode,
				   arg.getPwmParamsCallbackArg.pwmHoldingTime,
				   arg.getPwmParamsCallbackArg.pwmValue,
				   arg.getPwmParamsCallbackArg.pwmOnOff);
			break;
		case 0x4:
			printf("Ch2:pwmMode:%d pwmHoldingTime:%d pwmValue:%d Status:%d\n",
				   arg.getPwmParamsCallbackArg.pwmMode,
				   arg.getPwmParamsCallbackArg.pwmHoldingTime,
				   arg.getPwmParamsCallbackArg.pwmValue,
				   arg.getPwmParamsCallbackArg.pwmOnOff);
			break;
		case 0x8:
			printf("Ch3:pwmMode:%d pwmHoldingTime:%d pwmValue:%d Status:%d\n",
				   arg.getPwmParamsCallbackArg.pwmMode,
				   arg.getPwmParamsCallbackArg.pwmHoldingTime,
				   arg.getPwmParamsCallbackArg.pwmValue,
				   arg.getPwmParamsCallbackArg.pwmOnOff);
			break;
		default:
			printf("invalid channel index\n\r");
			break;
		}
	}
}

static void setPwmParamsCB(LC_CALLBACK_ARG_T arg)
{
	if (arg.setPwmParamsCallbackArg.error)
	{
		printf("set pwm params error\n");
	}
	else
	{
		printf(" set pwm params success\n\r");
	}
}

static void *lightControlNotifyProcess(void *arg)
{
	for (;;)
	{
		NKLC_Process_Async();
		usleep(10000);
	}
}

void printDeviceList()
{
	printf("Device list supported:");
	printf("\n\t 1:NP-6111-JH2");
	printf("\n\t 2:NP-6111-JH3");
	printf("\n\t 3:NP-6122-H1");
	printf("\n\t 4:NP-6122-JH2");
	printf("\n\t 5:NP-6122-H1B");
	printf("\n\t 6:NP-6122-JH3");
	printf("\n\r");
}

bool getCurrentExecutablePath(char *dirPath)
{
	char *p = NULL;
	const int len = 256;
	char buf[len] = {0};
	int n = readlink("/proc/self/exe", buf, len);

	if (n < 0 || n > len)
	{
		return false;
	}
	else
	{
		if (NULL != (p = strrchr(buf, '/')))
		{
			*p = '\0';
		}
		else
		{
			return false;
		}
		strcpy(dirPath, buf);
		return true;
	}
}

bool getDeviceConfigFile(int devType, char *configFilePath)
{
	char dirPath[256];
	getCurrentExecutablePath(dirPath);
	switch (devType)
	{
	case 1:
		printf("NP-6111-JH2 selected\n\r");
		strcat(dirPath, "/NP-6111-JH2/nkio_config.ini");
		strcpy(configFilePath, dirPath);
		return true;
	case 2:
		printf("NP-6111-JH3 selected\n\r");
		strcat(dirPath, "/NP-6111-JH3/nkio_config.ini");
		strcpy(configFilePath, dirPath);
		return true;
	case 3:
		printf("NP-6122-H1 selected\n\r");
		strcat(dirPath, "/NP-6122-H1/nkio_config.ini");
		strcpy(configFilePath, dirPath);
		return true;
	case 4:
		printf("NP-6122-JH2 selected\n\r");
		strcat(dirPath, "/NP-6122-JH2/nkio_config.ini");
		strcpy(configFilePath, dirPath);
		return true;
	case 5:
		printf("NP-6122-H1B selected\n\r");
		strcat(dirPath, "/NP-6122-H1B/nkio_config.ini");
		strcpy(configFilePath, dirPath);
		return true;
	case 6:
		printf("NP-6122-JH3 selected\n\r");
		strcat(dirPath, "/NP-6122-JH3/nkio_config.ini");
		strcpy(configFilePath, dirPath);
		return true;
	default:
		printf("unsupport devices selected\n\r");
		return false;
	}
}

void printfMenu(int devType)
{
	printf("Option menu:");
	switch (devType)
	{
	case 1:
		printf("\n\t 1: Read input test");
		printf("\n\t 2: Write output test");
		printf("\n\t 3: light control test");
		break;
	case 2:
		printf("\n\t 1: Read input test");
		printf("\n\t 2: Write output test");
		break;
	case 3:
		printf("\n\t 1: Read input test");
		printf("\n\t 2: Write output test");
		printf("\n\t 3: light control test");
		break;
	case 4:
		printf("\n\t 1: Read input test");
		printf("\n\t 2: Write output test");
		printf("\n\t 3: light control test");
		break;
	case 5:
		printf("\n\t 1: Read input test");
		printf("\n\t 2: Write output test");
		break;
	case 6:
		printf("\n\t 1: Read input test");
		printf("\n\t 2: Write output test");
		break;
	default:
		break;
	}
	printf("\n\r");
}

void diTest()
{
	unsigned char diByte0 = 0;
	unsigned char diByte1 = 0;
	printf("Start Read DI value\n\r");
	while (1)
	{
		NKDIO_PollingReadDiByte(0, &diByte0);
		NKDIO_PollingReadDiByte(1, &diByte1);
		printf("Byte0: %x Byte1:%x\n\r", diByte0, diByte1);
		usleep(2000);
	}
}

void doTest()
{
	unsigned char doByte0 = 0xFF;
	unsigned char doByte1 = 0xFF;
	printf("Start Write DO Test\n\r");
	while (1)
	{
		doByte0 = 0xFF;
		doByte1 = 0xFF;
		for (int i = 0; i < 9; i++)
		{
			printf("Byte0:%x Byte1:%x\n\r", doByte0, doByte1);
			NKDIO_PollingWriteDoByte(0, doByte0);
			NKDIO_PollingWriteDoByte(1, doByte1);
			doByte0 = doByte0 << 1;
			doByte1 = doByte1 << 1;
			sleep(1);
		}
	}
}

void lightControlTest()
{
	unsigned short portNum = 3;
	unsigned short chIdx = 0;
	unsigned short pwmMode;
	unsigned short pwmValue;
	unsigned short pwmHoldingTime;
	unsigned short pwmOnOff;
	unsigned short options = 0;
	printf("Plese input the ttyS* port to open:\n\r");
	scanf("%d", &portNum);
	if (NKLC_OpenDevice_Async((unsigned short)portNum, openPortCB) < 0)
	{
		printf("Open device failed\n\r");
		return;
	}
	else
	{
		printf("Please input the channel to test, ch0:0x1, ch1:0x2, ch3:0x4, ch3:0x8;\n\r");
		scanf("%x", &chIdx);
		printf("please input 1 to read the parameters, input 2 to write parameters\n\r");
		scanf("%d", &options);
		switch (options)
		{
		case 1: // read
			NKLC_GetPwmParams_Async(0x01, chIdx, getPwmParamsCB);
			break;
		case 2: // Write
			printf("Please input the ligt control mode: 0:SoftSwitch, 1:HardSwitch, 2:HardTrigger\n\r");
			scanf("%d", &pwmMode);
			if (pwmMode > 1)
			{
				printf("Please input the holding time: 1~255 seconds\n\r");
				scanf("%d", &pwmHoldingTime);
			}
			printf("Please input the light brightness level: 0~100\n\r");
			scanf("%d", &pwmValue);
			printf("Please input the command to switch the light: 0:off, 1:on\n");
			scanf("%d", &pwmOnOff);
			NKLC_SetPwmParams_Async(0x01, chIdx, pwmMode, pwmValue, pwmHoldingTime, pwmOnOff, setPwmParamsCB);
			break;
		default:
			printf("invalid options\n\r");
			break;
		}
	}
}

int main()
{
	int optionNum;
	int devType;
	int ret = -1;
	char configPath[256] = {0};

	pthread_t threadId;
	pthread_attr_t attr;

	printDeviceList();
	printf("Please input the type of the device currently used:\n\r");
	scanf("%d", &devType);
	getDeviceConfigFile(devType, configPath);
	printf("configPath: %s\n\r", configPath);

	// 1: Init the library
	ret = NKDIO_LibraryInit((const char *)configPath);
	if (ret != 0)
	{
		printf("DIO Library initialized failed:%d\n", ret);
	}
	ret = NKLC_LibraryInit((const char *)configPath);
	if (ret != 0)
	{
		printf("LC Library initialized failed:%d\n", ret);
	}
	else
	{
		// 2: Create the serial communication server thread
		if (pthread_attr_init(&attr) != 0)
		{
			printf("Init thread attr failed\n\r");
			return -1;
		}
		else if (pthread_attr_setstacksize(&attr, 3000000) != 0)
		{
			printf("Set the thread stack size failed\n\r");
			return -1;
		}
		else if (pthread_create(&threadId, &attr, lightControlNotifyProcess, 0) != 0)
		{
			printf("Create server thread failed\n\r");
			return -1;
		}
		else
		{
		}
		printf("Library initialized success\n\r");

		printfMenu(devType);
		printf("Plese input the test option:\n\r");
		scanf("%d", &optionNum);
		switch (optionNum)
		{
		case 1:
			diTest();
			break;
		case 2:
			doTest();
			break;
		case 3:
			lightControlTest();
			break;
		default:
			break;
		}
		while (1)
		{
			sleep(1000);
		}
	}

	return 0;
}
