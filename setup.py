from setuptools import find_packages, setup
import os
from glob import glob   

package_name = 'kokoro_tts_ros'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sobits',
    maintainer_email='sobits@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'kokoro_tts_server = kokoro_tts_ros.kokoro_tts_server:main',
            'kokoro_tts_client = kokoro_tts_ros.kokoro_tts_client:main',
        ],
    },
)
