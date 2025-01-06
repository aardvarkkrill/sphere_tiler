# sphere_tiler

playing with tiles mapped onto a sphere

Quick help:
you'll need to install python, with modules pygame and numpy. I used python 3.12 and pygame 2.5.2.

`$ python brain_tile.py`
or `$ python rainbow_tile.py`

creates a file {brain,rainbow}_tile.png, containing a regular hexagonal tile. The tile must be transparent (alpha=0)
outside the
hexagon. The hexagon has horizontal sides aligned with the top and bottom of the image.

`$ python hextiles.py <tile_file> <tile_scale>`

reads the tile file (default `tile.png`) scales it (default 1.0) and tiles it across the plane in the usual hexagonal
tiling with random rotations
and reflections (with a background colour added) and creates `output.png`

`<tile_file>` defaults to `tile.png`

`<tile_scale>` defaults to `1.0`, and changes the relative size of the tile before placing it in the plane.

`$ python project_to_sphere.py <plane_image> <sphere_radius> <shadow>`

Loads the plane image and wraps it around a sphere of given radius in pixels, with some
shadowing. The arguments are optional and default to `output.png`, `1200` and `0.3`.
Setting shadowing to 0 turns it off. Larger numbers are darker.

The file `nested_spheres.py` has functions to generate some pretty objects. These are obtained
by nesting several partially transparent spheres to get a sense of depth. You'll need to uncomment
the ones you want to try (at the bottom of the file) before running it.

That's all!

Please do mention aardvarkkrill if you do anything good with this code. And tell me about it!
