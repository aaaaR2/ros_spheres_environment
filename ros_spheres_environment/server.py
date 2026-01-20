""" Interface for exposing a `spheres_environment` to a ROS2 graph, such that 
    the properties of objects in the environment can be manipulated by remote 
    nodes.

Examples
--------

Initialize a ROS2 interface.

Create spheres environment.

Create a ROS2 node.

Connect the environment to ROS2.

Create a ROS2 client node.

Initialize a publisher for the object initialization topic.

Publish an object initialization message.

Allow the server node to process messages and confirm that the environment has 
been updated.

>>> import rclpy
>>> rclpy.init()

>>> import spheres_environment
>>> environment = spheres_environment.Environment()

>>> import rclpy.node
>>> node = rclpy.node.Node('server')


>>> #from geometry_msgs.msg import Point as position_message
>>> #from example_interfaces.msg import Float64 as radius_message
>>> topic_parameter_map \\
...   = {'cursor/position': dict(msg_type=position_message),
...      'cursor/radius': dict(msg_type=radius_message)}

>>> server = Server(node=node, 
...                 environment=environment)#, 
... #                topic_parameter_map=topic_parameter_map)

>>> client = rclpy.node.Node('client')

>>> publisher_map = {}
>>> topic = 'initialize'
>>> publisher_map[topic] \\
...   = client.create_publisher(topic=topic, 
...                             msg_type=spawn_message,
...                             qos_profile=qos.SYSTEM_DEFAULT.value)

>>> publisher_map['initialize'].publish(spawn_message(data='cursor'))
>>> spin = lambda n: rclpy.spin_once(n, timeout_sec=0.010)
>>> spin(client)

>>> spin(node)
>>> environment
{'cursor': {}}
>>> environment['cursor'].object_properties
['position', 'radius']

>>> publisher_map = {}
>>> topic = 'cursor/position'
>>> publisher_map[topic] \\
...   = client.create_publisher(topic=topic, 
...                             msg_type=position_message,
...                             qos_profile=qos.SYSTEM_DEFAULT.value)

>>> message = position_message(x=1.0, y=2.0, z=3.0)
>>> publisher_map[topic].publish(message)
>>> spin(client)

>>> spin(node)
>>> environment
{'cursor': {'position': {'x': 1.0, 'y': 2.0, 'z': 3.0}}}


Clean up the ROS2 node and shut down the ROS2 interface.

>>> node.destroy_node()
>>> rclpy.shutdown()

"""

# Copyright 2022 Carnegie Mellon University Neuromechatronics Lab (a.whit)
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Contact: a.whit (nml@whit.contact)

# ROS2 imports
import rclpy.node
from rclpy.qos import QoSPresetProfiles as qos
from rosidl_runtime_py import message_to_ordereddict

# spheres_environment imports
import spheres_environment

# Local imports.
from ros_spheres_environment.messages import *


# Server class.
class Server:
    """Bridge class that links the properties and methods of a virtual
        environment to ROS2 topics, such that the state of the environment can
        be remotely modified via ROS2 messages.

    The `Server` class creates subscriptions that are attached to the object
    initialization and destruction methods of the virtual environment, as well
    as to the properties of each individual object in the environment.

    Arguments
    ---------
    node : rclpy.node.Node
        A ROS2 node that provides an interface with a ROS2 graph. This node
        will be used to initialize publishers and subscribers that enable
        remote interaction with the environment object.
    environment : spheres_environment.base.Environment
        A class with data structures and methods that define an environment in
        which objects interact.

    """

    DEFAULT_TOPIC_PARAMETER_RECORD = dict(
        msg_type=default_message, qos_profile=qos.SYSTEM_DEFAULT.value
    )
    """ Default values to be passed to `rclpy.node.Node.create_publisher` or 
        `rclpy.node.Node.create_subscription` as keyword arguments.
    """

    DEFAULT_TOPIC_PARAMETER_MAP = dict(
        initialize=dict(msg_type=spawn_message), destroy=dict(msg_type=spawn_message)
    )
    """ Mapping from a ROS2 topic string to a set of keyword arguments to be 
        passed, by default, to `rclpy.node.Node.create_publisher` or 
        `rclpy.node.Node.create_subscription` when initializing publishers or 
        subscriptions for the topic.
    """

    DEFAULT_PROPERTY_MESSAGE_MAP = dict(
        position=position_message, radius=radius_message
    )
    """ Mapping from a spheres environment object property key to a ROS2 
        message type. Used for preparing arguments to 
        `rclpy.node.Node.create_publisher` or 
        `rclpy.node.Node.create_subscription` when initializing publishers or 
        subscriptions for the topic.
    """

    def __init__(self, node=None, environment=None, topic_parameter_map={}):
        # Initialize an empty subscription map.
        self._subscription_map = {}

        # Iniitalize the topic parameter map.
        self._topic_parameter_map = {
            **self.DEFAULT_TOPIC_PARAMETER_MAP,
            **topic_parameter_map,
        }

        # Initialize properties if values are provided.
        if node:
            # Set the node.
            self.node = node

            # Set the environment.
            if isinstance(environment, spheres_environment.base.Environment):
                self.environment = environment

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
        self._destroy_subscriptions()

        # Set the property.
        self._node = value

    @property
    def environment(self):
        """Interface with a virtual environment."""

        # Ensure that the node property has been set.
        if not hasattr(self, "_node"):
            raise

        # Ensure that the environment property has been set.
        if not hasattr(self, "_environment"):
            raise

        # Return the environment.
        return self._environment

    @environment.setter
    def environment(self, value):
        # Ensure appropriate type.
        assert isinstance(value, spheres_environment.base.Environment)

        # Set the property.
        self._environment = value

        # If the node has already been set and initialized, then de-initialize.
        self._destroy_subscriptions()

        # Initialize the ROS2 interface.
        self._initialize_subscriptions()

    def _initialize_subscriptions(self):
        """Create subscriptions that link the virtual environment -- and
        objects contained therein -- to a ROS2 graph.
        """

        ## Initialize callback shorthand.
        # def make_callback(method):
        #    def callback(message):
        #        method(key=message.data)
        #        self._environment.update()
        #    return callback

        # Prepare keyword arguments for an object creation topic subscription.
        topic = "initialize"
        kwargs = {
            **self.DEFAULT_TOPIC_PARAMETER_RECORD,
            "topic": topic,
            "callback": lambda m: self.initialize_object(
                key=m.data
            ),  # make_callback(self.initialize_object),
            **self._topic_parameter_map.get(topic, {}),
        }

        # Initialize topic shorthand.
        topic = kwargs["topic"]

        # Initialize the subscription.
        self._subscription_map[topic] = self.node.create_subscription(**kwargs)

        # Prepare keyword arguments for an object destruction topic subscription.
        topic = "destroy"
        kwargs = {
            **self.DEFAULT_TOPIC_PARAMETER_RECORD,
            "topic": topic,
            "callback": lambda m: self.destroy_object(
                key=m.data
            ),  # make_callback(self.destroy_object),
            **self._topic_parameter_map.get(topic, {}),
        }

        # Initialize topic shorthand.
        topic = kwargs["topic"]

        # Initialize the subscription.
        self._subscription_map[topic] = self.node.create_subscription(**kwargs)

    def _destroy_subscriptions(self):
        """Destroy any subscriptions that have been initialized by the server."""

        # Destroy each of the elements of the local subscription mapping.
        for topic, subscription in self._subscription_map.items():
            assert self.node.destroy_subscription(subscription)
            del self._subscription_map[topic]

    def initialize_object(self, key, type_key=None, **kwargs):
        """Initialize a new object in the environment.

        Although objects can be initialized directly using the mapping
        or `__setitem__` accessor, it is better to initialize objects
        functionally. This ensures that object classes are of a
        recognized type, and performs any needed housekeeping.

        Arguments
        ---------
        key : str
            Unique key used to identify an object in the environment.
        type_key : str
            Unique key that references an item in the `object_type_map`
            class variable. Defines the type of the initialized object.
            Defaults to the first key in the mapping, if not specified.

        Returns
        -------
        object
            The initialized object instance.
        """

        # Initialize the object in the environment.
        obj = self._environment.initialize_object(key=key, type_key=type_key)

        # Define a function for generating a ROS2 callback that passes
        # message data to a property of the corresponding object in the
        # virtual environment.
        # This default callback should not be used for scalar property types.
        # UPDATE:
        to_dict = lambda m: message_to_ordereddict(m)
        to_value = lambda d: d["data"] if (list(d) == ["data"]) else d

        # def to_dict(msg):
        #    d = message_to_ordereddict(m)
        #    d = {key: d['data']}
        #        if (list(d) == ['data'])
        #        else {f'{key}/{k}': v for (k, v) in d.items()}
        #    return d
        # make_callback \
        #  = lambda k: lambda m: setattr(obj, k, to_value(to_dict(m)))
        #  #= lambda k: lambda m: setattr(obj, k, to_dict(m))
        #  #= lambda k: lambda m: obj.set(**to_dict(m))
        def make_callback(key):
            def callback(message):
                value = message_to_ordereddict(message)
                value = value["data"] if (list(value) == ["data"]) else value
                setattr(obj, key, value)
                self._environment.update()  # !

            return callback

        # Iterate through the object properties.
        for property_key in obj.object_properties:
            # Retrieve the default message type for the object property.
            msg_type = self.DEFAULT_PROPERTY_MESSAGE_MAP[property_key]

            # Prepare keyword arguments.
            topic = f"{key}/{property_key}"
            kwargs = {
                **self.DEFAULT_TOPIC_PARAMETER_RECORD,
                "msg_type": msg_type,
                "topic": topic,
                "callback": make_callback(property_key),
                **self._topic_parameter_map.get(topic, {}),
            }

            # Initialize topic shorthand.
            topic = kwargs["topic"]

            # Initialize a subscription.
            self._subscription_map[topic] = self.node.create_subscription(**kwargs)

        # Update the environment.
        self._environment.update()

        # Return the initialized object.
        return obj

    def destroy_object(self, key):
        """Remove an object from the environment."""

        # Initialize shorthand.
        obj = self._environment[key]

        # Iterate through the object properties.
        for property_key in obj.object_properties:
            # Prepare keyword arguments.
            topic = f"{key}/{property_key}"

            # Retrieve the subscription.
            subscription = self._subscription_map[topic]  # pop

            # Destroy the subscription.
            assert self.node.destroy_subscription(subscription)

            # Remove the subscription pair from the mapping.
            del self._subscription_map[topic]

        # Delete the object from the environment.
        del self._environment[key]

        # Update the environment.
        self._environment.update()

    def __del__(self):
        """Destructor."""
        # self._destroy_subscriptions()


# Main.
if __name__ == "__main__":
    import doctest

    doctest.testmod()
