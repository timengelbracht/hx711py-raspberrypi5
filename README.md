# HX711 for Raspberry Pi 5 (libgpiod)

This library is based on [HX711 for Rasberry Pi](https://github.com/tatobari/hx711py) using [libgpiod](https://github.com/brgl/libgpiod) instead of RPi.GPIO.

## Motivation for libgpiod on RPi5

Works for reading hx711 on rpi. Not well tested and files like emulated_hx711.py and example.py are from the jetson nano branch i adapted, so just ignore them. I just made this cuz for some reason all hx711 libs dont work for rpi5. 


## Instructions

Check test_example.py to see how it works.

### Requirements
```
sudo apt install -y python3-libgpiod
pip3 install logzero
```

### Everything bleow this block of text ist from the jetson nano fork., wasnt necessary for me, might be hlpful for you ;)

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

