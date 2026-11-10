"""Shared layout constants for the Bear RPG world (all coordinates are world block coordinates)."""

# overworld build region (multiples of 16)
OX0, OZ0, OX1, OZ1 = -448, -448, 448, 448
OY0, OY1 = -64, 192
SEA = 62
G = 68                      # ground surface y in the town / plots

TOWN_R = 78                 # half size of the town wall square
PLOT_SIZE = 41              # interior size of one personal plot
PLOT_ROAD = 7
PLOT_X0, PLOT_Z0 = -316, -76   # north-west corner of the plot district (outer road edge)
PLOT_COLS, PLOT_ROWS = 4, 3

KEEP = (0, -252)            # plains dungeon (ruined keep) centre
KEEP_G = 71
MOUNTAIN = (275, -275)
MINE = (196, -186)          # cave dungeon entrance terrace
MINE_G = 74
PYRAMID = (292, 72)         # desert dungeon centre
PYR_G = 67
HARBOR = (0, 152)           # pier start on the south coast
TEMPLE = (0, 312)           # sunken temple centre
HELLGATE = (-252, 252)      # volcano crater with the nether gate
HELL_G = 72

# nether build region
NX0, NZ0, NX1, NZ1 = -256, -256, 256, 128
NY0, NY1 = 0, 128
NHUB = (0, 40, 0)           # nether hub arrival point (x, y, z)

# biome ids
BIO_OCEAN, BIO_PLAINS, BIO_DESERT, BIO_HILLS, BIO_FOREST = 0, 1, 2, 3, 4
BIO_RIVER, BIO_HELL, BIO_BEACH, BIO_DEEP = 7, 8, 16, 24
BIO_SOUL, BIO_CRIMSON, BIO_WARPED, BIO_BASALT = 178, 179, 180, 181
BIO_LUSH, BIO_DRIP, BIO_STONY, BIO_DARK = 187, 188, 189, 190
BIO_WARM = 40
