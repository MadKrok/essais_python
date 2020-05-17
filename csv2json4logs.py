import json
import csv
from datetime import datetime, timedelta
import pytz
from pytz import timezone


#INPUT FILES
#############################

#generic info on the assets monitored; csv file with headers : Switch; Switch_long_name; WGS84 long; WGS84 lat
coord_file = 'sydney_coord.csv'
#csv file extracted from centralised logs with maintenance activities (VITAL for Dubai, Excel file for Sydney)
maintenance_csv_list = 'sydney_list.csv'
#.json file with formatting information on the csv logs (to map them to our standardised maintenance json), and local timezone information, to ensure conversion to UTC. Main file to customise to make the converter compatible with other projects:
json_maptz = 'sydney_json_map+tz.json'
#is the "T" separating date and time in the standard UTC format appearing in our databases? It seems it does not.
output_time_format = '%Y-%m-%dT%H:%M:%SZ'  #full UTC : '%Y-%m-%dT%H:%M:%SZ'

#############################


#AUXILIARY FUNCTIONS
#############################

#check Python guidelines on initialising variables, etc. (note for myself)
monitoredAssets = []

with open(coord_file) as file:
	coord_reader = csv.DictReader(file, delimiter= ";")
	for row in coord_reader:
		monitoredAssets.append(row['Switch'])

#returns SQL variable name for the monitored assets
def long_name(switch):
	if switch in monitoredAssets:
		with open(coord_file) as file:
			coord_reader = csv.DictReader(file, delimiter= ";")
			for row in coord_reader:
				if row['Switch'] == switch:
					return row['Switch_long_name']
					break
	else:
		return switch


#axis: 'long' or 'lat'
def gps(switch, axis):
	if switch in monitoredAssets:
		with open(coord_file) as file:
			coord_reader = csv.DictReader(file, delimiter= ";")
			for row in coord_reader:
				if row['Switch'] == switch:
					coordWithUnit = row['WGS84 {}'.format(axis)]
					return coordWithUnit.replace('°','')
					break
	else:
		return "N/A"


with open(json_maptz, "r") as read_file:
	params = json.load(read_file)


def loc_to_UTC(dt_string):
	utc = pytz.utc
	local_tz = timezone(params['local_tz'])
	dt_object = datetime.strptime(dt_string, params['maintenance_log_datetime_format'])
	sydney_dt = local_tz.localize(dt_object)   #localises the datetime object (includes Z and offset to UTC info)
	utc_dt = sydney_dt.astimezone(utc)       #converts the datetime object to a localised UTC one
	return utc_dt

#############################


#CSV TO JSON FORMATTING (and individual json files exportation, one per logged maintenance)
#############################

jsonList = []

with open(maintenance_csv_list) as csvfile:
	reader = csv.DictReader(csvfile)
	for row in reader:
		local_timestamp = ""
		for i in range(params["col_number_for_timestamp"]):
			local_timestamp = local_timestamp + row[params["local_timestamp_col{}".format(i+1)]] + params["local_timestamp_col_separator{}".format(i+1)]
		UTC_dt = loc_to_UTC(local_timestamp)
		UTC_timestamp = UTC_dt.strftime(output_time_format)
#if timestamp for end of intervention exists, use it, otherwise, shift the initial timestap by half-an-hour
		if params ["maintenance_end_timestamp_provided"] == "yes":
			local_timestamp_end= ""
			for i in range(params["col_number_for_timestamp"]):
                        	local_timestamp_end = local_timestamp_end + row[params["local_timestamp_end_col{}".format(i+1)]] + params["local_timestamp_col_separator{}".format(i+1)]
			UTC_dt_end = loc_to_UTC(local_timestamp_end)
			UTC_timestamp_end = UTC_dt_end.strftime(output_time_format)
		else:
			UTC_timestamp_end = (UTC_dt + timedelta(minutes=+30)).strftime(output_time_format)

		maintenance_action = ""
		for j in range(params["col_number_for_maintenance_action"]):
			maintenance_action = maintenance_action + params["description_col{}".format(j+1)] + row[params["action_col{}".format(j+1)]]
		short_name = row[params["id_asset_col"]]

		if not params["type_col"]:
			type = params["type"]
		else:
			type = row[params['type_col']]

		if not params["maintenance_type_col"]:
			maintenance_type = params['maintenance_type']
		else:
			maintenance_type = row[params["maintenance_type_col"]]

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
#		with open("json_files/SRS_{}_{}.json".format(title), "w") as output_json:
#			json.dump(i, output_json)

k=0
for i in jsonList:
	k += 1
	with open("json_files/{}_{}.json".format(i["id_asset"],i["timestamp"]), "w") as output_json:
		json.dump(i, output_json)
