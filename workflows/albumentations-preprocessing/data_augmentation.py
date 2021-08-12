from albumentations.core.composition import Compose
import json
import yaml
import copy
import albumentations as A
from tqdm import tqdm
from yaml.loader import FullLoader
from inspect import getmembers
from utils import load_image, save_image, get_annotation_from_image_id

def data_augmentation(aug_params: str, dataset: dict, data_folder: str='', aug_steps: int=1) -> None:
    if len(aug_params) > 1 and aug_steps >= 1:
        print('\n Performing Data Augmentation')
        aug_dataset = copy.deepcopy(dataset)
        transform = create_transformation(aug_params)
        for step in range(aug_steps):
            print("Augmentation step: {}".format(step))
            for image_data in tqdm(dataset['images']):
                image_id = image_data['id']
                annotations = get_annotation_from_image_id(dataset, image_id)
                bboxes = [annotation['bbox'].copy() for annotation in annotations]
                labels = [annotation['category_id'] for annotation in annotations]
                keypoints, keypoint_map = polygon2keypoint(annotations)
                img_path = data_folder + 'images/' + image_data['file_name'].split('/')[-1]
                img_sufix = img_path.split('.')[-1]
                img = load_image(img_path)
                transformed = transform(image=img, bboxes=bboxes, class_labels=labels, keypoints=keypoints)
                transformed_image = transformed['image']
                transformed_bboxes = transformed['bboxes']
                transformed_keypoints = transformed['keypoints']
                if len(transformed_bboxes) == len(bboxes) and len(transformed_keypoints) == len(keypoints):
                    h, w, _ = transformed_image.shape
                    new_img = copy.deepcopy(image_data)
                    new_img['id'] = len(aug_dataset['images'])
                    new_img['file_name'] = '{:04d}.'.format(new_img['id'])+img_sufix
                    new_img['height'] = h
                    new_img['width'] = w
                    aug_dataset['images'].append(new_img)
                    for idx, annotation in enumerate(annotations):
                        annotation['bbox'] = transformed_bboxes[idx]
                        annotation['image_id'] = new_img['id']
                        annotation['id'] = len(aug_dataset['annotations'])
                        annotation['segmentation'] = keypoint2polygon(transformed_keypoints, keypoint_map, idx)
                        aug_dataset['annotations'].append(annotation)
                    new_img_path = data_folder + 'images/' + new_img['file_name']
                    save_image(new_img_path, transformed_image)
        with open(data_folder+'annotations/instances_default.json','w') as f:
            json.dump(aug_dataset,f)
        print('Done')

def create_transformation(aug_params: str) -> Compose:
    try: 
        params_dict = yaml.load(aug_params, Loader=FullLoader)
    except:
        raise ValueError('Parameters must have a valid YAML format')
    if not isinstance(params_dict, dict):
        raise TypeError('Parameters must have a valid YAML format')
    members_dict = {a:b for (a,b) in getmembers(A)}
    transformation_list = []
    for transformation in params_dict.keys():
        if transformation in members_dict:
            transformation_list.append(members_dict[transformation](**params_dict[transformation]))
        else:
            raise ValueError('"{}" is not a valid transformation, please refer to: https://albumentations.ai/docs/api_reference/augmentations/transforms/'.format(transformation))
    transform =  A.Compose(
        transformation_list, 
        bbox_params=A.BboxParams(format='coco', label_fields=['class_labels'], min_visibility=0.1), 
        keypoint_params=A.KeypointParams(format='xy', remove_invisible=True)
    )
    return transform

def polygon2keypoint(segmentations: list) -> list:
    keypoints = []
    keypoints_map = []
    counter = 0
    for segmentation in segmentations:
        keypoint_map = []
        if len(segmentation['segmentation']) == 1:
            for idx in range(len(segmentation['segmentation'][0])//2):
                keypoints.append([segmentation['segmentation'][0][2*idx], segmentation['segmentation'][0][2*idx+1]])
                keypoint_map.append(counter)
                counter = counter + 1
            keypoints_map.append(keypoint_map)
    return keypoints, keypoints_map

def keypoint2polygon(keypoints: list, keypoint_map: list, idx: int) -> list:
    segmentation = []
    if len(keypoint_map) > idx:
        for map_idx in keypoint_map[idx]:
            segmentation.append(keypoints[map_idx][0])
            segmentation.append(keypoints[map_idx][1])
    if len(segmentation) > 4:
        return [segmentation]
    else:
        return []