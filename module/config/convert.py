import re

def convert_daily(value):
    value = re.sub('Calyx_Crimson_Hunt', 'Calyx_Crimson_The_Hunt', value)
    return value