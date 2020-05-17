import json
import csv
from datetime import datetime, timedelta
import pytz
from pytz import timezone


#INPUT FILES
#############################

#generic info on the assets monitored,
#csv file with headers : Switch, Switch_long_name, WGS84 long, WGS84 lat
coord_file = 'dubai_coord.csv'

#csv file extracted from centralised logs with maintenance activities
#(VITAL for Dubai, Excel file for Sydney)
maintenance_csv_list = 'dubai_list.csv'

#.json file with formatting information on the csv logs (to map them to our
#standardised maintenance json), and local timezone information, to ensure
#conversion to UTC. Main file to customise to make the converter compatible
#with other projects.
json_maptz = 'dubai_json_map+tz.json'


##############################


#OUTPUT OPTIONS
##############################
#is the "T" separating date and time in the standard UTC format appearing
#in our databases? It seems it does not. The "T" can be replaced by " " for
#the timestamps in the output .json  to match the existing style.
output_time_format = '%Y-%m-%dT%H:%M:%SZ'  #full UTC : '%Y-%m-%dT%H:%M:%SZ'


#Improvement idea: enabling to choose a custom folder path for the generated
#files.  May require fiddling with os.mkdir() and os.path.exists().
#output_folder_path = '/json_files"

#############################


#AUXILIARY FUNCTIONS
#############################

monitoredAssets = []

with open(coord_file) as file:
	coord_reader = csv.DictReader(file, delimiter= ",")
	for row in coord_reader:
		monitoredAssets.append(row['Switch'])


#Returns SQL variable name for the monitored assets. For assets not monitored but
#mentioned in the maintenance logs, simply returns the passed argument.
#In the loops defined further down, this will display the "short_name".
#
#Such a filtering could be applied during the parsing of the maintenance logs
#(see #CSV TO JSON FORMATTING AND EXPORT section below), not to generate
#json files for assets not followed by PHM (if directly removing lines in the
#"maintenance_csv_list" input file is cumbersome).


def long_name(switch):
	if switch in monitoredAssets:
		with open(coord_file) as file:
			coord_reader = csv.DictReader(file, delimiter= ",")
			for row in coord_reader:
				if row['Switch'] == switch:
					return row['Switch_long_name']
					break
	else:
		return switch


#retuns a single GPS (WGS84 reference) coordinate (axis: 'long' or 'lat',
#respectively for longitude or latitude) in decimal degrees (DD), for the asset selected.
#Implies the coordinates in the "coord_file" columns are already in WGS84, DD format.
#
#Conversions from degree minutes second (DMS) could be included, maybe from other
#coordinates systems too? Probably unnecessarily complicated...

def gps(switch, axis):
	if switch in monitoredAssets:
		with open(coord_file) as file:
			coord_reader = csv.DictReader(file, delimiter= ",")
			for row in coord_reader:
				if row['Switch'] == switch:
					coordWithUnit = row['WGS84 {}'.format(axis)]
					return coordWithUnit.replace('°','')
					break
	else:
		return "N/A"


#Loads generic information on the maintenance logs formatting and timezone

with open(json_maptz, "r") as read_file:
	params = json.load(read_file)


#takes a timestamp string, turns it into a localised datetime Python object
#(timezone and formatting information of maintenance logs described in the
#"json_maptz"), then converts the datetime to the UTC time zone and returns it.
#
#Timezone is defined as per the Olson/IANA database (https://www.iana.org/time-zones).
#The use of the pytz library (https://pypi.org/project/pytz/) ensures conversions
#across time zones is consistent, even for past dates, and when daylight time savings
#(DST) are involved.
#
#IMPORTANT: Please note the time zone used by the local maintenance team for their
#reports and logs may be different than the one used by the data acquisition unit/datalogger
#to record the timestamp of each switch maneuver (UTC generally used in this case).

def loc_to_UTC(dt_string):
	utc = pytz.utc
	local_tz = timezone(params['local_tz'])
	#this datetime object is "naive", ie. has no timezone defined:
	dt_object = datetime.strptime(dt_string, params['maintenance_log_datetime_format'])
	#this localises the datetime object:
	localised_dt = local_tz.localize(dt_object)
	#converts the datetime object to a localised UTC one:
	utc_dt = localised_dt.astimezone(utc)
	return utc_dt

#############################



#CSV TO JSON FORMATTING AND EXPORT
#############################

#builds a list of "json-like" data, one per line included in the maintenance logs
#("maintenance_csv_list", which may require some formatting for consistency before
#being used here), and assigns the data according to the fields mapping in the
#"params" object (from the "json_maptz" input file).
#
#While most of the necessary information can be mapped directly, the timestamps
#and maintenance activities descriptions can annoyingly be spread over several
#columns of the maintenance logs... 3 sub-"for" loops are run in each iteration of
#the main "for" loop, to build the strings incrementally (pay attention to the
#"col_num_for_***" field in the "json_maptz" file).
#
#In case the maintenance logs only mention the date and not the time of intervention
#(as for Dubai), the "maintenance_log_datetime_format" field in the json_maptz" file
#should only refer to the day, month and year information. Upon the creation of a
#datetime Python object (third step of the "loc_to_UTC() function above, the time
#information will default to 00:00 (locally). This could be adjusted to match the
#middle of a typical maintenance shift...
#
#At last, when the starting time of an intervention is mentioned, the end time is
#not necessarily given (see the "maintenance_end_timestamp_provided" field in the
#"json_maptz" file). There is an "if" check below, to assign a default half-hour
#duration when the information is not available from the logs.

jsonList = []

with open(maintenance_csv_list) as csvfile:
	reader = csv.DictReader(csvfile)
	for row in reader:

		#builds the timestamp information, accross several columns of
		#the logs if necessary.
		local_timestamp = ""
		for i in range(params["col_number_for_timestamp"]):
			local_timestamp = local_timestamp + row[params["local_timestamp_col{}".format(i+1)]] + params["local_timestamp_col_separator{}".format(i+1)]
		UTC_dt = loc_to_UTC(local_timestamp)
		UTC_timestamp = UTC_dt.strftime(output_time_format)

		#if timestamp for end of intervention exists, uses it, otherwise,
		#shifts the initial timestap by half-an-hour. It is assumed the
		#same format is used for logged start and end timestamps when both
		#are available, hence only one set of "separators" field needs
		#defining when several columns are used in the logs.

		if params ["maintenance_end_timestamp_provided"] == "yes":
			local_timestamp_end= ""
			for i in range(params["col_number_for_timestamp"]):
                        	local_timestamp_end = local_timestamp_end + row[params["local_timestamp_end_col{}".format(i+1)]] + params["local_timestamp_col_separator{}".format(i+1)]
			UTC_dt_end = loc_to_UTC(local_timestamp_end)
			UTC_timestamp_end = UTC_dt_end.strftime(output_time_format)
		else:
			UTC_timestamp_end = (UTC_dt + timedelta(minutes=+30)).strftime(output_time_format)

		#Same principle as for the timestamps. The "description_col" fields
		#can be left at "" if the contents of the "action_col" fields are
		#sufficiently clear, but they are helpful for general legibility.
		maintenance_action = ""
		for j in range(params["col_number_for_maintenance_action"]):
			maintenance_action = maintenance_action + params["description_col{}".format(j+1)] + row[params["action_col{}".format(j+1)]]
		short_name = row[params["id_asset_col"]]

		#these 2 conditional checks will provide default values for the "type"
		#and "maintenance_type" fields of the json files, if no specific column
		#in the logs give details.
		if not params["type_col"]:
			type = params["type"]
		else:
			type = row[params['type_col']]

		if not params["maintenance_type_col"]:
			maintenance_type = params['maintenance_type']
		else:
			maintenance_type = row[params["maintenance_type_col"]]

		#the GPS info may be superfluous... It was an interesting exercise anyway!
		#I have not found an elegant way to directly attach pictures when they are
		#provided in bulk in the logs file (as per Sydney with the base Excel file)
		pre_json = {
			'logger': row[params['logger_col']],
			'id_asset': long_name(short_name),
			'timestamp': UTC_timestamp,
			'timestamp_end': UTC_timestamp_end,
			'type': type,
			'maintenance_type': maintenance_type,
			'maintenance_action': maintenance_action,
			'reset_baseline': 0,
			'reset_agan': 0,
			'gps_latitude': gps(short_name, 'lat'),
			'gps_longitude': gps(short_name, 'long'),
#			'mediaFolder': "",
#			'attachedPicture': "",
#			'descriptionPicture': "",
#			'attachedAudio': "",
#			'descriptionAudio': "",
#			'attachedVideo': "",
#			'descriptionVideo': "",
#			'attachedData': ""
			}
		jsonList.append(pre_json)


#Not sure if the writing of individual json files is better left on its own,
#or directly included in the loop above (no more need for the "jsonList" object
#in this case.
#
#It is assumed a "json_files" folder already exists at the same level as the
#script file when it is run, so it may need to be created manually otherwise.
#Alternatively, the path below may be modified to accomodate the preferred
#file structure. See second comment in the "OUTPUT OPTIONS" section at the top
#of this file.
k=0
for i in jsonList:
	k += 1
	with open("json_files/{}_{}.json".format(i["id_asset"],i["timestamp"]), "w") as output_json:
		json.dump(i, output_json)
