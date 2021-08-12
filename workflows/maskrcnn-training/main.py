"""
Mask R-CNN

Copyright (c) 2017 Matterport, Inc.
Licensed under the MIT License (see LICENSE for details)

------------------------------------------------------------

Usage: import the module (see Jupyter notebooks for examples), or run from
       the command line as such:

    # Continue training from COCO pretrained weights
    python3 main.py train --dataset=/path/to/coco/ --model=workflow_maskrcnn --num_classes=2 --extras="parameters string()" --logs=/path/to/output

    # Continue training a model that you had trained earlier
    python3 main.py train --dataset=/path/to/coco/ --model=/path/to/weights.h5 --num_classes=2 --extras="parameters string()" --logs=/path/to/output

    # Continue training a model that you had trained earlier using workflows
    python3 main.py train --dataset=/path/to/coco/ --model=workflow_maskrcnn --num_classes=2 --extras="parameters string()" --logs=/path/to/output --ref_model_path="reference name"

    # Run COCO evaluation on the last model you trained
    python3 main.py evaluate --dataset=/path/to/coco/ --model=last

"""

import os
import time
import json
import csv
import shutil
import yaml
import numpy as np
from tensorflow.config import list_physical_devices

import imgaug  # https://github.com/aleju/imgaug (pip3 install imgaug)

from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
from pycocotools import mask as maskUtils
import urllib.request
import shutil

# Import Mask RCNN
from mrcnn.config import Config
from mrcnn import model as modellib, utils

############################################################
#  Configurations
############################################################


class OnepanelConfig(Config):
    """Configuration for training on MS COCO format dataset.
    Derives from the base Config class and overrides values specific
    to the MS COCO format.
    """
    def __init__(self, params):
        self.NAME = "onepanel"
        for param in params.keys():
            if hasattr(self, param.upper()):
                setattr(self, param.upper(), params[param])
        if 'gpu_count' not in params:
            self.GPU_COUNT = 1
            num_gpus = len(list_physical_devices(device_type='GPU'))
            if num_gpus in [2,4,8]:
                self.GPU_COUNT = num_gpus
        super().__init__()
    

############################################################
#  Dataset
############################################################

class OnepanelDataset(utils.Dataset):
    def load_coco(self, dataset_dir):
        """Load a subset of the COCO dataset.
        dataset_dir: The root directory of the dataset in MS COCO format.
        """

        coco = COCO(os.path.join(dataset_dir, "annotations/instances_default.json"))
        image_dir = os.path.join(dataset_dir, "images/")

        # Load all classes or a subset?
        class_ids = sorted(coco.getCatIds())

        # All images or a subset?
        if class_ids:
            image_ids = []
            for id in class_ids:
                image_ids.extend(list(coco.getImgIds(catIds=[id])))
            # Remove duplicates
            image_ids = list(set(image_ids))
        else:
            # All images
            image_ids = list(coco.imgs.keys())

        # Add classes
        for i in class_ids:
            self.add_class("coco", i, coco.loadCats(i)[0]["name"])

        # Add images
        for i in image_ids:
            self.add_image(
                "coco", image_id=i,
                path=os.path.join(image_dir, os.path.basename(coco.imgs[i]['file_name'])),
                width=coco.imgs[i]["width"],
                height=coco.imgs[i]["height"],
                annotations=coco.loadAnns(coco.getAnnIds(
                    imgIds=[i], catIds=class_ids, iscrowd=None)))


    def load_mask(self, image_id):
        """Load instance masks for the given image.

        Different datasets use different ways to store masks. This
        function converts the different mask format to one format
        in the form of a bitmap [height, width, instances].

        Returns:
        masks: A bool array of shape [height, width, instance count] with
            one mask per instance.
        class_ids: a 1D array of class IDs of the instance masks.
        """
        # If not a COCO image, delegate to parent class.
        image_info = self.image_info[image_id]
        if image_info["source"] != "coco":
            return super(OnepanelDataset, self).load_mask(image_id)

        instance_masks = []
        class_ids = []
        annotations = self.image_info[image_id]["annotations"]
        # Build mask of shape [height, width, instance_count] and list
        # of class IDs that correspond to each channel of the mask.
        for annotation in annotations:
            class_id = self.map_source_class_id(
                "coco.{}".format(annotation['category_id']))
            if class_id:
                m = self.annToMask(annotation, image_info["height"],
                                   image_info["width"])
                # Some objects are so small that they're less than 1 pixel area
                # and end up rounded out. Skip those objects.
                if m.max() < 1:
                    continue
                # Is it a crowd? If so, use a negative class ID.
                if annotation['iscrowd']:
                    # Use negative class ID for crowds
                    class_id *= -1
                    # For crowd masks, annToMask() sometimes returns a mask
                    # smaller than the given dimensions. If so, resize it.
                    if m.shape[0] != image_info["height"] or m.shape[1] != image_info["width"]:
                        m = np.ones([image_info["height"], image_info["width"]], dtype=bool)
                instance_masks.append(m)
                class_ids.append(class_id)

        # Pack instance masks into an array
        if class_ids:
            mask = np.stack(instance_masks, axis=2).astype(np.bool)
            class_ids = np.array(class_ids, dtype=np.int32)
            return mask, class_ids
        else:
            # Call super class to return an empty mask
            return super(OnepanelDataset, self).load_mask(image_id)

    # The following two functions are from pycocotools with a few changes.

    def annToRLE(self, ann, height, width):
        """
        Convert annotation which can be polygons, uncompressed RLE to RLE.
        :return: binary mask (numpy 2D array)
        """
        segm = ann['segmentation']
        if isinstance(segm, list):
            # polygon -- a single object might consist of multiple parts
            # we merge all parts into one mask rle code
            try:
                rles = maskUtils.frPyObjects(segm, height, width)
            except IndexError:
                raise ValueError('Segmentations not found in annotations. Make sure to use polygons for annotations')
            rle = maskUtils.merge(rles)
        elif isinstance(segm['counts'], list):
            # uncompressed RLE
            rle = maskUtils.frPyObjects(segm, height, width)
        else:
            # rle
            rle = ann['segmentation']
        return rle

    def annToMask(self, ann, height, width):
        """
        Convert annotation which can be polygons, uncompressed RLE, or RLE to binary mask.
        :return: binary mask (numpy 2D array)
        """
        rle = self.annToRLE(ann, height, width)
        m = maskUtils.decode(rle)
        return m


############################################################
#  COCO Evaluation
############################################################

def build_coco_results(dataset, image_ids, rois, class_ids, scores, masks):
    """Arrange resutls to match COCO specs in http://cocodataset.org/#format
    """
    # If no results, return an empty list
    if rois is None:
        return []

    results = []
    for image_id in image_ids:
        # Loop through detections
        for i in range(rois.shape[0]):
            class_id = class_ids[i]
            score = scores[i]
            bbox = np.around(rois[i], 1)
            mask = masks[:, :, i]

            result = {
                "image_id": image_id,
                "category_id": dataset.get_source_class_id(class_id, "coco"),
                "bbox": [bbox[1], bbox[0], bbox[3] - bbox[1], bbox[2] - bbox[0]],
                "score": score,
                "segmentation": maskUtils.encode(np.asfortranarray(mask))
            }
            results.append(result)
    return results


def evaluate_coco(model, dataset, coco, eval_type="bbox", limit=0, image_ids=None):
    """Runs official COCO evaluation.
    dataset: A Dataset object with valiadtion data
    eval_type: "bbox" or "segm" for bounding box or segmentation evaluation
    limit: if not 0, it's the number of images to use for evaluation
    """
    # Pick COCO images from the dataset
    image_ids = image_ids or dataset.image_ids

    # Limit to a subset
    if limit:
        image_ids = image_ids[:limit]

    # Get corresponding COCO image IDs.
    coco_image_ids = [dataset.image_info[id]["id"] for id in image_ids]

    t_prediction = 0
    t_start = time.time()

    results = []
    for i, image_id in enumerate(image_ids):
        # Load image
        image = dataset.load_image(image_id)

        # Run detection
        t = time.time()
        r = model.detect([image], verbose=0)[0]
        t_prediction += (time.time() - t)

        # Convert results to COCO format
        # Cast masks to uint8 because COCO tools errors out on bool
        image_results = build_coco_results(dataset, coco_image_ids[i:i + 1],
                                           r["rois"], r["class_ids"],
                                           r["scores"],
                                           r["masks"].astype(np.uint8))
        results.extend(image_results)

    # Load results. This modifies results with additional attributes.
    coco_results = coco.loadRes(results)

    # Evaluate
    cocoEval = COCOeval(coco, coco_results, eval_type)
    cocoEval.params.imgIds = coco_image_ids
    cocoEval.evaluate()
    cocoEval.accumulate()
    cocoEval.summarize()

    print("Prediction time: {}. Average {}/image".format(
        t_prediction, t_prediction / len(image_ids)))
    print("Total time: ", time.time() - t_start)


############################################################
#  Training
############################################################

def evaluate(dataset_dir, model, limit):
    # Validation dataset
    dataset_val = OnepanelDataset()
    coco = dataset_val.load_coco(dataset_dir)
    dataset_val.prepare()
    print("Running COCO evaluation on {} images.".format(limit))
    evaluate_coco(model, dataset_val, coco, "bbox", limit=int(limit))


def train(params, model, config, train_dataset, val_dataset, output_folder, use_validation=False):
    # Training dataset. Use the training set and 35K from the
    # validation set, as as in the Mask RCNN paper.
    dataset_train = OnepanelDataset()
    dataset_train.load_coco(train_dataset)
    dataset_train.prepare()

    # Validation dataset
    if use_validation:
        dataset_val = OnepanelDataset()
        dataset_val.load_coco(val_dataset)
        dataset_val.prepare()
    else:
        dataset_val = dataset_train

    # Image Augmentation
    augmentation = get_augmentations(params)

    # *** Training schedule ***

    # Training - Stage 1
    if params['stage_1_epochs'] > 0:
        print("Training network heads")
        model.train(dataset_train, dataset_val,
                    learning_rate=config.LEARNING_RATE,
                    epochs=params['stage_1_epochs'],
                    layers='heads',
                    augmentation=augmentation)
    else:
        print("First stage skipped, {} sent as num of first stage epochs".format(params['stage_1_epochs']))

    # Training - Stage 2
    # Finetune layers from ResNet stage 4 and up
    if params['stage_2_epochs'] > params['stage_1_epochs']:
        print("Fine tune Resnet stage 4 and up")
        model.train(dataset_train, dataset_val,
                    learning_rate=config.LEARNING_RATE,
                    epochs=params['stage_2_epochs'],
                    layers='4+',
                    augmentation=augmentation)
    else:
        print("Second stage skipped, {} sent as num of second stage epochs".format(params['stage_2_epochs']))

    # Training - Stage 3
    # Fine tune all layers
    if params['stage_3_epochs'] > params['stage_2_epochs']:
        print("Fine tune all layers")
        model.train(dataset_train, dataset_val,
                    learning_rate=config.LEARNING_RATE / 10,
                    epochs=params['stage_3_epochs'],
                    layers='all',
                    augmentation=augmentation)
    else:
        print("Third stage skipped, {} sent as num of third stage epochs".format(params['stage_3_epochs']))

    # Extract trained model
    print("Training complete\n Extracting trained model")
    extract_model(train_dataset, output_folder, config, params)
    print("Workflow complete!")


############################################################
#  Utils
############################################################

def generate_csv(input_file, output_file):
	with open(input_file) as f:
		data = json.load(f)

	csv_out = open(os.path.join(output_file, "classes.csv"), "w", newline='')

	csv_writer = csv.writer(csv_out)
	csv_writer.writerow(['labels','id'])

	for lbl in data['categories']:
		csv_writer.writerow([lbl['name'], lbl['id']])


def preprocess_inputs(args):
    print("Command: ", args.command)
    print("Model: ", args.model)
    print("Checkpoint: ", args.ref_model_path)
    print("Dataset: ", args.dataset)
    print("Validation Dataset: ", args.val_dataset)
    print("Logs: ", args.output)
    print("Num Classes: ", args.num_classes)
    print("Extras: ", args.extras)
    try:
        params = yaml.load(args.extras)
    except:
        raise ValueError('Parameters must have a valid YAML format')
    if not isinstance(params, dict):
        raise TypeError('Parameters must have a valid YAML format')
    params['steps_per_epoch'] = params.pop('num_steps')
    params['num_classes'] = int(args.num_classes) + 1

    if 'stage-1-epochs' in params:
        params['stage_1_epochs'] = params.pop('stage-1-epochs')
    if 'stage-2-epochs' in params:
        params['stage_2_epochs'] = params.pop('stage-2-epochs')
    if 'stage-3-epochs' in params:
        params['stage_3_epochs'] = params.pop('stage-3-epochs')

    # Check num epochs sanity
    if 'stage_1_epochs' in params and 'stage_2_epochs' in params and 'stage_3_epochs' in params:
        params['stage_1_epochs'] = int(params['stage_1_epochs'])
        params['stage_2_epochs'] = params['stage_1_epochs'] + int(params['stage_2_epochs'])
        params['stage_3_epochs'] = params['stage_2_epochs'] + int(params['stage_3_epochs'])
    else:
        print('Num of epochs at each stage not provided, using default ones')
        params['stage_1_epochs'] = 1
        params['stage_2_epochs'] = 2
        params['stage_3_epochs'] = 3
    return params


def get_config(command, params):
    if command == "train":
        config = OnepanelConfig(params)
        # config.NUM_CLASSES = args.num_classes
    else:
        class InferenceConfig(OnepanelConfig):
            # Set batch size to 1 since we'll be running inference on
            # one image at a time. Batch size = GPU_COUNT * IMAGES_PER_GPU
            def __init__(self, params):
                params['gpu_count'] = 1
                params['images_per_gpu'] = 1
                super().__init__(params)
        config = InferenceConfig(params)
    return config


def create_model(command, config, logs_dir, selected_model, ref_model_path=''):
    if command == "train":
        model = modellib.MaskRCNN(mode="training", config=config,
                                  model_dir=logs_dir)
    else:
        model = modellib.MaskRCNN(mode="inference", config=config,
                                  model_dir=logs_dir)

    # Select weights file to load
    if selected_model.lower() == "workflow_maskrcnn":
        print("Executed from Onepanel workflow")
        if not os.path.exists("/mnt/data/models"):
            os.makedirs("/mnt/data/models")
        if ref_model_path == '':
            #download model
            if not os.path.isfile("/mnt/data/models/mask_rcnn_coco.h5"):
                print("Downloading COCO pretrained weights")
                urllib.request.urlretrieve("https://github.com/matterport/Mask_RCNN/releases/download/v2.0/mask_rcnn_coco.h5","/mnt/data/models/mask_rcnn_coco.h5")
            model_path = "/mnt/data/models/mask_rcnn_coco.h5"
        elif os.path.isfile("/mnt/data/models/output/model/onepanel_trained_model.h5"):
            model_path = "/mnt/data/models/output/model/onepanel_trained_model.h5"
        elif os.path.isfile("/mnt/data/models/model/onepanel_trained_model.h5"):
            model_path = "/mnt/data/models/model/onepanel_trained_model.h5"
        elif os.path.isfile("/mnt/data/models/onepanel_trained_model.h5"):
            model_path = "/mnt/data/models/onepanel_trained_model.h5"
        elif ref_model_path.split('.')[-1] == "h5" and os.path.isfile(os.path.join("/mnt/data/models/", ref_model_path.split('/')[-1])):
            model_path = os.path.join("/mnt/data/models/", ref_model_path.split('/')[-1])
        else:
                raise ValueError("No valid checkpoint found")
        print("Model found: {}".format(model_path))
    else:
        if os.path.isfile(selected_model):
            model_path = selected_model
        else:
            raise ValueError('Provided model is not valid, use "model" flag with a valid model for custom pretrained model')

    
    # Load weights
    # print("Loading weights ", model_path)
    if int(args.num_classes) != 81:
        model.load_weights(model_path, by_name=True, exclude=[ "mrcnn_class_logits", "mrcnn_bbox_fc", "mrcnn_bbox", "mrcnn_mask"])
    else:
        model.load_weights(model_path, by_name=True)
    return model


def extract_model(train_dataset, output_dir, config, params):
    generate_csv(
        os.path.join(train_dataset, "annotations/instances_default.json"), 
        os.path.join(output_dir, "model")
    )
    shutil.copyfile(
        os.path.join(output_dir, "checkpoints/mask_rcnn_{}_{:04d}.h5".format(config.NAME.lower(), int(params['stage_3_epochs']))),
        os.path.join(output_dir, "model/onepanel_trained_model.h5")
    )

def get_augmentations(params):
    # Image Augmentation
    if 'augmentations' in params:
        ## TODO: implement augmentation parsing
        augmentation = imgaug.augmenters.Fliplr(0.5)
    else:
        # Right/Left flip 50% of the time
        augmentation = imgaug.augmenters.Fliplr(0.5)
    return augmentation

def create_output_folders(output_dir):
    subdirs = ['tensorboard/heads', 'tensorboard/4+', 'tensorboard/all', 'checkpoints', 'model'] 
    for subdir in subdirs:
        dir = os.path.join(output_dir, subdir)
        if not os.path.isdir(dir):
            os.makedirs(dir)
            print('Path {} created!'.format(dir))

############################################################
#  Main
############################################################

def main(args):
    
    create_output_folders(args.output)

    params = preprocess_inputs(args)

    # Configurations
    config = get_config(args.command, params)
    config.display()

    # Create model
    model = create_model(args.command, config, args.output, args.model, args.ref_model_path)


    # Train or evaluate
    if args.command == "train":
        train(params, model, config, args.dataset, args.val_dataset, args.output, args.use_validation)

    elif args.command == "evaluate":
        # Validation dataset
        evaluate(args.dataset, model, args.limit)

    else:
        print("'{}' is not recognized. "
              "Use 'train' or 'evaluate'".format(args.command))

if __name__ == '__main__':
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Train Mask R-CNN on MS COCO.')
    parser.add_argument("command",
                        metavar="<command>",
                        help="'train' or 'evaluate' on MS COCO")
    parser.add_argument('--dataset', required=True,
                        metavar="/path/to/coco/",
                        help='Directory of the MS-COCO dataset')
    parser.add_argument('--val_dataset',
                        metavar="/path/to/coco/",
                        help='Directory of the validation MS-COCO dataset')
    parser.add_argument('--model', required=True,
                        metavar="/path/to/weights.h5",
                        help="Path to weights .h5 file or 'coco'")
    parser.add_argument('--output', required=False,
                        default="/mnt/output",
                        metavar="/path/to/logs/",
                        help='Logs and checkpoints directory ')
    parser.add_argument('--limit', required=False,
                        default=500,
                        metavar="<image count>",
                        help='Images to use for evaluation (default=500)')
    parser.add_argument('--extras', required=False, default=None, help="extra arguments from user")
    parser.add_argument('--num_classes', default=81, help="Number of classes present in a dataset")
    parser.add_argument('--ref_model_path', default='', help="ref model path")
    parser.add_argument('--use_validation', default=False, type=bool)
    args = parser.parse_args()
    
    # Run Workflow
    main(args)
