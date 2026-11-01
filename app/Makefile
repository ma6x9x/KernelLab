# KernelLab.app — rootless SpringBoard shell over /var/jb/usr/bin/kernellab.
# Ubuntu CI does not run this Makefile (no Theos, no iOS SDK).
# packaging/build.sh still stages Applications/KernelLab.app.
#
# On a Mac with Theos:
#   export THEOS=~/theos
#   make -C app clean all
#   ./packaging/build.sh
#
# `make all` writes the bundle under app/.theos. The packaging script
# prefers app/prebuilt/KernelLab.app, then that Theos bundle, then the
# source layout (Info.plist + icons, no Mach-O).

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
