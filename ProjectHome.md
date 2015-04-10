**NOTE: We are no longer actively checking in code here as we've switched project hosting to [Github](https://github.com/wnd-charm/wnd-charm).** This site will be retired soon.

The current release is v1.52, available here: [wndchrm-1.52.775.tar.gz](http://ome.grc.nia.nih.gov/wnd-charm/wndchrm-1.52.775.tar.gz)

WND-CHARM is a multi-purpose image classifier that can be applied to a wide variety of image classification tasks without modifications or fine-tuning, and yet provides classification accuracy comparable to state-of-the-art task-specific image classifiers. Wndchrm can extract up to ~3,000 generic image descriptors (features) including polynomial decompositions, high contrast features, pixel statistics, and textures. These features are derived from the raw image, transforms of the image, and compound transforms of the image (transforms of transforms). The features are filtered and weighted depending on their effectiveness in discriminating between a set of pre-defined image classes (the training set). These features are then used to classify test images based on their similarity to the training classes. This classifier was tested on a wide variety of imaging problems including biological and medical image classification using several imaging modalities, face recognition, and other pattern recognition tasks. WND-CHARM is an acronym that stands for _weighted neighbor distance_ using _compound hierarchy_ of _algorithms representing morphology_.

The current implementation is a command-line program that reads a directory hierarchy containing image files, with one class per directory.  The primary output is an html report containing classifier statistics (accuracy, predictions, interpolations, etc.), and/or plain text (i.e. stdout).

This research was supported entirely by the Intramural Research Program of the National Institutes of Health, National Institute on Aging, Ilya Goldberg, Investigator. Address: Laboratory of Genetics/NIA/NIH, 251 Bayview Blvd., Suite 100, Baltimore, MD, 21224, USA


---


A full description of the wndchrm utility can be found at:

[Shamir L, Orlov N, Eckley DM, Macura T, Johnston J, Goldberg IG, Wndchrm - an open source utility for biological image analysis. BMC Source Code for Biology and Medicine. 3: 13, 2008.](http://www.scfbm.org/content/3/1/13)  ([PDF download](http://ome.grc.nia.nih.gov/wnd-charm/BMC-wndchrm-utility.pdf))

The wndchrm utility is an implementation of the WND-CHARM algorithm described here:

[WND-CHARM: Multi-purpose image classification using compound image transforms. Orlov N, Shamir L, Macura T, Johnston J, Eckley DM, Goldberg IG Pattern Recognition Letters. 29(11): 1684-93, 2008.](http://ome.grc.nia.nih.gov/wnd-charm/PRL_2008.pdf)


---

  * Dependencies: Installation of Wndchrm requires a C compiler, LibTIFF and FFTW
    * We use GCC 4.2 on MacOS, and 4.4/4.6 on Linux
    * LibTIFF 3.x: http://www.libtiff.org
      * `CentOS/RedHat`: sudo yum install libtiff-devel
      * Ubuntu/Debian: sudo apt-get libtiff4-dev
    * FFTW 3.x: http://www.fftw.org/download.html
      * `CentOS/RedHat`: sudo yum install fftw-static fftw-devel
      * Ubuntu/Debian: sudo apt-get libfftw3-dev
    * Optional for dendrograms: PHYLIP http://evolution.genetics.washington.edu/phylip/install.html
      * Some X11 libraries must be installed prior to compiling/installing PHYLIP ("make install" in the src dir.)
        * `CentOS/RedHat`: sudo yum install libX11-devel libXt-devel libXaw-devel
        * Ubuntu/Debian: sudo apt-get install libX11-dev libxt-dev libxaw7-dev
  * Recommended Hardware: 2 GB RAM (per core), 10 GB HD space, 2 GHZ CPU. Please be aware that this utility is very computationally intensive. Multiple instances of wndchrm can work concurrently on the same dataset on multi-core/multi-processor CPUs. Simply use the same command line to launch as many instances of wndchrm as there are CPU cores available.
  * Wndchrm was tested using Linux (Ubuntu, CentOS) and MacOS X, but should also run with other Unix and Linux distributions.


---


Please also visit the [IICBU Biological Image Repository](http://ome.grc.nia.nih.gov/iicbu2008/), which provides a benchmark for testing and comparing the performance of image analysis algorithms for biological imaging.