README
======

pykosimcli
----------
A command line interface tool for kosim model analysis

Supported formats: 
- kosim results database *.kdbf* -

Tool set includes
- graphical display of fiktiv Zentral Becken Fracht und Fracht, spezifische Fracht, Entlastungrate und Entlastungshäufigkeit pro Bauwerk
- parse results to a human readable format
                            
Requires Python 3.7


What is pykosimcli?
---------------
pykosimcli was created in order to run general plausibility tests on kosim models
in order to gain a quick overview as an peer reviewer / auditor. 

Further analysis of specific model parameters can be performed much quicker 
after an initial check and also give the modeller a feedback as to the quality 
of the model. Pykosimcli speeds up the compute --> review --> revise loop 
that is standard in the creation and quality assessment of SF-models.

pykosimcli is still currently under development. If you have any ideas feel free
to contact me at the address below.


How do I get set up?
--------------------

Installation
++++++++++++

Get the repo and install ::

    # clone the repo
    $ git clone https://github.com/sweeneybrian907/pykosimcli.git

    # change the working directory to sherlock
    $ cd pykosimcli

    # install the requirements
    $ python3 -m pip install -r requirements.txt

It is recommended to install the package in a virtual environment 


Further set up
+++++++++++++++++

kdbf files are firebird databases. In order to open them you need either 
a running firebird server on your system or the embedded client dlls. The 
client dlls can be downloaded from the firebird website
(firebird embedded https://github.com/FirebirdSQL/firebird/releases/download/R2_5_9/Firebird-2.5.9.27139-0_Win32_embed.zip).
In order to use the client libraries you need to add the folder path
to the environmental path. If the libraries aren't recognized then you can try
placing the path in the first order of the PATH variable.

On linux or linux emulator this can be done with:

``export PATH=/path/to/lib/folder:$PATH``

If the directory is not added to the path then a WinError 126 will be thrown
when trying to connect to the database.


Dependencies
++++++++++++
fdb, pandas, numpy, xlsxwriter, matplotlib  


How to run tests
++++++++++++++++
Currently there are no tests for the package. Feel free to fork the repo and
write your own. 


Contribution guidelines
-----------------------
feel free to contribute
* Repo owner - Brian Sweeney - sweeneybrian907 at gmail.com
