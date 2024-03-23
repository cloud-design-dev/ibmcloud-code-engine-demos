import os
from icecream import ic

# Define the prefix
prefix = "CE_"

# Filter environment variables that start with the prefix
ce_variables = {key: value for key, value in os.environ.items() if key.startswith(prefix)}

# Print the filtered environment variables
for key, value in ce_variables.items():
    ic(f"{key}: {value}")