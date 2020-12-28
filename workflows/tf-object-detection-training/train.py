import sys
import os
import subprocess
import shutil
import urllib.request
import tarfile
import argparse
import yaml
import json
import csv

import faulthandler
faulthandler.enable()

from google.protobuf import text_format
import tensorflow as tf
import numpy as np

def count_samples(dataset):
    cnt_graph = dataset.reduce(np.int64(0), lambda x, _: x + 1)
    with tf.compat.v1.Session() as sess:
        cnt = sess.run(cnt_graph)
    return cnt

def split_dataset(path, train_path, val_path, val_ratio=0.2, seed=99):
    print('\nSplitting up dataset')
    if (val_ratio > 1.0) or (val_ratio < 0.0):
        val_ratio = 0.2
    
    # Load Dataset
    full_dataset = tf.data.TFRecordDataset(path)

    # Count samples
    cnt = count_samples(full_dataset)
    print('full dataset size: {}'.format(cnt))

    # Split
    full_dataset = full_dataset.shuffle(cnt, seed=seed) # Shuffle dataset
    train_size = int(val_ratio * cnt)
    train_dataset = full_dataset.take(train_size)
    val_dataset = full_dataset.skip(train_size)

    # Save train and validation datasets
    train_writer = tf.data.experimental.TFRecordWriter(train_path)
    val_writer = tf.data.experimental.TFRecordWriter(val_path)
    with tf.compat.v1.Session() as sess:
        sess.run(train_writer.write(train_dataset))
        sess.run(val_writer.write(val_dataset))

    # Count new dataset samples
    train_cnt = count_samples(train_dataset)
    val_cnt = count_samples(val_dataset)
    print('train dataset size: {}'.format(train_cnt))
    print('validation dataset size: {}'.format(val_cnt))

def convert_labels_to_csv(path):
    with open(os.path.join(path, 'label_map.pbtxt'),'r') as f:
        txt = f.readlines()
    print('Generating label maps file...')
    csv_out = open(os.path.join('/mnt/output/', 'classes.csv'), 'w')
    csv_writer = csv.writer(csv_out)
    csv_writer.writerow(['labels'])
    data = {}
    for line in txt:
        if 'id' in line:
            i = str(line.split(':')[1].strip())
            data[i] = None
        if 'name'  in line:
            n = line.split(':')[1].strip().strip("'")
            csv_writer.writerow([n])
            data[i] = n
    d = {'label_map': data}
    with open(os.path.join('/mnt/output/', 'label_map.json'), 'w') as outfile:
        json.dump(d, outfile)
    print('Finished generating label maps file')

def create_pipeline(pipeline_path, model_path, label_path,
    train_tfrecord_path, eval_tfrecord_path, out_pipeline_path, model_architecture, params):
	# We need to import here since pb files are built right before this function is called
    from object_detection.protos import pipeline_pb2

    pipeline_config = pipeline_pb2.TrainEvalPipelineConfig()
    with tf.gfile.GFile(pipeline_path, 'r') as f:
        proto_str = f.read()
        text_format.Merge(proto_str, pipeline_config)
    if model_architecture == 'ssd':
        pipeline_config.model.ssd.num_classes=int(params['num_classes'])
        if 'image-height' in params:
            pipeline_config.model.ssd.image_resizer.fixed_shape_resizer.height = int(params['image-height'])
        if 'image-width' in params:
            pipeline_config.model.ssd.image_resizer.fixed_shape_resizer.width = int(params['image-width'])
    else:  #faster-rcnn based models
        pipeline_config.model.faster_rcnn.num_classes=int(params['num_classes'])
        if int(params['num-clones']) != 1:
            pipeline_config.train_config.batch_size = int(params['num-clones'])
        if 'min-dimension' in params:
            pipeline_config.model.faster_rcnn.image_resizer.keep_aspect_ratio_resizer.min_dimension = int(params['min-dimension'])
        if 'max-dimension' in params:
            pipeline_config.model.faster_rcnn.image_resizer.keep_aspect_ratio_resizer.max_dimension = int(params['max-dimension'])
        if 'initial-learning-rate' in params:
            pipeline_config.train_config.optimizer.momentum_optimizer.learning_rate.manual_step_learning_rate.initial_learning_rate = float(initial-learning-rate)
        if 'schedule-step-1' in params:
            pipeline_config.train_config.optimizer.momentum_optimizer.learning_rate.manual_step_learning_rate.schedule[0].step = int(params['schedule-step-1'])
        if 'schedule-step-2' in params:
            pipeline_config.train_config.optimizer.momentum_optimizer.learning_rate.manual_step_learning_rate.schedule[1].step = int(params['schedule-step-2'])

    pipeline_config.train_config.fine_tune_checkpoint=model_path
    pipeline_config.train_config.num_steps=int(params['epochs'])
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

    model_architecture = 'frcnn'
    if 'num-clones' not in params:
        params['num-clones'] = 1
    if 'train-val-ratio' not in params:
        params['train-val-ratio'] = 0.8
    if 'num-steps' not in params:
        params['num-steps'] = 10000
    if 'ssd-mobilenet-v2-coco' in params['model'] or 'ssd-mobilenet-v1-coco2' in params['model']:
        if 'num-steps' not in params:
            params['num-steps'] = 15000
        model_architecture = 'ssd'
    elif 'frcnn-res101-low' in params['model'] or 'frcnn-nas-coco' in params['model']:
        if 'num-steps' not in params:
            params['num-steps'] = 10
    elif 'ssdlite-mobilenet-coco' in params['model']:
        if 'num-steps' not in params:
            params['num-steps'] = 10
        model_architecture = 'ssd'
    params['epochs'] = params.pop('num-steps')

    split_dataset(
        params['dataset']+'/default.tfrecord', 
        params['dataset']+'/train.tfrecord', 
        params['dataset']+'/validation.tfrecord',
        params['train-val-ratio']
    )

    create_pipeline('/mnt/data/models/pipeline.config',
        '/mnt/data/models/model.ckpt',
        params['dataset']+'/label_map.pbtxt',
        params['dataset']+'/train.tfrecord',
        params['dataset']+'/validation.tfrecord',
        '/mnt/output/pipeline.config',
        model_architecture,
        params)

    os.chdir('/mnt/output')
    os.mkdir('eval/')
    subprocess.call(['python',
        '/mnt/src/tf/research/object_detection/legacy/train.py',
        '--train_dir=/mnt/output/',
        '--pipeline_config_path=/mnt/output/pipeline.config',
        '--num_clones={}'.format(params['num-clones'])
    ])
    subprocess.call(['python',
        '/mnt/src/tf/research/object_detection/export_inference_graph.py',
        '--input-type=image_tensor',
        '--pipeline_config_path=/mnt/output/pipeline.config',
        '--trained_checkpoint_prefix=/mnt/output/model.ckpt-{}'.format(params['epochs']),
        '--output_directory=/mnt/output'
    ])

    # generate lable map
    convert_labels_to_csv(params['dataset'])
    print('Training complete and output saved')

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
    params.update(vars(args))
    print('Processed parameters: ', params)
    main(params)

