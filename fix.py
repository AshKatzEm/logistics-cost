import pandas as pd

# This will print the line number of the bad line
try:
    pd.read_csv('shipping_macro_data.csv')
except Exception as e:
    print(e)

# Once you know it's line 1063, you can open the file in a text editor
# and delete the extra comma or the entire line.