#!/usr/bin/env python3

from setuptools import setup, find_packages, findall

setup(
    maintainer='BlaBlaCar',
    maintainer_email='team-arch@blablacar.com',
    name='enjoliver-api',
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={
        'enjoliver': ['configs.yaml']
    },
    data_files=[
        ('static', findall('static')),
        ('templates', findall('templates')),
    ],
    scripts=[],
    zip_safe=False,
    install_requires=[
        'boto3',
        'deepdiff',
        'flasgger',
        'flask',
        'prometheus_client',
        'psutil',
        'psycopg2',
        'requests',
        'sqlalchemy',
        'werkzeug<0.13',
    ],
)
