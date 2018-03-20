import setuptools

requirements = []
setuptools.setup(
    name='TF-DATAFLOW-DEMO',
    version='v1',
    install_requires=requirements,
    packages=setuptools.find_packages(),
    package_data={'model': ['trained/*',
                            'trained/v1/*',
                            'trained/v1/variables/*']
                  },
)