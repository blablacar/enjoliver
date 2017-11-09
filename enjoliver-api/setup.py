from setuptools import setup

setup(
    name='enjoliver-api',
    packages=['enjoliver'],
    include_package_data=True,
    scripts=[],
    zip_safe=False,
    install_requires=[
        'deepdiff',
        'flasgger',
        'Flask',
        'prometheus_client',
        'psycopg2',
        'requests',
        'sqlalchemy',
    ],
)
