import os
import sys
import shutil
import urllib.request
import tarfile
import yaml
import argparse

from google.protobuf import text_format

def create_pipeline(pipeline_path, model_path, label_path,
    train_tfrecord_path, eval_tfrecord_path, out_pipeline_path,
    epochs, num_classes, num_clones, format, params):
	# We need to import here since pb files are built right before this call
	from object_detection.protos import pipeline_pb2

	pipeline_config = pipeline_pb2.TrainEvalPipelineConfig()
    with tf.gfile.GFile(pipeline_path, 'r') as f:
        proto_str = f.read()
        text_format.Merge(proto_str, pipeline_config)
    if format == 'ssd':
        pipeline_config.model.ssd.num_classes=int(num_classes)
        if 'image-height' in params:
            pipeline_config.model.ssd.image_resizer.fixed_shape_resizer.height = int(params['image-height'])
        if 'image-width' in params:
            pipeline_config.model.ssd.image_resizer.fixed_shape_resizer.width = int(params['image-width'])
    else:  #faster-rcnn based models
        pipeline_config.model.faster_rcnn.num_classes=int(num_classes)
        if int(num_clones) != 1:
            pipeline_config.train_config.batch_size = int(num_clones)
        if 'min-dimension' in params:
            pipeline_config.model.faster_rcnn.image_resizer.keep_aspect_ratio_resizer.min_dimension = int(params['min-dimension'])
        if 'max-dimension' in params:
            pipeline_config.model.faster_rcnn.image_resizer.keep_aspect_ratio_resizer.max_dimension = int(params['max-dimension'])
        if 'schedule-step-1' in params:
            pipeline_config.train_config.optimizer.momentum_optimizer.learning_rate.manual_step_learning_rate.schedule[0].step = int(params['schedule-step-1'])
        if 'schedule-step-2' in params:
            pipeline_config.train_config.optimizer.momentum_optimizer.learning_rate.manual_step_learning_rate.schedule[1].step = int(params['schedule-step-2'])

    pipeline_config.train_config.fine_tune_checkpoint=model_path
    pipeline_config.train_config.num_steps=int(epochs)
    pipeline_config.train_input_reader.label_map_path=label_path
    pipeline_config.train_input_reader.tf_record_input_reader.input_path[0]=train_tfrecord_path

    pipeline_config.eval_input_reader[0].label_map_path=label_path
    pipeline_config.eval_input_reader[0].tf_record_input_reader.input_path[0]=eval_tfrecord_path

    config_text = text_format.MessageToString(pipeline_config)
    with tf.gfile.Open(out_pipeline_path, 'wb') as f:
        f.write(config_text)

def main(params):
	if not os.path.isdir('/mnt/data/models'):
		try:
			os.remove('/mnt/data/models')
		except:
			pass
		print('Creating models dir')
		os.makedirs('/mnt/data/models/')

	#check if base model exists, if not then download
	if params['sys_finetune_checkpoint'] == '':
		print('base model does not exist, downloading...')
		urllib.request.urlretrieve('https://github.com/onepanelio/templates/releases/download/v0.2.0/{}.tar'.format(params['model']), '/mnt/data/models/model.tar')
		model_files = tarfile.open('/mnt/data/models/model.tar')
		model_files.extractall('/mnt/data/models')
		model_files.close()
		model_dir = '/mnt/data/models/'+params['model']
		files = os.listdir(model_dir)
		for f in files:
			shutil.move(model_dir+'/'+f,'/mnt/data/models')


	os.system('pip install test-generator')
	os.system('mkdir -p /mnt/src/protoc')
	os.system('wget -P /mnt/src/protoc https://github.com/protocolbuffers/protobuf/releases/download/v3.10.1/protoc-3.10.1-linux-x86_64.zip')
	os.chdir('/mnt/src/protoc/')
	os.system('unzip protoc-3.10.1-linux-x86_64.zip')
	os.chdir('/mnt/src/tf/research/')
	os.system('/mnt/src/protoc/bin/protoc object_detection/protos/*.proto --python_out=.')

	model = 'frcnn'
	if 'epochs' not in params:
		params['epochs'] = 10000
	if 'ssd-mobilenet-v2-coco' in params['model'] or 'ssd-mobilenet-v1-coco2' in params['model']:
		if 'epochs' not in params:
			params['epochs'] = 15000
		model = 'ssd'
	elif 'frcnn-res101-low' in params['model'] or 'frcnn-nas-coco' in params['model']:
		if 'epochs' not in params:
			params['epochs'] = 10
	elif 'ssdlite-mobilenet-coco' in params['model']:
		if 'epochs' not in params:
			params['epochs'] = 10
		model = 'ssd'

	create_pipeline('/mnt/data/models/pipeline.config',
		'/mnt/data/models/model.ckpt',
		params['dataset']+'/label_map.pbtxt',
		params['dataset']+'/*.tfrecord',
		params['dataset']+'/default.tfrecord',
		'/mnt/output/pipeline.config',
		params['epochs'],
		params['num_classes'],
		params['num-clones'],
		model,
		params)

	os.chdir('/mnt/output')
	os.mkdir('eval/')

	os.system('python /mnt/src/tf/research/object_detection/legacy/train.py --train_dir=/mnt/output/ --pipeline_config_path=/mnt/output/pipeline.config --num_clones={}'.format(params['num-clones']))
	os.system('python /mnt/src/tf/research/object_detection/export_inference_graph.py --input-type=image_tensor --pipeline_config_path=/mnt/output/pipeline.config --trained_checkpoint_prefix=/mnt/output/model.ckpt-{} --output_directory=/mnt/output'.format(params['epochs']))

	#generate lable map
	os.system('python /mnt/src/train/convert_json_workflow.py {}/'.format(params['dataset']))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Train TFOD.')
	parser.add_argument('--dataset', default='/mnt/data/datasets')
	parser.add_argument('--extras', help='hyperparameters or other configs')
	parser.add_argument('--sys_finetune_checkpoint', default=' ', help='path to checkpoint')
	parser.add_argument('--model', default='frcnn-res50-coco', help='which model to train')
	parser.add_argument('--num_classes', default=81, type=int, help='number of classes')
	args = parser.parse_args()
	# parse parameters
	# sample: epochs=100;num_classes=1
	print('Arguments: ', args)
	extras = args.extras.split('\n')
	extras_processed = [i.split('#')[0].replace(' ','') for i in extras if i]
	params = {i.split('=')[0]:i.split('=')[1] for i in extras_processed}
	if 'num-clones' not in params:
		params['num-clones'] = 1
	params.update(vars(args))
	params['epochs'] = params.pop('num-steps') 
	print('Processed parameters: ', params)
	main(params)

