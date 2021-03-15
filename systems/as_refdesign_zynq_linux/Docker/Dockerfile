FROM debian:stretch

MAINTAINER Patrick Zacharias <patrick.zacharias@yahoo.de>

ENV KERNEL_VERSION efb8afa6517cc706ac1a722ab5551984c15932b2

ENV DEBIAN_FRONTEND noninteractive

# Host gcc is required to build scripts
RUN apt-get -y update \
	&& apt-get -y install ca-certificates \
    && apt-get -y --no-install-recommends install \
        autoconf \
        cmake \
        doxygen \
        gcc-arm-linux-gnueabihf \
        git \
		bison \
		flex \
		bc \
		u-boot-tools \
    && git clone https://github.com/Xilinx/linux-xlnx.git /linux-xlnx \
    && cd /linux-xlnx \
    && git checkout -qf $KERNEL_VERSION

RUN apt-get -y install make gcc

COPY kern_conf /linux-xlnx/.config
COPY zynq-zybo.dts /linux-xlnx/arch/arm/boot/dts
    
RUN cd /linux-xlnx \
	&& make CROSS_COMPILE=arm-linux-gnueabihf- ARCH=arm olddefconfig \
	&& make CROSS_COMPILE=arm-linux-gnueabihf- ARCH=arm LOADADDR=0x8000 uImage

COPY asterics.git /asterics.git
RUN git clone /asterics.git /asterics
WORKDIR /asterics/support/software/as-linux/src/kernel_module/asterics-driver
RUN make

ENV U_BOOT_VERSION dc61275b1d505f6a236de1c5b0f35485914d2bcc
WORKDIR /
RUN cd / && git clone https://github.com/Xilinx/u-boot-xlnx.git \
    && cd /u-boot-xlnx \
    && git checkout -qf $U_BOOT_VERSION

RUN apt-get -y install libssl-dev
WORKDIR /u-boot-xlnx
RUN make CROSS_COMPILE=arm-linux-gnueabihf- ARCH=arm zynq_zybo_config \
    && make CROSS_COMPILE=arm-linux-gnueabihf- ARCH=arm -j$(nproc)

RUN apt-get -y install nano debootstrap
#RUN apt-get -y install dosfstools nano fuseext2
# RUN fallocate -l 3.5G /sdcard_rootfs.img
RUN cd /linux-xlnx \
        && make CROSS_COMPILE=arm-linux-gnueabihf- ARCH=arm zynq-zybo.dtb

# ROOTFS preperation begins below
RUN apt-get -y install qemu-user-static

RUN debootstrap --arch=armhf --foreign bullseye /sdcard_root_orig

RUN cp /usr/bin/qemu-arm-static /sdcard_root_orig/usr/bin/ \
	&& cp /etc/resolv.conf /sdcard_root_orig/etc/

# Uncommented because privileged container would be required during build (does not work)
#RUN chroot /sdcard_root_orig/ sh -c "export LANG=C && /debootstrap/debootstrap --second-stage"
RUN apt-get -y install rsync
WORKDIR /
RUN echo "#!/bin/sh \n \
rsync -avP --numeric-ids --exclude='/dev' --exclude='/proc' --exclude='/sys' /sdcard_root_orig/ /sdcard_root \n \
echo \"/dev/mmcblk0p1  /sdcard auto     defaults             0                  0\" > /sdcard_root/etc/fstab" > /copy_root.sh \
	&& chmod +x /copy_root.sh

# Create the copy script to be executed by user after build
RUN echo "IyEvYmluL3NoCgpjcCAvbGludXgteGxueC9hcmNoL2FybS9ib290L2R0cy96eW5xLXp5Ym8uZHRiIC9zZGNhcmRfYm9vdC8KY3AgL2xpbnV4LXhsbngvYXJjaC9hcm0vYm9vdC91SW1hZ2UgL3NkY2FyZF9ib290LwoKY3AgL3UtYm9vdC14bG54L3UtYm9vdC5pbWcgL3NkY2FyZF9ib290LwpjcCAvdS1ib290LXhsbngvc3BsL2Jvb3QuYmluIC9zZGNhcmRfYm9vdC8KCmNhdCA8PEVPRiA+IC9zZGNhcmRfYm9vdC91RW52LnR4dApib290YXJncz1yb290PS9kZXYvbW1jYmxrMHAyIHJ3IHJvb3R3YWl0CmJvb3RjbWQ9ZmF0bG9hZCBtbWMgMCAweDEwMDAwMCBzeXN0ZW0uYml0OyBmcGdhIGxvYWRiIDAgMHgxMDAwMDAgM2RiYjczOyBmYXRsb2FkIG1tYyAwIDB4MzAwMDAwMCB1SW1hZ2U7IGZhdGxvYWQgbW1jIDAgMHgyZmYwMDAwIHp5bnEtenliby5kdGI7IGJvb3RtIDB4MzAwMDAwMCAtIDB4MmZmMDAwMAp1ZW52Y21kPWJvb3QKRU9GCgoK" | base64 -d > /copy.sh \
	&& chmod +x /copy.sh
