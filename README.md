Tides of the Elements is a real-time networked 3D fighting game created with Python and the [OGRE 3D rendering engine](http://www.ogre3d.org/).

It was designed and written by
[Jeff Gaskill](https://github.com/mistergaskill),
[Preston Lewis](https://github.com/hosemagi), and
[Parsha Pourkhomami](https://github.com/parshap)
in Spring 2009 for CS 113, *Computer Game Development*, taught by
[Dan Frost](http://frost.ics.uci.edu) at the *University of California,
Irvine*. Contributions were made by several others, notably art by Aaron Moore and David Woo of the *Laguna College of Art and Design* and sound by Andria Coyne.

A design document for the game can be found at:
https://sites.google.com/site/iso25tides.

[A video of gameplay](media/tote.wmv) and [several
screenshots](media/screenshots) are included in this repository.

The original README included with the game [is also
included](game/trunk/readme.txt).

Interesting parts of the source include:

 * [Collision detection and resolution](game/trunk/gamestate/collision.py) for rectangles, circles, line segments, and cones in a 2d world (Preston Lewis)
 * [Netcode and binary protocol](game/trunk/net) (Parsha Pourkhomami)
 * [Client and server-side game loops](game/trunk/application.py)
 * Model-View decoupling between [game state](game/trunk/gamestate) and the [rendered visuals](game/trunk/nodes.py) that represent them using events for message passing

This repository is here for historical reasons. This code is not
intended to be used.
