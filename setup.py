#!/usr/bin/env python

from distutils.core import setup
import glob
import os.path

setup( 
    name='Boscli-oss', 
    version='0.2.0', 
    author='Eduardo Ferro Aldama', 
    author_email='eferro@alea-soluciones.com', 
    url='http://oss.alea-soluciones.com/trac/wiki/BoscliOss', 
    desctiption ='Extensible command line processor for "ad hoc" shells creation',
    license='GPL',
    platforms = 'Linux',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Interpreters',
        ],

    package_dir  = { '' : 'src' }, 
    packages = ['boscli', ],
    scripts = ['src/bin/boscli', ],
    data_files = [ ( '/usr/lib/boscli/', 
                     glob.glob( 'src/lib/*.py')  ) ],
)
