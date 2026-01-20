"""Interface for exposing a `spheres_environment` to a ROS2 graph, such that
    the properties of objects in the environment can be manipulated by remote
    nodes.

Examples
--------

Create a spheres environment. This object organizes data structures and methods
relevant to modeling a environment in which spherical objects interact in a
3D virtual space.

>>> environment = spheres_environment.Environment()

Initialize a ROS2 interface.

>>> import rclpy
>>> rclpy.init()

Define shorthand for updating (i.e., spinning) nodes in the ROS2 environment.

>>> spin = lambda n: rclpy.spin_once(n, timeout_sec=0.010)

Create a ROS2 node to act as a "server" for the environment. This node will
receive ROS2 messages that request changes to the environment. For example, a
subset of messages will be used to update property values for the objects in
the environment.

>>> import rclpy.node
>>> server_node = rclpy.node.Node('server')

Link the virtual environment to the ROS2 interface by creating a ROS2
subscription for initializing objects in the virtual environment.

>>> callback = lambda msg: environment.initialize_object(key=msg.data)
>>> sub = server_node.create_subscription(msg_type=spawn_message,
...                                       topic='initialize',
...                                       callback=callback,
...                                       qos_profile=qos.SYSTEM_DEFAULT.value)

Create a ROS2 client node. This node will act as an interface for sending
messages to the server, such that the virtual environment can be modified
remotely.

>>> client_node = rclpy.node.Node('client')
>>> client = Environment(node=client_node)

Confirm that the environment is in the baseline state, with no objects
initialized.

>>> environment
{}

Use the client to request initialization of an object in the remote virtual
environment. In order for the request / message to be transmitted, both the
client and server nodes must be spun. Spinning the client sends the ROS2
message requesting object initialization. Spinning the server causes the
message to be processed on the remote end of the ROS2 topic.

>>> client.initialize_object('cursor')
>>> spin(client_node)
>>> spin(server_node)

Confirm that the request from the client has been received, and a new object
has been initialized in the remote environment.

>>> environment
{'cursor': {}}

Initialize a subscription for modifying the spherical cursor radius.

>>> def callback(msg): environment['cursor'].radius = msg.data
>>> sub = server_node.create_subscription(msg_type=radius_message,
...                                       topic='cursor/radius',
...                                       callback=callback,
...                                       qos_profile=qos.SYSTEM_DEFAULT.value)

Test the new subscription.

>>> client['cursor'].radius = 0.10
>>> spin(client_node)
>>> spin(server_node)
>>> environment
{'cursor': {'radius': 0.1}}

Initialize a subscription for modifying the spherical cursor position.

>>> def callback(msg): environment['cursor'].position = (msg.x, msg.y, msg.z)
>>> sub = server_node.create_subscription(msg_type=position_message,
...                                       topic='cursor/position',
...                                       callback=callback,
...                                       qos_profile=qos.SYSTEM_DEFAULT.value)

Test the subscription.

>>> client['cursor'].position = (0.1, -0.5, 1.0)
>>> spin(client_node)
>>> spin(server_node)
>>> environment
{'cursor': {'radius': 0.1, 'position': {'x': 0.1, 'y': -0.5, 'z': 1.0}}}

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


# Collections / containers imports.

# ROS2 imports
import rclpy.node
from rclpy.qos import QoSPresetProfiles as qos

# spheres_environment imports
import spheres_environment

# Local imports.
from ros_spheres_environment.messages import *


# Sphere client class.
class Sphere(spheres_environment.Sphere):
    """ """

    def __init__(self, *args, node, **kwargs):
        # Invoke the superclass constructor.
        super().__init__(*args, **kwargs)

        # Store a local reference to the ROS2 node.
        self._node = node

        # Initialize publishers for all object properties.
        self._initialize_publishers()

    def __del__(self):
        """Destroy publishers for all object properties."""
        self._destroy_publishers()

    def _initialize_publishers(self):
        """Initialize ROS2 publishers for all object properties."""

        # Prepare shorthand.
        create_publisher = self._node.create_publisher

        # Initialize publisher map.
        self._publisher_map = dict()

        # Define a publisher record map.
        publisher_record_map = dict(
            position=dict(msg_type=position_message),
            radius=dict(msg_type=radius_message),
        )

        # Iterate through object properties.
        for key in self.object_properties:
            # Prepare keyword arguments.
            topic = f"{self.key}/{key}"
            defaults = dict(topic=topic, qos_profile=qos.SYSTEM_DEFAULT.value)
            kwargs = {**defaults, **publisher_record_map[key]}

            # Initialize a publisher.
            self._publisher_map[topic] = create_publisher(**kwargs)

    def _destroy_publishers(self):
        """Destroy ROS2 publishers for all object properties."""

        # Iterate through object properties.
        for key in self.object_properties:
            # Initialize shorthand.
            topic = f"{self.key}/{key}"
            publisher = self._publisher_map[topic]

            # Destroy the publisher.
            self._node.destroy_publisher(publisher)

    def __setitem__(self, key, value):
        """ """

        # Invoke the superclass method.
        # This is necessary only to store a local copy of the value.
        super().__setitem__(key, value)

        # Ensure that the key corresponds to a valid object property.
        if not self.is_object_property(key):
            raise KeyError

        # Generate a mapping between object property keys and message
        # generators.
        message_map = dict(
            radius=lambda v: radius_message(data=value),
            position=lambda v: position_message(**value),
        )

        # Publish the message.
        topic = f"{self.key}/{key}"
        message = message_map[key](value)
        publisher = self._publisher_map[topic]
        publisher.publish(message)


# Environment client class.
class Environment(spheres_environment.Environment):
    """ """

    object_type_map = dict(sphere=Sphere)

    def __init__(self, node=None):
        # Initialize an empty subscription map.
        self._publisher_map = {}

        # Initialize properties if values are provided.
        if node:
            # Set the node.
            self.node = node

    @property
    def node(self):
        """An inintialized ROS2 node that provides the interface with a ROS2
            graph.

        This property must be set before the server is used. In particular, it
        must be set prior to referencing the `environment` property.
        """

        # Ensure that the property has been set.
        if not hasattr(self, "_node"):
            raise

        # Return the ROS2 node.
        return self._node

    @node.setter
    def node(self, value):
        # Ensure appropriate type.
        assert isinstance(value, rclpy.node.Node)

        # If the node has already been set and initialized, then de-initialize.
        self._destroy_publishers()

        # Set the property.
        self._node = value

        # Initialize the ROS2 interface.
        self._initialize_publishers()

    def _initialize_publishers(self):
        """Create publishers that link the virtual environment -- and
        objects contained therein -- to a ROS2 graph.
        """

        # Initialize an `initialize` publisher.
        topic = "initialize"
        kwargs = dict(
            msg_type=spawn_message, topic=topic, qos_profile=qos.SYSTEM_DEFAULT.value
        )
        self._publisher_map[topic] = self.node.create_publisher(**kwargs)

        # Initialize an `destroy` publisher.
        topic = "destroy"
        kwargs = dict(
            msg_type=spawn_message, topic=topic, qos_profile=qos.SYSTEM_DEFAULT.value
        )
        self._publisher_map[topic] = self.node.create_publisher(**kwargs)

    def _destroy_publishers(self):
        """Destroy any subscriptions that have been initialized by the server."""

        # Destroy each of the elements of the local subscription mapping.
        for topic, subscription in self._publisher_map.items():
            assert self.node.destroy_publisher(subscription)
            del self._publisher_map[topic]

    def initialize_object(self, key, **kwargs):
        """ """

        # Publish the request that the remote environment initialize an object.
        publisher = self._publisher_map["initialize"]
        message = spawn_message(data=key)
        publisher.publish(message)

        # Invoke superclass method with an additional argument.
        # This argument is passed to the initialized object.
        return super().initialize_object(key=key, node=self._node, **kwargs)

    def destroy_object(self, key):
        """ """

        # Publish a request that the remote environment destroy an object.
        publisher = self._publisher_map["destroy"]
        message = spawn_message(data=key)
        publisher.publish(message)

        # Invoke superclass method if the item exists.
        # The check is necessary in case the local virtual environment does
        # not exactly match the remote environment.
        if key in self:
            super().destroy_object(key=key)

    def __del__(self):
        """Destructor."""
        # self._destroy_publishers()


# Main.
if __name__ == "__main__":
    import doctest

    doctest.testmod()
