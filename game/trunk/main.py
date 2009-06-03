from __future__ import division
import exceptions

# Import OGRE-specific (and other UI-Client) external packages and modules.
import ogre.renderer.OGRE as ogre

# Import other external packages and modules.
import sys

# Import internal packages and modules modules.
import application


def main(argv=None):
    # Get command line arguments or passed parameters.
    if argv is None:
        argv = sys.argv

    # Start the application.
    if len(argv) > 1 and argv[1] == "server":
        try:
            app = application.ServerApplication()
            app.go()
        except KeyboardInterrupt:
            app.stop()
        except Exception:
            raise
            try: app.stop()
            except: pass
    else:
        address = "localhost"
        port = 8981
        if len(argv) > 1:
            address = argv[1]
        if len(argv) > 2:
            port = int(argv[2])
        print address, port
        try:
            app = application.ClientApplication(address, port)
            app.go()
        except ogre.OgreException, e:
            print e

    # Exit
    return 1


if __name__ == '__main__':
    main()