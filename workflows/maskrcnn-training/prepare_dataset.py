# Prepares Dataset for the corresponding job with Trained Model and Classes File

import json
import csv
import os
import glob

# create csv file for inference
def generate_csv(input_file):
	with open(input_file) as f:
		data = json.load(f)

	csv_out = open(os.path.join("/mnt/output/", "classes.csv"), "w", newline='')

	csv_writer = csv.writer(csv_out)
	csv_writer.writerow(['labels','id'])

	for lbl in data['categories']:
		csv_writer.writerow([lbl['name'], lbl['id']])


if __name__ == '__main__':
	import sys
	from pprint import pprint

	generate_csv(sys.argv[1])

	from datetime import datetime
	time = datetime.now()
	stamp = time.strftime("%m%d%Y%H%M%S")
	dataset_name = "maskrcnn-model-output-{}".format(stamp)

	for i,_,_ in os.walk("/mnt/output/logs"):
		if "cvat" in i:
			model_path = i
	if not model_path.endswith("/"):
		model_path += "/"
	# find last saved model
	latest_model = max(glob.glob(model_path+"mask*"), key=os.path.getctime)
	print("Uploading to AWS S3")
