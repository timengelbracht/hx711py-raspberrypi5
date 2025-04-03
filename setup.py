from setuptools import setup, find_packages

setup(
    name='hx711',
    version='0.1.0',
    description='HX711 driver for Raspberry Pi 5 using gpiod',
    author='Your Name',
    packages=find_packages(),
    install_requires=[
        'gpiod',
        'logzero'
    ],
    python_requires='>=3.7',
)
