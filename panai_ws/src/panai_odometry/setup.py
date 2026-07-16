from setuptools import find_packages, setup

package_name = 'panai_odometry'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Developer',
    maintainer_email='developer@todo.todo',
    description='Odometry node for PanAI',
    license='Proprietary',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'odometry_node = panai_odometry.odometry_node:main',
        ],
    },
)
