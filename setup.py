from setuptools import setup, find_packages

setup(
    name='oocrawlers',
    version='0.1',
    description="OpenOil crawlers for the aleph system",
    long_description="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    keywords='',
    author='Friedrich Lindenberg',
    author_email='friedrich@pudo.org',
    url='http://openoil.net',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    entry_points={
        'aleph.crawlers': [
            'edgar = oocrawlers.edgar:EdgarCrawler',
            'openoil = oocrawlers.openoil:OpenOilCrawler'
        ]
    },
    tests_require=[]
)
