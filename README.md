# py-vitals

Python tools for rdlevels, adds a few helpful functions for downloading and parsing levels.

# Installation

Just run `pip install pyvitals`!
The pypi version of this module is still a bit old, you might want to do
`pip install git+https://github.com/huantianad/pyvitals` instead, to download from the github repo..

# Examples

```python
import os

import pyvitals

# Get the list of levels from the rdlevels API
data = pyvitals.get_sheet_data()

# Only get verified levels
data = pyvitals.get_sheet_data(verified_only=True)

# Download the first level in the list to the current directory, unzipping it in the process
path = pyvitals.download_level(data[0]['download_url'], './', unzip=True)

# Parse the rdlevel from the recently download level
level_data = pyvitals.parse_level(os.path.join(path, 'main.rdlevel'))

# Parse a rdzip's main.rdlevel directly
level_data = pyvitals.parse_rdzip(data[0]['download_url'])
```

## Documentation
There's no documentation yet :(, but I'll probably get to it eventually.
For now, you can check out the docstrings.
