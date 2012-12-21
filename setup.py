from distutils.core import setup

setup(
  name='Burlap',
  version='0.0.1',
  author='Chun',
  author_email='chun@localhost',
  packages=['burlap'],
  description='Personal Python Fabric Utils',
  long_description='Personal Python Fabric Utils',
  install_requires=[
    "fabric >= 1.5",
  ],
)
