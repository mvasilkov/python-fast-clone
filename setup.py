from setuptools import find_packages, setup

if __name__ == '__main__':
    setup(
        name='fastclone',

        version='0.0.1',

        description='',
        long_description='',

        url='https://github.com/mvasilkov/python-fast-clone',

        author='Mark Vasilkov',
        author_email='mvasilkov@gmail.com',

        license='MIT',

        classifiers=[
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3 :: Only',
        ],

        keywords='',

        packages=find_packages(),
        include_package_data=True,

        install_requires=[
            'oslo.concurrency>=3.27.0',
        ]
    )
