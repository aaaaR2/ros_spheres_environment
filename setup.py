from setuptools import setup

package_name = "ros_spheres_environment"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="a.whit",
    maintainer_email="nml@whit.contact",
    description="ROS2 package for manipulating a virtual environment in which spherical objects interact in a 3D space.",
    license="Mozilla Public License 2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [],
    },
)
