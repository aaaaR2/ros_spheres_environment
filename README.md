---
title: README
author: a.whit ([email](mailto:nml@whit.contact))
date: December 2022
---

<!-- License

Copyright 2022 Neuromechatronics Lab, Carnegie Mellon University (a.whit)

Created by: a. whit. (nml@whit.contact)

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
-->

# ros_spheres_environment

A ROS2 package for manipulating a virtual environment in which spherical
objects interact in a 3D space. This package is intended to be general and
pluggable, to be used with _any_ objects that implement the interfaces defined
in the [spheres_environment] package. By wrapping such objects, this package
makes their properties remotely accessible, via the [ROS2 graph].

## Installation

This package requires the [spheres_environment] Python package. This
requirement must be installed prior to using this package.

This package can be added to any [ROS2 workspace]. ROS2 workspaces are built
using [colcon]. See the
[installation documentation](doc/markdown/installation.md) for further
information.

### Testing

See the [testing documentation](doc/markdown/testing.md) for further
information.

## Getting started

Perhaps the best way to get started is via a simple example. The code that
follows must be run from within a [configured ROS2 environment].

First, create a spheres environment. This object organizes data structures and
methods relevant to modeling a environment in which spherical objects interact
in a 3D virtual space. This Python object is the interface to the virtual
environment.

```python
>>> import spheres_environment
>>> environment = spheres_environment.Environment()

```

Import the ROS2 Python library and initialize a ROS2 interface.

```python
>>> import rclpy
>>> rclpy.init()

```

Define shorthand for updating (i.e., spinning) nodes in the ROS2 environment.
This function briefly passes control to the [ROS2 executor] in order to allow
it to process ROS2 messages.
It will be necessary to spin nodes a number of times throughout this example,
and this shorthand improves clarity.

```python
>>> spin = lambda n: rclpy.spin_once(n, timeout_sec=0.010)

```

Create a pair of ROS2 nodes. One node will serve as a "client", and the other
will function as a "server". The server wraps the virtual environment, and
connects it to the ROS2 graph.

```python
>>> import rclpy.node
>>> server_node = rclpy.node.Node('server')
>>> client_node = rclpy.node.Node('client')

```

Wrap the "server" node with the `Server` interface provided by this package.
This interface / wrapper acts as "glue" that links the virtual environment to
the ROS2 graph. Once this interface is initialized, messages that arrive on
the appropriate ROS2 topics (e.g., `objects/sphere/radius`) will be routed to
corresponding properties (e.g., `radius`) of objects in the virtual environment
(examples to follow).

```python
>>> from ros_spheres_environment import Server
>>> server = Server(node=server_node, environment=environment)

```

Wrap the "client" node with the 'Client' interface provided by this package.
This interface effectively creates a remote mirror of the virtual environment,
by implementing the interfaces defined in the [spheres_environment] package.
The client can then be treated exactly as though it were the remote virtual
environment, without any reference or knowledge of the ROS2 transmissions
occuring "under the hood".

```python
>>> from ros_spheres_environment import Client
>>> client = Client(node=client_node)

```

Before testing the client/server model, confirm that the environment is empty,
in the baseline state.

```python
>>> environment
{}

```

Using the `initialize_object` method defined by the [spheres_environment]
interface, use the client to create an object -- in this case, a sphere with
the label `cursor` -- in the remote virtual environment. Briefly surrender
control to ROS2 in order to allow the client node to send the appropriate
message, and then again to allow the server node to receive and process it.

```python
>>> client.initialize_object('cursor')
{}
>>> spin(client_node)
>>> spin(server_node)

```

Confirm that the request from the client was received by the server, and that a
new object was initialized in the remote environment. Note that the same
outcome could have been accomplished by directly invoking the
`initialize_object` method of the `environment` object. However, this example
is meant to illustrate the capability of this package to facilitate interaction
with a virtual environment in the case in which direct access to the
environment is not feasible or desirable.

```python
>>> environment
{'cursor': {}}

```

At baseline, the new object assumes default parameter values. This behavior is
dictated by the [spheres_environment] package. At present, there is no
mechanism for remotely querying parameter values.

```python
>>> cursor = environment['cursor']
>>> cursor.radius
1.0
>>> cursor.position
{'x': 0.0, 'y': 0.0, 'z': 0.0}

```

The properties of the new sphere object can be remotely modified by setting the
corresponding properties of the client. Update the radius of the sphere, and
confirm the changes.

```python
>>> client['cursor'].radius = 0.10
>>> spin(client_node)
>>> spin(server_node)

```

Similarly modify the position of the sphere.

```
>>> client['cursor'].position = (0.1, -0.5, 1.0)
>>> spin(client_node)
>>> spin(server_node)

```

Confirm that the changes have been effected in the virtual environment.

```
>>> environment
{'cursor': {'radius': 0.1, 'position': {'x': 0.1, 'y': -0.5, 'z': 1.0}}}

```

This concludes the example.
Clean up the ROS2 nodes and shut down the ROS2 interface.

```python
>>> client_node.destroy_node()
>>> server_node.destroy_node()
>>> rclpy.shutdown()

```

### Example doctests

The examples in this README are rendered in [doctest] format, and can be run
via the following code:[^python_paths]

[^python_paths]:
    Provided that the package is installed, or the [Python path]
    is otherwise set appropriately.

```
import doctest
doctest.testfile('README.md', module_relative=False)

```

These tests can also be run from the command line:

```bash
python -m doctest path/to/ros_spheres_environment/README.md

```

## Design

A diagram and description of the system architecture is provided in the
[extended documentation](doc/markdown/architecture.md).

## License

Copyright 2022 [Neuromechatronics Lab][neuromechatronics],
Carnegie Mellon University

Created by: a. whit. (nml@whit.contact)

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

<!---------------------------------------------------------------------
   References
---------------------------------------------------------------------->

[Python path]: https://docs.python.org/3/tutorial/modules.html#the-module-search-path
[doctest]: https://docs.python.org/3/library/doctest.html
[setuptools]: https://setuptools.pypa.io/en/latest/userguide/quickstart.html#basic-use
[neuromechatronics]: https://www.meche.engineering.cmu.edu/faculty/neuromechatronics-lab.html
[pip install]: https://pip.pypa.io/en/stable/cli/pip_install/
[spheres_environment]: https://github.com/ricmua/spheres_environment
[ROS2 graph]: https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Nodes/Understanding-ROS2-Nodes.html#background
[ROS2 executor]: https://docs.ros.org/en/humble/Concepts/About-Executors.html
