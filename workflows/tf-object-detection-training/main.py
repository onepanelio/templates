import os
import glob
import yaml
import shutil
import tarfile
import argparse
import subprocess
import urllib.request

from yaml.loader import FullLoader

from utils import convert_labels_to_csv, create_pipeline

def is_checkpoint_directory(dir):
    matched_files = get_checkpoint_files(dir)
    return True if len(matched_files)>0 else False

def get_last_checkpoint_filename(dir):
    matched_files = get_checkpoint_files(dir)
    matched_files.sort()
    match_file = matched_files[-1].split('/')[-1]
    return '.'.join(match_file.split('.')[0:2])

def get_checkpoint_files(dir):
    search_expression = os.path.join(dir, 'model.ckpt*')
    return [f for f in glob.glob(search_expression) if os.path.isfile(f)]


def main(params):

    data_dir = params['dataset']
    model_dir = params['model_path']
    checkpoint_dir = os.path.join(params['output_path'], 'checkpoints')
    trained_model_dir = os.path.join(params['output_path'], 'model')

    directories = [data_dir, model_dir, checkpoint_dir, trained_model_dir]

    if os.path.exists(trained_model_dir) and os.path.isdir(trained_model_dir):
        shutil.rmtree(trained_model_dir)

    for directory in directories:
        if len(directory) > 3 and not os.path.isdir(directory):
            try:
                os.remove(directory)
            except:
                pass
            os.makedirs(directory)

	#check if base model exists, if not then download
    if params['sys_finetune_checkpoint'] == '':
        files_dir = os.path.join(model_dir , params['model'])
        if not os.path.isdir(files_dir):
            print('base model does not exist, downloading...')
            urllib.request.urlretrieve('https://github.com/onepanelio/templates/releases/download/v0.2.0/{}.tar'.format(params['model']), os.path.join(model_dir , 'model.tar'))
            model_files = tarfile.open(os.path.join(model_dir , 'model.tar'))
            model_files.extractall(model_dir)
            model_files.close()
        files = os.listdir(files_dir)
        for f in files:
            shutil.move(os.path.join(files_dir , f),model_dir)
    elif is_checkpoint_directory(os.path.join(model_dir , 'output/model')):
        model_dir = os.path.join(model_dir , 'output/model')
    elif is_checkpoint_directory(os.path.join(model_dir , 'output/checkpoint')):
        model_dir = os.path.join(model_dir , 'output/checkpoint')
    elif is_checkpoint_directory(os.path.join(model_dir , 'model')):
        model_dir = os.path.join(model_dir , 'model')
    elif is_checkpoint_directory(os.path.join(model_dir , 'checkpoint')):
        model_dir = os.path.join(model_dir , 'checkpoint')
    elif not is_checkpoint_directory(model_dir):
        raise ValueError("No valid checkpoint found")

    checkpoint_name = get_last_checkpoint_filename(model_dir)
    print(checkpoint_name)

    if params['from_preprocessing']:
        train_set = 'tfrecord/train.tfrecord*'
        eval_set = 'tfrecord/eval.tfrecord*'
    else:
        train_set = '*.tfrecord'
        eval_set = 'default.tfrecord'

    params = create_pipeline(os.path.join(model_dir , 'pipeline.config'),
        os.path.join(model_dir , checkpoint_name),
        os.path.join(data_dir, 'label_map.pbtxt'),
        os.path.join(data_dir, train_set),
        os.path.join(data_dir, eval_set),
        os.path.join(checkpoint_dir, 'pipeline.config'),
        params)
        
    return_code = subprocess.call(['python',
        os.path.join(params['tfod_path'],'research/object_detection/model_main.py'),
        '--alsologtostderr',
        '--model_dir={}'.format(checkpoint_dir),
        '--pipeline_config_path={}'.format(os.path.join(checkpoint_dir, 'pipeline.config')),
        '--num_train_steps={}'.format(params['epochs'])
    ])
    if return_code != 0:
        raise RuntimeError('Training process failed')

    return_code = subprocess.call(['python',
        os.path.join(params['tfod_path'],'research/object_detection/export_inference_graph.py'),
        '--input-type=image_tensor',
        '--pipeline_config_path={}'.format(os.path.join(checkpoint_dir, 'pipeline.config')),
        '--trained_checkpoint_prefix={}-{}'.format(os.path.join(checkpoint_dir, 'model.ckpt'), params['epochs']),
        '--output_directory={}'.format(trained_model_dir)
    ])
    if return_code != 0:
        raise RuntimeError('Model export process failed')

    # generate lable map
    convert_labels_to_csv(data_dir, trained_model_dir)
    print('Training complete and output saved')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train TFOD.')
    parser.add_argument('--dataset', default='/mnt/data/datasets')
    parser.add_argument('--extras', default='', help='hyperparameters or other configs')
    parser.add_argument('--sys_finetune_checkpoint', default='', help='path to checkpoint')
    parser.add_argument('--model', default='frcnn-res50-coco', help='which model to train')
    parser.add_argument('--num_classes', default=81, type=int, help='number of classes')
    parser.add_argument('--tfod_path', default='/mnt/src/tf', help='path to tensorflow/models repository')
    parser.add_argument('--output_path', default='/mnt/output', help='path to output files')
    parser.add_argument('--model_path', default='/mnt/data/models', help='path to pretrained models')
    parser.add_argument('--from_preprocessing', default=False, type=bool)
    args = parser.parse_args()
    # parse parameters
    # sample: epochs=100;num_classes=1
    try:
        params = yaml.load(args.extras, Loader=FullLoader)
    except:
        raise ValueError('Parameters must have a valid YAML format')
    if not isinstance(params, dict):
        raise TypeError('Parameters must have a valid YAML format')
    params.update(vars(args))
    params.pop('extras')
    print('Processed parameters: ', params)
    main(params)

