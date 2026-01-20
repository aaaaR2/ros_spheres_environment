"""ROS2 publishers and subscribers for interacting with spherical
    objects contained within a 3D environment.

Examples
--------
Create a spheres environment. This object organizes data structures and methods
relevant to modeling a environment in which spherical objects interact in a
3D virtual space.

>>> import spheres_environment
>>> environment = spheres_environment.Environment()

Initialize a ROS2 interface.

>>> import rclpy
>>> rclpy.init()

Define shorthand for updating (i.e., spinning) nodes in the ROS2 environment.

>>> spin = lambda n: rclpy.spin_once(n, timeout_sec=0.010)




>>> import rclpy.node
>>> server_node = rclpy.node.Node('server')
>>> client_node = rclpy.node.Node('client')

>>> server = Server(node=server_node, environment=environment)
>>> client = Client(node=client_node)


>>> environment
{}

>>> client.initialize_object('cursor')
>>> spin(client_node)
>>> spin(server_node)

Confirm that the request from the client has been received, and a new object
has been initialized in the remote environment.

>>> environment
{'cursor': {}}




Clean up the ROS2 nodes and shut down the ROS2 interface.

>>> client_node.destroy_node()
>>> server_node.destroy_node()
>>> rclpy.shutdown()

"""

# Copyright 2022 Carnegie Mellon University Neuromechatronics Lab (a.whit)
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Contact: a.whit (nml@whit.contact)

# Local imports
from ros_spheres_environment.client import Environment as Client
from ros_spheres_environment.messages import (
    position_message,
    radius_message,
    spawn_message,
)
from ros_spheres_environment.server import Server

# Main.
if __name__ == "__main__":
    import doctest

    doctest.testmod()
