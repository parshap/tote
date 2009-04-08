"""
This is a prototype for different movement input modes.
"""
# Use 3.0 style division (/ vs //)
from __future__ import division

# Python modules
import sys
import math

# Other modules
import pyglet
import rabbyt

#######################
##   CONFIGURATION   ##
#######################

KEYBOARD_CONTROLS = {
	# Absolute movement in a cardinal direction, regardless of the player's
	# current facing direction.
	"UP": None,
	"DOWN": None,
	"LEFT": None,
	"RIGHT": None,
	
	# Relative movement based on the player's current facing direction.
	"FORWARD": pyglet.window.key.W,
	"BACKWARD": pyglet.window.key.S,
	"STRAFE_LEFT": pyglet.window.key.A,
	"STRAFE_RIGHT": pyglet.window.key.D,

	# Change in the direction the player is facing.
	"TURN_LEFT": None,
	"TURN_RIGHT": None,
}

MOUSE_CONTROLS = {
	# The player will face towards the mouse cursor position when this button
	# is pressed.
	"FACE": pyglet.window.mouse.RIGHT,
	
	# The player will move forward (relative to the facing direction) when this
	# button is pressed.
	"MOUSEMOVE": pyglet.window.mouse.RIGHT | pyglet.window.mouse.LEFT
	
	# NOTE: You can require multiple mouse buttons to be pressed at the same
	#       time using a bitwise OR operator.
}

# If this is true the player will always be facing the mouse cursor position
# regardless of what buttons are being pressed.
PLAYER_ALWAYS_FACE_MOUSE = False

# The player's movement speed.
PLAYER_MOVE_SPEED = 300 # 300 pixels per second

# The player's rotation speed when changing facing direction using TURN_LEFT
# and TURN_RIGHT.
PLAYER_TURN_SPEED = 180 # 180 degrees per second

# This is the size of the map.
MAP_WIDTH = 25 # tiles wide
MAP_HEIGHT = 25 # tiles high
MAP_TILE_SIZE = 40 # pixel square tiles

#######################
## END CONFIGURATION ##
#######################


class PrototypeClient:
	"""
	This class represents the UI component.
	"""
	def __init__(self):
		pass
	
	def run(self):
		# Set up the display and attempt 4x AA.
		display = pyglet.window.get_platform().get_default_display() 
		screen = display.get_default_screen()
		glconfig = pyglet.gl.Config(double_buffer=True,
		                            sample_buffers=True,
		                            samples=8,
		                            )
		try:
			config = screen.get_best_config(glconfig)
		except window.NoSuchConfigException:
			# Failed AA config - use a config without AA.
			config = screen.get_best_config(pyglet.gl.Config(double_buffer=True))
		self.window = pyglet.window.Window(config=config, resizable=True, vsync=True)

		# Load terrain tiles.
		terrain_grid_image = pyglet.image.ImageGrid(pyglet.image.load("data/tiles.png"),
		                                             1, 1, MAP_TILE_SIZE+1, MAP_TILE_SIZE+1, 1, 1)
		terrain_grid = pyglet.image.TextureGrid(terrain_grid_image)
		terrain_dirt = rabbyt.Sprite(texture=terrain_grid[0], u=1, v=1)
		self.terrain = [[terrain_dirt] * MAP_WIDTH] * MAP_HEIGHT
		
		# Load the player and put it in the middle of the map.
		self.player = Player()
		self.player.x = MAP_WIDTH * MAP_TILE_SIZE / 2
		self.player.y = MAP_HEIGHT * MAP_TILE_SIZE / 2
		
		# Load the FPS display.
		self.fps_display = pyglet.clock.ClockDisplay(color=(1, 1, 1, 0.5))

		# Init rabbyt
		rabbyt.set_default_attribs()
		
		# Set up the clock and keep track of the time.
		self.clock = pyglet.clock.get_default()
		# self.clock.set_fps_limit(30)
		def track_time(dt):
			self.dt = dt
			self.time += dt
		self.clock.schedule(track_time)
		
		self.time = 0
		self.dt = 0
		
		# Get a keyboard handler to store the state of all keys.
		self.keyboard = pyglet.window.key.KeyStateHandler()
		
		# Keep track of mouse button states.
		self.mouse = 0
		
		# Keep track of mouse x, y coordinates.
		self.mousex = self.mousey = None

		# Push applicable event handlers to the window.
		self.window.push_handlers(self.on_draw,
		                          self.keyboard,
		                          self.on_mouse_press,
		                          self.on_mouse_release,
		                          self.on_mouse_motion,
		                          self.on_mouse_drag)

		# Go!
		pyglet.app.run()
		
	def on_draw(self):
		"""
		Draw method to be called on every frame.
		"""
		rabbyt.set_time(self.time)
		
		# Handle player movement due to keyboard/mouse input.
		if self.keyboard[KEYBOARD_CONTROLS["UP"]]:
			self.player.mup(PLAYER_MOVE_SPEED * self.dt)

		if self.keyboard[KEYBOARD_CONTROLS["DOWN"]]:
			self.player.mdown(PLAYER_MOVE_SPEED* self.dt)
			
		if self.keyboard[KEYBOARD_CONTROLS["RIGHT"]]:
			self.player.mright(PLAYER_MOVE_SPEED * self.dt)
			
		if self.keyboard[KEYBOARD_CONTROLS["LEFT"]]:
			self.player.mleft(PLAYER_MOVE_SPEED * self.dt)
			
		if self.keyboard[KEYBOARD_CONTROLS["FORWARD"]] or \
		   self.mouse & MOUSE_CONTROLS["MOUSEMOVE"] == MOUSE_CONTROLS["MOUSEMOVE"]:
			self.player.forward(PLAYER_MOVE_SPEED * self.dt)
			
		if self.keyboard[KEYBOARD_CONTROLS["BACKWARD"]]:
			self.player.backward(PLAYER_MOVE_SPEED * self.dt)
			
		if self.keyboard[KEYBOARD_CONTROLS["STRAFE_RIGHT"]]:
			self.player.strafe_right(PLAYER_MOVE_SPEED * self.dt)
			
		if self.keyboard[KEYBOARD_CONTROLS["STRAFE_LEFT"]]:
			self.player.strafe_left(PLAYER_MOVE_SPEED * self.dt)
		
		if self.keyboard[KEYBOARD_CONTROLS["TURN_RIGHT"]]:
			self.player.turn_right(PLAYER_TURN_SPEED * self.dt)
			
		if self.keyboard[KEYBOARD_CONTROLS["TURN_LEFT"]]:
			self.player.turn_left(PLAYER_TURN_SPEED * self.dt)
		
		# Turn the player to face the mouse if we need to.
		if (self.mouse & MOUSE_CONTROLS["FACE"] or PLAYER_ALWAYS_FACE_MOUSE) and \
		   self.mousex is not None and self.mousey is not None:
			# Calculate the x, y coordinates of the click based on the given
			# screen coordinates.
			self.player.face(self.mousex + self.player.x - self.window.get_size()[0]/2,
			                 self.mousey + self.player.y - self.window.get_size()[1]/2)
			
		# Update the player's x, y coordinates.
		self.player.updatepos()
		
		# Keep the player inside the map.
		self.player.clamp(0, MAP_HEIGHT*MAP_TILE_SIZE, MAP_WIDTH*MAP_TILE_SIZE, 0)
		
		# Reset the screen to a blank state.
		rabbyt.clear((0, 0, 0, 1))
		
		# Center the viewable area around the player.
		self.view(self.player.x - self.window.get_size()[0]/2,
		          self.player.y - self.window.get_size()[1]/2)
		
		# Do the drawing.
		
		# Determine which tile the player is on.
		tilex = int(self.player.x / MAP_TILE_SIZE)
		tiley = int(self.player.y / MAP_TILE_SIZE)
		
		# Determine how many tiles need to be drawn on the screen on each side
		# of the player (the center).
		tilecountx = int(self.window.get_size()[0] / (MAP_TILE_SIZE*2)) + 2
		tilecounty = int(self.window.get_size()[1] / (MAP_TILE_SIZE*2)) + 2
		
		startx = max(0, tilex - tilecountx)
		endx = min(MAP_WIDTH, tilex + tilecountx)
		starty = max(0, tiley - tilecounty)
		endy = min(MAP_HEIGHT, tiley + tilecounty)
		
		# Draw the background terrain.
		terrain = self.terrain
		for x in range(startx, endx):
			for y in range(starty, endy):
				terrain[x][y].left = x * MAP_TILE_SIZE
				terrain[x][y].bottom = y * MAP_TILE_SIZE
				terrain[x][y].render()
		
		# Draw the player.
		self.player.render()
		
		# Set the render mode to HUD mode.
		self.hud();
		
		# Draw the FPS. This is a Pyglet sprite and not a Rabbyt sprite, so we
		# use .draw() instead of .render().
		self.fps_display.draw()
	
	def view(self, x, y):
		""" Set the render mode to draw the viewable area at position x, y. """
		# Set modelview matrix to move, scale & rotate to camera position"
		pyglet.gl.glMatrixMode(pyglet.gl.GL_MODELVIEW)
		pyglet.gl.glLoadIdentity()
		pyglet.gl.gluLookAt(
		    x, y, +1.0,
		    x, y, -1.0,
		    0, 1, 0.0)
	
	def hud(self):
		""" Set the render mode to draw HUD elements. """
		pyglet.gl.glMatrixMode(pyglet.gl.GL_MODELVIEW)
		pyglet.gl.glLoadIdentity()
	
	def on_mouse_press(self, x, y, button, modifiers):
		self.mouse |= button
		if button & MOUSE_CONTROLS["FACE"]:
			# Save the mouse coordinates so we can face it.
			self.mousex = x
			self.mousey = y
		
	def on_mouse_release(self, x, y, button, modifiers):
		self.mouse &= ~button
	
	def on_mouse_motion(self, x, y, dx, dy):
		if PLAYER_ALWAYS_FACE_MOUSE:
			# If the player is always facing the mouse, save the new
			# coordinates so we can face the them.
			self.mousex = x
			self.mousey = y

	def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
		if buttons & MOUSE_CONTROLS["FACE"] or PLAYER_ALWAYS_FACE_MOUSE:
			# Save the mouse coordinates so we can face it.
			self.mousex = x
			self.mousey = y


class Player(rabbyt.Sprite):
	"""
	This class represents the player's UI element (sprite).
	"""
	def __init__(self):
		texture = pyglet.image.load("data/amg1.png").get_texture()
		rabbyt.Sprite.__init__(self, texture=texture,
                               shape=[-16, 16, 16, -16],
		                       tex_shape=[0, 1, 0.125, 0])
		self.dx = self.dy = self.drx = self.dry = 0
		
	def updatepos(self):
		"""
		Update the player's screen x, y coordinates based on movement made.
		"""
		# Calculate the change in position from relative movements (e.g., from
		# Player.forward() or Player.strafe_right()).
		drmag = math.sqrt(self.drx*self.drx + self.dry*self.dry)
		if drmag != 0:
			bound = max(math.fabs(self.drx), math.fabs(self.dry))
			p = bound/drmag
			dcomprx = self.drx * p
			dcompry = self.dry * p
			self.x += math.cos(math.radians(self.rot + 90)) * dcompry
			self.y += math.sin(math.radians(self.rot + 90)) * dcompry
			self.x += math.sin(math.radians(self.rot + 90)) * dcomprx
			self.y -= math.cos(math.radians(self.rot + 90)) * dcomprx
			self.drx = self.dry = 0
			
		# Calculate the change in position from absolute movements (e.g., from
		# Player.up() or Player.right()).
		dmag = math.sqrt(self.dx*self.dx + self.dy*self.dy)
		if dmag != 0:
			bound = max(math.fabs(self.dx), math.fabs(self.dy))
			p = bound/dmag
			dcompx = self.dx * p
			dcompy = self.dy * p
			self.x += dcompx
			self.y += dcompy
			
		# Reset the d- attributes.
		self.dx = self.dy = self.drx = self.dry = 0

	def clamp(self, left, top, right, bottom):
		"""
		Clamp the player inside the given rectangle.
		"""
		# @todo Accept different inputs (tuples? shape? rect? list?).
		# @todo Don't assume top left and bottom right coordinates.
		if self.left < left:
			self.left = left
		if self.right > right:
			self.right = right
		if self.bottom < bottom:
			self.bottom = bottom
		if self.top > top:
			self.top = top
				
	def face(self, x, y):
		"""
		Update the direction the player is facing to be towards the
		given screen x, y coordinates.
		"""
		rx, ry = x - self.x, y - self.y
		if rx == 0:
			if ry >= 0: self.rot = 0
			else: self.rot = 180
		else:
			if rx >= 0: self.rot = math.degrees(math.atan(ry/rx)) - 90
			else: self.rot = math.degrees(math.atan(ry/rx)) + 90
			
	def forward(self, d):
		"""
		Moves the player forward in the current facing direction by d units.
		"""
		self.dry += d
		# self.x += math.cos(math.radians(self.rot + 90)) * d
		# self.y += math.sin(math.radians(self.rot + 90)) * d

	def backward(self, d):
		"""
		Moves the player backward in the current facing direction by d units.
		"""
		self.forward(-d)
		
	def strafe_right(self, d):
		"""
		Strafes the player right relative to the current facing direction by
		d units.
		"""
		self.drx += d
		# self.x += math.sin(math.radians(self.rot + 90)) * d
		# self.y -= math.cos(math.radians(self.rot + 90)) * d
		
	def strafe_left(self, d):
		"""
		Strafes the player right relative to the current facing direction by
		d units.
		"""
		self.strafe_right(-d)
		
	def mup(self, d):
		self.dy += d
		
	def mdown(self, d):
		self.dy -= d
		
	def mleft(self, d):
		self.dx -= d
		
	def mright(self, d):
		self.dx += d
		
	def turn_right(self, d):
		self.rot -= d
		
	def turn_left(self, d):
		self.rot += d

def main(argv=None):
	# Get explicitely passed arguments or command line arguments.
	if argv is None:
		argv = sys.argv
	
	# Start the client and run it.
	client = PrototypeClient()
	client.run()
	
	# Exit
	return 1

if __name__ == "__main__":
	sys.exit(main())