# py-vitals

Python tools for rdlevels, adds a few helpful functions for downloading and parsing levels.

# Installation

Just run `pip install pyvitals`!

# Examples

```python
import pyvitals

# Get the list of levels from the rdlevels API
data = pyvitals.get_site_data()
print(data)

# Only get verified levels
data = pyvitals.get_site_data(verified_only=True)
print(data)

# Download the first level in the list to the current directory, unzipping it in the process
path = pyvitals.download_level(data[0]['download_url'], './', unzip = True)

# Parse the rdlevel from the recently download level
level_data = pyvitals.parse_level(f'{path}/main.rdlevel')
print(level_data)
```
