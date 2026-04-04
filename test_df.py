import pandas as pd
from name_map import *

def test_mappings():
    print(normalize_mr("MME CLEMENCE"))
    print(normalize_product("KLINDEX-M"))
    print(normalize_activity("PETITE DEJOUNER"))
    print(normalize_territory("YOPOUGON OUEST"))
    print(normalize_distributor("TEDIS"))

test_mappings()
