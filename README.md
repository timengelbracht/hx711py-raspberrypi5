# HX711 for Jetson Nano (libgpiod)

This library is based on [HX711 for Rasberry Pi](https://github.com/tatobari/hx711py) using [libgpiod](https://github.com/brgl/libgpiod) instead of RPi.GPIO.

## Motivation for libgpiod on Jetson Nano

HX711 has a sevior timing requirement while reading data from DOUT. We have only 50us between 1 and 0 of PD_SCK pulse. Original hx711py library uses legacy/slow `/sys/class/gpio` interface with RPi.GPIO so that Jetson Nano violates 50us timing.

libgpiod is the solution using GPIO character device interface, it's faster than /sys/class/gpio interface. Let's use it!


## Instructions

Check example.py to see how it works.

## Prerequirements

### libgpiod

You need to install libgpiod <=v1.6.x because newer version (v2.0) requires Linux kernel 5.5, but Jetson Nano's kernel version is 4.9.

```
sudo apt install autoconf-archive
git clone git://git.kernel.org/pub/scm/libs/libgpiod/libgpiod.git
cd libgpiod
git checkout v1.6.3 -b v1.6.3
./autogen.sh --enable-tools=yes --prefix=/usr/local --enable-bindings-python
make
sudo make install
```

You have to configure something to process libgpiod in user space.


1. Add `/usr/local/lib` line to `/etc/ld.so.conf.d/libgpiod.conf`
2. Rebuild `/etc/ld.so.cache` as the below.

```
sudo ldconfig
```

3. Add the line to `/etc/udev/rules.d/99-gpio.rules` as same as RPi.GPIO setting as the below.

```
SUBSYSTEM=="gpio", KERNEL=="gpiochip*", GROUP="gpio", MODE="0660"
```

4. Reload udev.

```
sudo udevadm control --reload-rules && sudo udevadm trigger
```

5. Confirm the group permission for gpiochips.

```
$ ll /dev/gpio*
crw-rw---- 1 root gpio 254, 0  Mar 24 15:53 /dev/gpiochip0
crw-rw---- 1 root gpio 254, 1  Mar 24 15:53 /dev/gpiochip1
```


## Installation for Jetson Nano

1. Clone or download and unpack this repository
2. In the repository directory, run
```
python setup.py install
```

## Using a 2-channel HX711 module

Channel A has selectable gain of 128 or 64.  Using set_gain(128) or set_gain(64)
selects channel A with the specified gain.

Using set_gain(32) selects channel B at the fixed gain of 32.  The tare_B(),
get_value_B() and get_weight_B() functions do this for you.

This info was obtained from an HX711 datasheet located at
https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf

