# sphere_tiler
playing with tiles mapped onto a sphere

Quick help:
you'll need to install python, with modules pygame and numpy.

`$ python make_tile.py`

creates a file tile.png, containing a hexagonal tile.  The tile must be transparent (alpha=0) outside the hexagon.

`$ python hextiles.py`

reads tile.png, tiles it across the plane in the usual hexagonal tiling with random rotations and reflections (with a suitable background colour) and creates output.png
In addition, it takes the tiled image and wraps it around a hemisphere (using stereographic projection) and adds a little bit of shading, then writes sphere.png

hextiles has optional arguments

`$ python hextiles.py <tile_file> <tile_scale>`

`<tile_file>` defaults to `tile.png`

`<tile_scale>` defaults to `1.0`, and changes the relative size of the tile before placing it in the plane.

That's all!

Please do mention aardvarkkrill if you do anything good with this code.  And tell me about it!
