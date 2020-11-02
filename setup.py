from setuptools import setup, find_packages

setup(
    name = 'gpuutil',
    version = '0.0.1',
    keywords='gpu utils',
    description = 'A tool for observing gpu stat and auto set visible gpu in python code.',
    license = 'MIT License',
    url = '',
    author = 'zmy',
    author_email = 'izmy@qq.com',
    packages = find_packages(),
    include_package_data = True,
    platforms = 'any',
    install_requires = [],
)
