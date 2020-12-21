import os
import sys
import shutil
import urllib.request
import tarfile
import yaml
import argparse

def start_training(params):
	if not os.path.isdir("/mnt/data/models"):
		try:
			os.remove("/mnt/data/models")
		except:
			pass
		print("Creating models dir")
		os.makedirs("/mnt/data/models/")

	#check if base model exists, if not then download
	if params['sys_finetune_checkpoint'] == "":
		print("base model does not exist, downloading...")
		urllib.request.urlretrieve("https://github.com/onepanelio/templates/releases/download/v0.2.0/{}.tar".format(params['model']), "/mnt/data/models/model.tar")
		model_files = tarfile.open("/mnt/data/models/model.tar")
		model_files.extractall("/mnt/data/models")
		model_files.close()
		model_dir = "/mnt/data/models/"+params['model']
		files = os.listdir(model_dir)
		for f in files:
			shutil.move(model_dir+"/"+f,"/mnt/data/models")


	os.system("pip install test-generator")
	os.system("mkdir -p /mnt/src/protoc")
	os.system("wget -P /mnt/src/protoc https://github.com/protocolbuffers/protobuf/releases/download/v3.10.1/protoc-3.10.1-linux-x86_64.zip")
	os.chdir("/mnt/src/protoc/")
	os.system("unzip protoc-3.10.1-linux-x86_64.zip")
	os.chdir("/mnt/src/tf/research/")
	os.system("/mnt/src/protoc/bin/protoc object_detection/protos/*.proto --python_out=.")
	from create_pipeline_v2 import create_pipeline

	if "ssd-mobilenet-v2-coco" in params['model']:
		if 'epochs' not in params:
			params['epochs'] = 15000
		create_pipeline("/mnt/data/models/pipeline.config","/mnt/data/models/model.ckpt", params['dataset']+'/label_map.pbtxt', params['dataset']+'/*.tfrecord', params['dataset']+'/default.tfrecord', "/mnt/output/pipeline.config", params['epochs'],params['num_classes'], params['num-clones'],"ssd", params)


	elif "ssd-mobilenet-v1-coco2" in params['model']:
		if 'epochs' not in params:
			params['epochs'] = 15000
		create_pipeline("/mnt/data/models/pipeline.config","/mnt/data/models/model.ckpt", params['dataset']+'/label_map.pbtxt', params['dataset']+'/*.tfrecord', params['dataset']+'/default.tfrecord', "/mnt/output/pipeline.config", params['epochs'],params['num_classes'], params['num-clones'],"ssd", params)


	elif "frcnn-res101-coco" in params['model']:
		if 'epochs' not in params:
			params['epochs'] = 10000
		create_pipeline("/mnt/data/models/pipeline.config","/mnt/data/models/model.ckpt", params['dataset']+'/label_map.pbtxt', params['dataset']+'/*.tfrecord', params['dataset']+'/default.tfrecord', "/mnt/output/pipeline.config", params['epochs'],params['num_classes'], params['num-clones'],"frcnn", params)


	elif "frcnn-res50-low" in params['model']:
		if 'epochs' not in params:
			params['epochs'] = 10000
		create_pipeline("/mnt/data/models/pipeline.config","/mnt/data/models/model.ckpt", params['dataset']+'/label_map.pbtxt', params['dataset']+'/*.tfrecord', params['dataset']+'/default.tfrecord', "/mnt/output/pipeline.config", params['epochs'],params['num_classes'], params['num-clones'],"frcnn", params)
	elif "frcnn-res50-coco" in params['model'] or "faster-rcnn-res50" in params['model']:
		if 'epochs' not in params:
			params['epochs'] = 10000
		create_pipeline("/mnt/data/models/pipeline.config","/mnt/data/models/model.ckpt", params['dataset']+'/label_map.pbtxt', params['dataset']+'/*.tfrecord', params['dataset']+'/default.tfrecord', "/mnt/output/pipeline.config", params['epochs'],params['num_classes'], params['num-clones'],"frcnn", params)

	elif "frcnn-res101-low" in params['model']:
		if 'epochs' not in params:
			params['epochs'] = 10
		create_pipeline("/mnt/data/models/pipeline.config","/mnt/data/models/model.ckpt", params['dataset']+'/label_map.pbtxt', params['dataset']+'/*.tfrecord', params['dataset']+'/default.tfrecord', "/mnt/output/pipeline.config", params['epochs'],params['num_classes'], params['num-clones'],"frcnn", params)


	elif "frcnn-nas-coco" in params['model']:
		if 'epochs' not in params:
			params['epochs'] = 10
		create_pipeline("/mnt/data/models/pipeline.config","/mnt/data/models/model.ckpt", params['dataset']+'/label_map.pbtxt', params['dataset']+'/*.tfrecord', params['dataset']+'/default.tfrecord', "/mnt/output/pipeline.config", params['epochs'],params['num_classes'], params['num-clones'],"frcnn", params)

	elif "ssdlite-mobilenet-coco" in params['model']:
		if 'epochs' not in params:
			params['epochs'] = 10
		create_pipeline("/mnt/data/models/pipeline.config","/mnt/data/models/model.ckpt", params['dataset']+'/label_map.pbtxt', params['dataset']+'/*.tfrecord', params['dataset']+'/default.tfrecord', "/mnt/output/pipeline.config", params['epochs'],params['num_classes'], params['num-clones'],"ssd", params)

	os.chdir("/mnt/output")
	os.mkdir("eval/")



	os.system("python /mnt/src/tf/research/object_detection/legacy/train.py --train_dir=/mnt/output/ --pipeline_config_path=/mnt/output/pipeline.config --num_clones={}".format(params['num-clones']))
	os.system("python /mnt/src/tf/research/object_detection/export_inference_graph.py --input-type=image_tensor --pipeline_config_path=/mnt/output/pipeline.config --trained_checkpoint_prefix=/mnt/output/model.ckpt-{} --output_directory=/mnt/output".format(params["epochs"]))


	#generate lable map
	os.system("python /mnt/src/train/convert_json_workflow.py {}/".format(params['dataset']))

	#evaluate model in the end
	# this is commented because the v1.13.0 of TF OD API is older uses unicode instead of str and updating it might break other parts.
	# either fork that repo and update the file or update tf model and fix other parts that it might break
	#os.system("python /mnt/src/tf/research/object_detection/legacy/eval.py --checkpoint_dir=/mnt/output/ --pipeline_config_path=/mnt/output/pipeline.config --eval_dir=/mnt/output/eval/")

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Train TFOD.')
	parser.add_argument('--dataset', default="/mnt/data/datasets")
	parser.add_argument('--extras', help="hyperparameters or other configs")
	parser.add_argument('--sys_finetune_checkpoint', default=" ", help="path to checkpoint")
	parser.add_argument('--model', default="frcnn-res50-coco", help="which model to train")
	parser.add_argument('--num_classes', default=81, type=int, help="number of classes")
	args = parser.parse_args()
	# parse parameters
	# sample: epochs=100;num_classes=1
	print("Arguments: ", args)
	extras = args.extras.split("\n")
	extras_processed = [i.split("#")[0].replace(" ","") for i in extras if i]
	params = {i.split('=')[0]:i.split('=')[1] for i in extras_processed}
	if 'num-clones' not in params:
		params['num-clones'] = 1
	params.update(vars(args))
	params['epochs'] = params.pop('num-steps') 
	print("Processed parameters: ", params)
	start_training(params)

