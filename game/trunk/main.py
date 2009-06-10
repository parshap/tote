from __future__ import division
import exceptions

# Import OGRE-specific (and other UI-Client) external packages and modules.
import ogre.renderer.OGRE as ogre

# Import other external packages and modules.
import sys
import random

# Import internal packages and modules modules.
import application


def main(argv=None):
    random.seed()
    # Get command line arguments or passed parameters.
    if argv is None:
        argv = sys.argv

    # Start the application.
    if len(argv) > 1 and argv[1] == "server":
        # Run as a server.
        try:
            app = application.ServerApplication()
            app.go()
        except KeyboardInterrupt:
            try: app.stop()
            except: pass
        except Exception:
            raise
            try: app.stop()
            except: pass
    
    else:
        # Run as a client.
        # Set up the default parameters.
        player_name = "Newbie"
        address = "localhost"
        port = 8981
        if len(argv) > 1:
            player_name = argv[1]
        if len(argv) > 2:
            address = argv[2]
        if len(argv) > 3:
            port = int(argv[3])
        print "Starting and connecting to %s:%s as %s." % (address, port, player_name)
        try:
            app = application.ClientApplication(player_name, address, port)
            app.go()
        except ogre.OgreException, e:
            print e

    # Exit
    return 1


if __name__ == '__main__':
    main()