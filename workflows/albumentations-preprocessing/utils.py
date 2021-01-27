import os
import json
import copy
import cv2
import subprocess
from typing import Any

from cv2 import data

def save_datasets(output_path, train_set, val_set):
    with open(
        os.path.join(output_path, 'train_set/annotations/instances_default.json'),
        'w'
    ) as f:
        json.dump(train_set,f)
    with open(
        os.path.join(output_path, 'eval_set/annotations/instances_default.json'),
        'w'
    ) as f:
        json.dump(val_set,f)

def get_annotation_from_image_id(dataset: dict, image_id: int) -> dict:
    annotations = []
    for annotation in dataset['annotations']:
        if annotation['image_id'] == image_id:
            annotations.append(copy.deepcopy(annotation))
    return annotations

def load_image(path: str) -> Any:
    image = cv2.imread(path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image

def save_image(path: str, image: Any) -> None:
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(path, image)

def bbox_coco2albumentations(bboxes: list, img: Any) -> list:
    album_boxes = []
    h, w, _ = img.shape
    for bbox in bboxes:
        x_min, y_min, width, height = bbox
        x_max = x_min + width
        y_max = y_min + height
        x_min, x_max = x_min / w, x_max / w
        y_min, y_max = y_min / h, y_max / h
        album_boxes.append([x_min, y_min, x_max, y_max])
    return album_boxes

def bbox_albumentations2coco(bboxes:list, img: Any) ->list:
    coco_boxes = []
    h, w, _ = img.shape
    for bbox in bboxes:
        x_min, y_min, x_max, y_max = bbox
        x_min, x_max = x_min * w, x_max * w
        y_min, y_max = y_min * h, y_max * h
        width = x_max - x_min
        height = y_max - y_max
        coco_boxes.append([x_min, y_min, width, height])
    return coco_boxes

def export_dataset(dataset: dict, format: str=None, output_folder: str='') -> None:
    if format == 'tfrecord':
        export_to_tfrecord(output_folder, 'train')
        export_to_tfrecord(output_folder, 'eval')
        export_label_map(output_folder, dataset)

def export_to_tfrecord(output_folder: str, mode: str) -> None:
    return_value = subprocess.call([
        'python',
        'utils/create_coco_tf_record.py',
        '--image_dir={}'.format(os.path.join(output_folder, '{}_set/images/'.format(mode))),
        '--object_annotations_file={}'.format(os.path.join(output_folder, '{}_set/annotations/instances_default.json'.format(mode))),
        '--output_file_prefix={}'.format(os.path.join(output_folder, 'tfrecord/{}.tfrecord'.format(mode)))
    ])
    if return_value != 0:
        raise RuntimeError('Failed to save {} dataset'.format(mode))

def export_label_map(output_folder: str, dataset: dict):
    if 'categories' in dataset:
        with open(os.path.join(output_folder, 'label_map.pbtxt'), 'w', encoding='utf8') as f:
            for category in dataset['categories']:
                f.write("item {{\n\tid: {}\n\tname: '{}'\n}}\n\n".format(category['id'], category['name']))
