## Bulk extraction of .json maintenance files from logs


### Input files
This seems to work well-ish with Sydney and Dubai, I have not tried it elsewhere.
First step requires to obtain a CSV-like list of maintenance activities, and format
it to get consistency across all lines (asset names, timestamp format, etc.).

Another csv file is used to define the `short_name` of the assets (as appearing
in the client's maintenance logs) their `long_name` (in our SQL databases), and
their GPS coordinates `WGS84 lat`and `WGS4 long`.

At last, a json file is used to include information of the client's logs formatting
and local timezone. It is critical (and a pain, yes) to set it up to get a correct
mapping of the information.

Modifying the paths mentioned in the "INPUT FILES" section of the `csv2json4logs.py`
script will presumably enable it to run for other projects, provided a consistent
mapping can be achieved.

### Disclaimers
I will not be competent in maintaining or cleaning up the `csv2json4logs.py` script
much further, I have mainly been treating this as a *Python for Dummies* exercise.
I have however commented as much as I could what I understood of my own code, so
feel free to use or improve on it if this is of any help to you!

The empty `json_files` folder in the repository is the default output for the generated
files. 

Sample generated files are provided in the `output_examples` folder, from
running the script on the included data from Sydney and Dubai projects. These are **ONLY**
here for illustration purposes, I have not looked for the latest logs available for
either project, hence the output could be inaccurate and/or outdated. **DO NOT** use
these files on a production environment.

