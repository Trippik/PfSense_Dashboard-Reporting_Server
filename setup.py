from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="PfSense_Dashboard-Data_Reporting_Server",
    version="1.0.x",
    author="Cameron Trippick",
    install_requires=requirements,
    packages=['reporting_server', 'reporting_server.lib'],
    entry_points={
        'console_scripts': [
            'PfSense_Dashboard-Data_Reporting_Server = reporting_server.app:main',
        ]
    }
)