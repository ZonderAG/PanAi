from setuptools import find_packages, setup

package_name = 'panai_orchestrator'

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
    description='Orchestrator node for PanAI',
    license='Proprietary',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'orchestrator_node = panai_orchestrator.orchestrator_node:main',
        ],
    },
)
