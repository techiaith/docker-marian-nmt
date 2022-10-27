from setuptools import setup, find_namespace_packages

packages = find_namespace_packages('src')


setup(
    name='techiaith-marian-nmt-lab',
    version='22.10',
    packages=packages,
    package_dir={'': 'src'},
    package_data={'bombe.translation.api.data': [
        'example_translation_request.json'
    ]},
    include_package_data=True,
    extras_require={
        'dev': ['gitpython', 'virtualenvwrapper', 'pytest']
    })
