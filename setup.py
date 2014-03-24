from distutils.core import setup

setup(
  name='PyMoJo',
  version='0.2.4',
  author='Ryan Jung',
  author_email='gradysghost@gmail.com',
  packages=['pymojo'],
  url='https://github.com/GradysGhost/pymojo',
  license='LICENSE',
  description='PyJoJo client library',
  long_description=open('README.txt').read(),
  install_requires=[
    'requests == 1.1.0'
  ]
)
