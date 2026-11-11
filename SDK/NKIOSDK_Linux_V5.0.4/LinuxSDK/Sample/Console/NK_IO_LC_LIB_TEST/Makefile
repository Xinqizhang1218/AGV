###########################################################################################
#
# Makefile to generate nk_io_lc_lib test under linux
#
# Tom Dong
#
# (C) Copyright Suzhou Nodka Automation technology Co.,Ltd. 
#
###########################################################################################

RM := rm -rf

LIBS := -lNKLCLIB -lNKIOLIB -lpthread -lrt
IDE_LIB = ${LIB_PATH}
IDE_LIB += -L./


EXENAME = ./bin/NK_IO_LC_TEST
OBJDIR = ./obj

# Add inputs and outputs from these tool invocations to the build variables
CPP_SRCS = $(wildcard *.cpp)
CPPOBJS = $(patsubst %.cpp, $(OBJDIR)/%.o, $(CPP_SRCS))

#---------------------------------------------------------------------------------
#-------- Toolchain (need to be changed according to the customer settings)-------
IDE_INCLUDES   =  ${INCLUDE_PATH}
ADD_INCLUDES   = -I./

#---------------------------------------------------------------------------------
#----------------------------- C Compiler ----------------------------------------
#CC            = ${TOOL_PATH}/${TOOL_PREFIX}gcc
CC            = gcc
CFLAGS	      = -O2 -Wall -c -fmessage-length=0 -fno-strict-aliasing -fno-stack-protector
CFLAGS       += $(IDE_INCLUDES) 
CFLAGS       += $(ADD_INCLUDES) 

#---------------------------------------------------------------------------------
#---------------------------- Assembler Compiler ---------------------------------
# AS            = ${TOOL_PATH}/${TOOL_PREFIX}as
AS            = as

#---------------------------------------------------------------------------------
#---------------------------- Compiling C++ code ---------------------------------
#CPP           = ${TOOL_PATH}/${TOOL_PREFIX}g++
CPP           = g++
CPPFLAGS      = -O2 -Wall -c -fmessage-length=0 -fno-strict-aliasing -fno-stack-protector
CPPFLAGS     += $(IDE_INCLUDES) 
CPPFLAGS     += $(ADD_INCLUDES) 

#---------------------------------------------------------------------------------
#---------------------------- Library --------------------------------------------
AR           = ${TOOL_PATH}/${TOOL_PREFIX}ar
ARFLAGS      = -r

#---------------------------------------------------------------------------------
#---------------------------------------------------------------------------------
# All Target
all: $(EXENAME)

# Tool invocations
$(EXENAME): $(CPPOBJS)
	@echo 'Building target'
	@echo 'Invoking: GCC C++ Linker'
	g++  -o $(EXENAME)  $(CPPOBJS) ${IDE_LIB} $(LIBS)
	@echo 'Finished building target'
	@echo ' '

# Other Targets
clean:
	-$(RM) $(CPPOBJS) $(EXENAME)
	-@echo ' '


$(OBJDIR)/%.o : %.cpp
	$(CPP) $(CPPFLAGS) -c $^  -o $@



