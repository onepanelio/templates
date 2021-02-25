import os
import copy
import json
import shutil
import random
from utils import save_datasets, get_annotation_from_image_id

def read_dataset(path: str='annotations/instances_default.json') -> dict:
    with open(path) as f:
        file = json.load(f)
    return file

def create_empty_datasets(categories: list) -> tuple:
    train_set={"images": [], "annotations": [], "info": {"url": "", "year": "", "version": "", "contributor": "", "date_created": "", "description": ""}, "licenses": [{"name": "", "id": 0, "url": ""}], "categories": categories}
    val_set={"images": [], "annotations": [], "info": {"url": "", "year": "", "version": "", "contributor": "", "date_created": "", "description": ""}, "licenses": [{"name": "", "id": 0, "url": ""}], "categories": categories}
    return (train_set, val_set)

def split_dataset(dataset_name: str='instances_default.json', val_split: float=0.2, input_path: str='', output_path: str='') -> tuple:
    val_split /= 100
    if val_split > 1 or val_split < 0:
        raise ValueError('val_split should be between [0:100]')
    create_split_folders(output_path) 
    dataset = read_dataset(input_path + 'annotations/' + dataset_name)
    train_set, val_set = create_empty_datasets(dataset['categories'])
    print('Splitting dataset:')
    print('Total images: {}'.format(len(dataset['images'])))
    print('Total annotations: {}'.format(len(dataset['annotations'])))
    random.seed(99)
    for image in dataset['images']:
        rand = random.random()
        new_image = copy.deepcopy(image)
        new_annotations = get_annotation_from_image_id(dataset, new_image['id'])
        if rand < val_split:
            image_id = len(val_set['images'])
            new_image['id'] = image_id
            for new_annotation in new_annotations:
                annotation_id = len(val_set['annotations'])
                new_annotation['id'] = annotation_id
                new_annotation['image_id'] = image_id
                segmentations = new_annotation['segmentation']
                new_annotation['segmentation'] = []
                for segmentation in segmentations:
                    if len(segmentation) > 4 and len(segmentation) % 2 == 0:
                        new_annotation['segmentation'].append(segmentation)
                val_set['annotations'].append(new_annotation)
            old_filename = new_image['file_name'].split('/')[-1]
            img_sufix = old_filename.split('.')[-1]
            new_image['file_name'] = '{:04d}.'.format(image_id)+img_sufix
            val_set['images'].append(new_image)
            shutil.copyfile(input_path+'images/'+old_filename,output_path+'eval_set/images/'+new_image['file_name'])
        else:
            image_id = len(train_set['images'])
            new_image['id'] = image_id
            for new_annotation in new_annotations:
                annotation_id = len(train_set['annotations'])
                new_annotation['id'] = annotation_id
                new_annotation['image_id'] = image_id
                segmentations = new_annotation['segmentation']
                new_annotation['segmentation'] = []
                for segmentation in segmentations:
                    if len(segmentation) > 4 and len(segmentation) % 2 == 0:
                        new_annotation['segmentation'].append(segmentation)
                train_set['annotations'].append(new_annotation)
            old_filename = new_image['file_name'].split('/')[-1]
            img_sufix = old_filename.split('.')[-1]
            new_image['file_name'] = '{:04d}.'.format(image_id)+img_sufix
            train_set['images'].append(new_image)
            shutil.copyfile(input_path+'images/'+old_filename,output_path+'train_set/images/'+new_image['file_name'])

    save_datasets(output_path, train_set, val_set)

    print('\nSplitting done!')
    print('Train images: {}'.format(len(train_set['images'])))
    print('Train annotations: {}'.format(len(train_set['annotations'])))
    print('Eval images: {}'.format(len(val_set['images'])))
    print('Eval annotations: {}'.format(len(val_set['annotations'])))

    return train_set, val_set

def create_split_folders(output_path: str) -> None:
    directories = [
        'train_set/images/',
        'train_set/annotations/',
        'eval_set/images/',
        'eval_set/annotations/'
    ]
    for directory in directories:
        full_dir = os.path.join(output_path, directory)
        if not os.path.isdir(full_dir):
            os.makedirs(full_dir)