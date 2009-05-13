try:
    import setuptools
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import setup, find_packages
setup(name='Vellumbot',
      version='0.6',
      author='Cory Dodt',
      description='Vellumbot D&D robot',
      url='http://goonmill.org/vellumbot/',
      download_url='http://vellumbot-source.goonmill.org/archive/tip.tar.gz',

      packages=find_packages(),

      install_requires=[
          'pysqlite>=2',
          'playtools>=0.3.0',
          'storm>=0.13',
          ],

      package_data={
          'vellumbot': [ ],
        },
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Environment :: Console',
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Games/Entertainment :: Role-Playing',
          'Topic :: Communications :: Chat :: Internet Relay Chat',
          ],

      )
