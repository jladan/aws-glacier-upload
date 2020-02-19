from setuptools import setup

setup(
    # Needed to silence warnings
    name='aws-glacier-upload',
    url='https://github.com/jladan/aws-glacier-upload.git',
    author='John Ladan',
    author_email='john@ladan.ca',
    # Needed to actually package something
    #packages=['backup'],
    # Needed for dependencies
    install_requires=['boto3', 'tqdm'],
    # *strongly* suggested for sharing
    version='0.1.0',
    license='MIT',
    description='A script/module to perform multi-part uploads to AWS S3 Glacier',
    long_description=open('README.md').read(),
    # if there are any scripts
    scripts=[
        'backup.py',
        ],

)
