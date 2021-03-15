# Disclaimer:
This system and the ASTERICS Linux Kernel Driver are currently in development and considered as experimental.

# Document
This file was written by Patrick Zacharias and describes how to get this system up and running for the ZYBO board.
It was last modified 03/14/2021 00:34 (CEST)

# Dockerfile to build ASTERICS driver
First copy the .git folder into the Docker folder:

```bash
cp -r ../../../.git asterics.git
```

Then build the image inside the Docker folder:

```bash
docker build -t asterics:latest .
```

Enter container and copy built kernel module:

```bash
docker run -it --entrypoint=/bin/bash -v $(pwd)/output:/mnt asterics:latest
cp /asterics/support/software/as-linux/src/kernel_module/asterics-driver/asterics.ko /mnt
cp /linux-xlnx/arch/arm/boot/uImage /mnt
```

# Install image to microSD
After having built the kernel module, bootloader and initial image in the Docker container,
following steps have to be performed to finish the installation:

Prepare the microSD with the following partition scheme:
200MiB FAT boot partition,
(3.5GiB, but can be more) ext4

You can use the provided text file (sdcard_format.txt) as input for sfdisk,
but be careful as applying it to the wrong disk will lead to data loss.

```bash
sfdisk test.img < ./sdcard_format.txt
```

Afterwards make sure the partitions got rescanned (either by reinserting the microSD card or by using appropriate tools).

Proceed by using mkfs.vfat to format the first partition used for booting (/dev/mmcblkXp1 or /dev/sdXp1 depending on type of reader)
and by using mkfs.ext4 to format the second partition used as rootfs (/dev/mmcblkXp2 or /dev/sdXp2 depending on type of reader).

Mount these partitions rw to locations and memorize their mount points for the following steps.

Enter container and execute last debootstrap process:

```bash
docker run -it --privileged --entrypoint=/bin/bash -v $(pwd)/output:/mnt -v [PATH TO SD CARD ROOTFS]:/sdcard_root asterics_new:latest
```

```bash
chroot /sdcard_root_orig/ sh -c "export LANG=C && /debootstrap/debootstrap --second-stage"
```

Copy the rootfs to the mounted microSD card root partition. (Inside container)
```bash
/copy_root.sh
```

Re-enter container:
```bash
docker run -it --privileged --entrypoint=/bin/bash -v $(pwd)/output:/mnt -v [PATH TO SD CARD BOOT]:/sdcard_boot asterics_new:latest
```

Copy the boot files to the mounter microSD card boot partition. (Inside container)
```bash
/copy.sh
```

# Copy kernel module to board

To copy the kernel module to the board use:

```bash
sudo cp output/asterics.ko [PATH TO ROOTFS]/home/root
```

Compile create-devices and copy it to the board together with load_devices.sh from software/

# Load driver

To load the driver execute

```bash
sudo insmod ~/asterics.ko
cd ~/simple
sudo ./load_devices.sh
```

# Execute tests

To run the unit tests,
execute unit_test as root:

```bash
sudo ./unit_test
```

Use the flag --help for more information.

# Rebuild tests

The tests are located inside software/memory_loop_test
Adjust the path in zynq-toolchain.cmake (one folder above) to point to an existing rootfs folder (if you followed the guide it has been mounted at /media/$USER/rootfs), which contains libraries including the boost unit test framework.
You need to specify the correct cross compiler in CMAKE_C_COMPILER and CMAKE_CXX_COMPILER.
This has only been tested with arm-linux-gnueabihf-g++-8 and 9, make sure you install corresponding package.

Build the tests using:

```bash
cd unit_test_memory_loop
mkdir build-zynq
cd build-zynq
cmake -DCMAKE_TOOLCHAIN_FILE=[Absolute path to]/zynq-toolchain.cmake ..
```


Copy the tests over SSH (when board is powered on and booted into Linux) using:

```bash
scp unit_test zynq@zynq:/home/zynq/
```

# Build create-devices

To build the program necessary to create the devices files visible under /dev,
proceed the same as mentioned in "Rebuild tests", but use the directory "create-devices"
instead of "unit_test_memory_loop".
Be aware, that changes to the system need to be reflected in the respective as_hardware.[hc] files
and require manual editing.

# Build system
Change the directory into the root of the asterics git tree.
Then source the settings.sh file.

```bash
cd ../../
souce ./settings.sh
```

Use the makefile in this folder (as_refdesign_zynq_linux) to build a system.

```bash
make
```

This has been tested with Vivado 2020.2.
After Generation of Bitfile is complete,
you can copy it to the board using:

```bash
scp hardware/build/system.runs/impl_1/design_1_wrapper.bit zynq@zynq:/sdcard/system.bit
```
