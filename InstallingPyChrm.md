# Introduction #

This document explains how to install PyChrm: the Python implementation of the WND-CHARM algorithm.

Our server nodes are octocore AMD x86-64 running CentOS 6, and our compiler is gcc 4.6.6. Note that Pychrm is under active development, and the hope is to reduce the number of dependencies required to install and run it.


# Details #

  * If you are a member of the development team, you can check out a copy of the source tree using the command `svn checkout https://wnd-charm.googlecode.com/svn/ wnd-charm --username your_wndchrm_project_username@nih.gov`. See http://code.google.com/p/wnd-charm/source/checkout for more details
  * You should install the easy\_install utility using the command `sudo yum install python-setuptools python-setuptools-devel`
  * PyChrm uses the SWIG utility, which also requires the python development package: `sudo yum install swig python-devel`
  * Finally, Pychrm requires the popular packages numpy, scipy, and matplotlib to manipulate data and matrices and create plots:`sudo yum install numpy scipy matplotlib`
  * Now navigate to the directory in the source code where Pychrm lives:` cd /path/to/the_code_you_checked_out_from_step_one_above/wnd-charm/pychrm/trunk`
  * Build Pychrm: `python setup.py build`
  * Install Pychrm: `sudo python setup.py install`