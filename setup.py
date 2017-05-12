from distutils.core import setup

setup (name = "cibot",
       author="Charles Doutriaux",
       version="0.2",
       description = "Utilities for git/github continuous integration",
       url = "http://github.com/uv-cdat/ci-bot",
       packages = ['cibot'],
       package_dir = {'cibot': 'lib'},
       scripts= ["scripts/ci-bot"],
      )
    
