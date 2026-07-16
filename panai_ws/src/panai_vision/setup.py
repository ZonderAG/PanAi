from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'panai_vision'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'pyyaml', 'numpy', 'opencv-python'],
    package_data={
        'panai_vision': ['crack_scanner/config/*', 'crack_scanner/calib/*'],
    },
    zip_safe=True,
    maintainer='Developer',
    maintainer_email='developer@todo.todo',
    description='Vision node wrapping crack_scanner',
    license='Proprietary',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'vision_node = panai_vision.vision_node:main',
        ],
    },
)
