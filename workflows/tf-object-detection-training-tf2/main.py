import sys
import os
import subprocess
import shutil
import urllib.request
import tarfile
import argparse

from utils import convert_labels_to_csv, create_pipeline


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
        #urllib.request.urlretrieve('https://github.com/onepanelio/templates/releases/download/v0.2.0/{}.tar'.format(params['model']), '/mnt/data/models/model.tar')
        urllib.request.urlretrieve('http://download.tensorflow.org/models/object_detection/tf2/20200711/faster_rcnn_resnet50_v1_800x1333_coco17_gpu-8.tar.gz'.format(params['model']), '/mnt/data/models/model.tar')
        model_files = tarfile.open('/mnt/data/models/model.tar')
        model_files.extractall('/mnt/data/models')
        model_files.close()
        #model_dir = '/mnt/data/models/'+params['model']
        model_dir = '/mnt/data/models/'+'faster_rcnn_resnet50_v1_800x1333_coco17_gpu-8'
        files = os.listdir(model_dir)
        for f in files:
            shutil.move(model_dir+'/'+f,'/mnt/data/models')

    params = create_pipeline('/mnt/data/models/pipeline.config',
        '/mnt/data/models/checkpoint/ckpt-0',
        params['dataset']+'/label_map.pbtxt',
        params['dataset']+'/*.tfrecord',
        params['dataset']+'/default.tfrecord',
        '/mnt/output/pipeline.config',
        params)

    os.chdir('/mnt/output')
    os.mkdir('eval/')
    return_code = subprocess.call(['python',
        '/mnt/src/tf/research/object_detection/model_main_tf2.py',
        '--pipeline_config_path=/mnt/output/pipeline.config',
        '--model_dir=/mnt/output/',
        '--num_train_steps={}'.format(params['epochs'])
    ])
    if return_code != 0:
        raise RuntimeError('Training process failed')
    return_code = subprocess.call(['python',
        '/mnt/src/tf/research/object_detection/exporter_main_v2.py',
        '--input_type=image_tensor',
        '--pipeline_config_path=/mnt/output/pipeline.config',
        '--trained_checkpoint_dir=/mnt/output/',
        '--output_directory=/mnt/output/model/'
    ])
    if return_code != 0:
        raise RuntimeError('Model export process failed')

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
    