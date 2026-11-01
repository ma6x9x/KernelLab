# KernelLab.app — rootless SpringBoard application over /var/jb/usr/bin/kernellab.
# Ubuntu CI does not run this Makefile (no Theos, no iOS SDK).
# The deb ships app/prebuilt/KernelLab.app, a signed arm64 Mach-O.
# `make -C app` on a Theos machine replaces that binary; packaging prefers
# the .theos bundle when its executable is Mach-O.
#
#   export THEOS=~/theos
#   make -C app clean all
#   ./packaging/build.sh

export THEOS_PACKAGE_SCHEME := rootless
TARGET := iphone:clang:latest:15.0
ARCHS := arm64
INSTALL_TARGET_PROCESSES := SpringBoard

include $(THEOS)/makefiles/common.mk

APPLICATION_NAME := KernelLab

KernelLab_FILES := $(wildcard Sources/*.swift)
KernelLab_FRAMEWORKS := UIKit SwiftUI
KernelLab_CODESIGN_FLAGS := -Sentitlements.plist
KernelLab_INSTALL_PATH := /Applications

include $(THEOS_MAKE_PATH)/application.mk
