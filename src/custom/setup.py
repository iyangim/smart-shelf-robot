from setuptools import find_packages, setup

package_name = 'smart_shelf_robot'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='iyangim',
    maintainer_email='iyangim@todo.todo',
    description='Smart Shelf Robot custom controllers and integration nodes',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'vla_bridge_node = custom.integration.vla_bridge_node:main',
            'diffusion_inference_node = custom.integration.diffusion_inference_node:main',
            'main_controller_node = custom.integration.main_controller_node:main',
        ],
    },
)
