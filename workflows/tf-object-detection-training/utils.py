
import os
import json
import yaml
import csv
import numpy as np
import tensorflow as tf
from google.protobuf import text_format
from object_detection.protos import pipeline_pb2

def get_default_params(model):
    with open('defaults.json', 'r') as f:
        default_dict = json.load(f)
    return default_dict[model].copy()

def legacy_params_compatibility(params):
    new_params = params.copy()
    if "num-clones" in params:
        new_params["num_clones"] = params["num-clones"]
    if "batch-size" in params:
        new_params["batch_size"] = params["batch-size"]
    if "initial-learning-rate" in params:
        new_params["initial_learning_rate"] = params["initial-learning-rate"]
    if "learning_rate" in params:
        new_params["initial_learning_rate"] = params["learning_rate"]
    if "num-steps" in params:
        new_params["num_steps"] = params["num-steps"]
    if "schedule-step-1" in params:
        new_params["schedule_step_1"] = params["schedule-step-1"]
    if "schedule-lr-1" in params:
        new_params["schedule_lr_1"] = params["schedule-lr-1"]
    if "schedule-step-2" in params:
        new_params["schedule_step_2"] = params["schedule-step-2"]
    if "schedule-step-1" in params:
        new_params["schedule_lr_2"] = params["schedule-lr-2"]
    if "image-height" in params:
        new_params["image_height"] = params["image-height"]
    if "image-width" in params:
        new_params["image_width"] = params["image-width"]
    
    return new_params

def process_params(params):
    model_params = get_default_params(params['model'])
    params = legacy_params_compatibility(params)

    if ('ssd-mobilenet-v2-coco' in params['model'] or 'ssd-mobilenet-v1-coco2' in params['model']) or 'ssdlite-mobilenet-coco' in params['model']:
        model_architecture = 'ssd'
    else:
        model_architecture = 'frcnn'
    
    model_params['eval_interval_secs'] = 3000
    model_params['epochs'] = params.pop('num_steps')

    for key in params.keys():
        model_params[key] = params[key]

    return model_params, model_architecture

def convert_labels_to_csv(path, output_path):
    with open(os.path.join(path, 'label_map.pbtxt'),'r') as f:
        txt = f.readlines()
    print('Generating label maps file...')
    csv_out = open(os.path.join(output_path, 'classes.csv'), 'w')
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
    with open(os.path.join(output_path, 'label_map.json'), 'w') as outfile:
        json.dump(d, outfile)
    print('Finished generating label maps file')

def create_pipeline(pipeline_path, model_path, label_path,
                    train_tfrecord_path, eval_tfrecord_path, 
                    out_pipeline_path,params):

    model_params, model_architecture = process_params(params)

    pipeline_config = pipeline_pb2.TrainEvalPipelineConfig()
    with tf.gfile.GFile(pipeline_path, 'r') as f:
        proto_str = f.read()
        text_format.Merge(proto_str, pipeline_config)
    if model_architecture == 'ssd':
        pipeline_config.model.ssd.num_classes=int(model_params['num_classes'])
        pipeline_config.model.ssd.image_resizer.fixed_shape_resizer.height = int(model_params['image_height'])
        pipeline_config.model.ssd.image_resizer.fixed_shape_resizer.width = int(model_params['image_width'])
        pipeline_config.model.ssd.feature_extractor.depth_multiplier=float(model_params['depth_multiplier'])
        pipeline_config.model.ssd.feature_extractor.min_depth = int(model_params['min_depth'])
        pipeline_config.model.ssd.feature_extractor.conv_hyperparams.regularizer.l2_regularizer.weight = float(model_params['first_stage_regularizer_weight'])
        pipeline_config.model.ssd.feature_extractor.conv_hyperparams.initializer.truncated_normal_initializer.mean = float(model_params['first_stage_initializer_mean'])
        pipeline_config.model.ssd.feature_extractor.conv_hyperparams.initializer.truncated_normal_initializer.stddev = float(model_params['first_stage_initializer_stddev'])
        pipeline_config.model.ssd.feature_extractor.conv_hyperparams.activation = int(model_params['first_stage_activation'])
        pipeline_config.model.ssd.feature_extractor.conv_hyperparams.batch_norm.decay = float(model_params['first_stage_batchnorm_decay'])
        pipeline_config.model.ssd.feature_extractor.conv_hyperparams.batch_norm.epsilon = float(model_params['first_stage_batchnorm_epsilon'])
        pipeline_config.model.ssd.box_coder.faster_rcnn_box_coder.y_scale = float(model_params['boxcoder_y_scale'])
        pipeline_config.model.ssd.box_coder.faster_rcnn_box_coder.x_scale = float(model_params['boxcoder_x_scale'])
        pipeline_config.model.ssd.box_coder.faster_rcnn_box_coder.height_scale = float(model_params['boxcoder_height_scale'])
        pipeline_config.model.ssd.box_coder.faster_rcnn_box_coder.width_scale = float(model_params['boxcoder_width_scale'])
        pipeline_config.model.ssd.matcher.argmax_matcher.matched_threshold = float(model_params['matched_threshold'])
        pipeline_config.model.ssd.matcher.argmax_matcher.unmatched_threshold = float(model_params['unmatched_threshold'])
        pipeline_config.model.ssd.box_predictor.convolutional_box_predictor.conv_hyperparams.regularizer.l2_regularizer.weight = float(model_params['second_stage_regularizer_weight'])
        pipeline_config.model.ssd.box_predictor.convolutional_box_predictor.conv_hyperparams.initializer.truncated_normal_initializer.mean = float(model_params['second_stage_initializer_mean'])
        pipeline_config.model.ssd.box_predictor.convolutional_box_predictor.conv_hyperparams.initializer.truncated_normal_initializer.stddev = float(model_params['second_stage_initializer_stddev'])
        pipeline_config.model.ssd.box_predictor.convolutional_box_predictor.conv_hyperparams.activation = int(model_params['second_stage_activation'])
        pipeline_config.model.ssd.box_predictor.convolutional_box_predictor.conv_hyperparams.batch_norm.decay = float(model_params['second_stage_batchnorm_decay'])
        pipeline_config.model.ssd.box_predictor.convolutional_box_predictor.conv_hyperparams.batch_norm.epsilon = float(model_params['second_stage_batchnorm_epsilon'])
        pipeline_config.model.ssd.box_predictor.convolutional_box_predictor.min_depth = int(model_params['second_stage_min_depth'])
        pipeline_config.model.ssd.box_predictor.convolutional_box_predictor.max_depth = int(model_params['second_stage_max_depth'])
        pipeline_config.model.ssd.box_predictor.convolutional_box_predictor.num_layers_before_predictor = int(model_params['second_stage_num_layers_before_predictor'])
        pipeline_config.model.ssd.box_predictor.convolutional_box_predictor.use_dropout = model_params['second_stage_use_dropout']
        pipeline_config.model.ssd.box_predictor.convolutional_box_predictor.dropout_keep_probability = float(model_params['second_stage_dropout_keep_probability'])
        pipeline_config.model.ssd.box_predictor.convolutional_box_predictor.kernel_size = int(model_params['second_stage_dropout_kernel_size'])
        pipeline_config.model.ssd.box_predictor.convolutional_box_predictor.box_code_size = int(model_params['second_stage_dropout_box_code_size'])
        pipeline_config.model.ssd.anchor_generator.ssd_anchor_generator.num_layers = int(model_params['anchor_generator_num_layers'])
        pipeline_config.model.ssd.anchor_generator.ssd_anchor_generator.min_scale = float(model_params['anchor_generator_min_scale'])
        pipeline_config.model.ssd.anchor_generator.ssd_anchor_generator.max_scale = float(model_params['anchor_generator_max_scale'])
        pipeline_config.model.ssd.post_processing.batch_non_max_suppression.score_threshold = float(model_params['second_stage_nms_score_threshold'])
        pipeline_config.model.ssd.post_processing.batch_non_max_suppression.iou_threshold = float(model_params['second_stage_nms_iou_threshold'])
        pipeline_config.model.ssd.post_processing.batch_non_max_suppression.max_detections_per_class = int(model_params['second_stage_max_detections_per_class'])
        pipeline_config.model.ssd.post_processing.batch_non_max_suppression.max_total_detections = int(model_params['second_stage_max_detections_max_total_detections'])
        pipeline_config.model.ssd.loss.classification_weight = float(model_params['second_stage_classification_loss_weight'])
        pipeline_config.model.ssd.loss.localization_weight = float(model_params['second_stage_localization_loss_weight'])

        pipeline_config.train_config.optimizer.rms_prop_optimizer.learning_rate.exponential_decay_learning_rate.initial_learning_rate = float(model_params['initial_learning_rate'])
        pipeline_config.train_config.optimizer.rms_prop_optimizer.learning_rate.exponential_decay_learning_rate.decay_steps = int(model_params['decay_steps'])
        pipeline_config.train_config.optimizer.rms_prop_optimizer.learning_rate.exponential_decay_learning_rate.decay_factor = float(model_params['decay_factor'])
        pipeline_config.train_config.optimizer.rms_prop_optimizer.momentum_optimizer_value = float(model_params['momentum_optimizer_value'])
        pipeline_config.train_config.optimizer.rms_prop_optimizer.decay = float(model_params['momentum_decay'])
        pipeline_config.train_config.optimizer.rms_prop_optimizer.epsilon = float(model_params['momentum_epsilon'])
        pipeline_config.train_config.batch_size = int(model_params['batch_size'])
    else:  #faster-rcnn based models
        pipeline_config.model.faster_rcnn.num_classes=int(model_params['num_classes'])
        pipeline_config.model.faster_rcnn.image_resizer.keep_aspect_ratio_resizer.min_dimension = int(model_params['min_dimension'])
        pipeline_config.model.faster_rcnn.image_resizer.keep_aspect_ratio_resizer.max_dimension = int(model_params['max_dimension'])
        pipeline_config.model.faster_rcnn.feature_extractor.first_stage_features_stride = int(model_params['first_stage_features_stride'])
        pipeline_config.model.faster_rcnn.first_stage_anchor_generator.grid_anchor_generator.height_stride = int(model_params['height_stride'])
        pipeline_config.model.faster_rcnn.first_stage_anchor_generator.grid_anchor_generator.width_stride = int(model_params['width_stride'])
        pipeline_config.model.faster_rcnn.first_stage_box_predictor_conv_hyperparams.regularizer.l2_regularizer.weight = float(model_params['first_stage_regularizer_weight'])
        pipeline_config.model.faster_rcnn.first_stage_box_predictor_conv_hyperparams.initializer.truncated_normal_initializer.stddev = float(model_params['first_stage_initializer_stddev'])
        pipeline_config.model.faster_rcnn.first_stage_nms_score_threshold = float(model_params['first_stage_nms_score_threshold'])
        pipeline_config.model.faster_rcnn.first_stage_nms_iou_threshold = float(model_params['first_stage_nms_iou_threshold'])
        pipeline_config.model.faster_rcnn.first_stage_max_proposals = int(model_params['first_stage_max_proposals'])
        pipeline_config.model.faster_rcnn.first_stage_localization_loss_weight = float(model_params['first_stage_localization_loss_weight'])
        pipeline_config.model.faster_rcnn.first_stage_objectness_loss_weight = float(model_params['first_stage_objectness_loss_weight'])
        pipeline_config.model.faster_rcnn.initial_crop_size = int(model_params['initial_crop_size'])
        pipeline_config.model.faster_rcnn.maxpool_kernel_size = int(model_params['maxpool_kernel_size'])
        pipeline_config.model.faster_rcnn.maxpool_stride = int(model_params['maxpool_stride'])        
        pipeline_config.model.faster_rcnn.second_stage_box_predictor.mask_rcnn_box_predictor.fc_hyperparams.regularizer.l2_regularizer.weight = float(model_params['second_stage_regularizer_weight'])
        pipeline_config.model.faster_rcnn.second_stage_box_predictor.mask_rcnn_box_predictor.fc_hyperparams.initializer.variance_scaling_initializer.factor = float(model_params['second_stage_initializer_factor'])
        pipeline_config.model.faster_rcnn.second_stage_box_predictor.mask_rcnn_box_predictor.fc_hyperparams.initializer.variance_scaling_initializer.mode = int(model_params['second_stage_initializer_mode'])
        pipeline_config.model.faster_rcnn.second_stage_box_predictor.mask_rcnn_box_predictor.use_dropout = model_params['second_stage_use_dropout']
        pipeline_config.model.faster_rcnn.second_stage_box_predictor.mask_rcnn_box_predictor.dropout_keep_probability = float(model_params['second_stage_dropout_keep_probability'])
        pipeline_config.model.faster_rcnn.second_stage_post_processing.batch_non_max_suppression.score_threshold = float(model_params['second_stage_nms_score_threshold'])
        pipeline_config.model.faster_rcnn.second_stage_post_processing.batch_non_max_suppression.iou_threshold = float(model_params['second_stage_nms_iou_threshold'])
        pipeline_config.model.faster_rcnn.second_stage_post_processing.batch_non_max_suppression.max_detections_per_class = int(model_params['second_stage_max_detections_per_class'])
        pipeline_config.model.faster_rcnn.second_stage_post_processing.batch_non_max_suppression.max_total_detections = int(model_params['second_stage_max_detections_max_total_detections'])
        pipeline_config.model.faster_rcnn.second_stage_localization_loss_weight = float(model_params['second_stage_localization_loss_weight'])
        pipeline_config.model.faster_rcnn.second_stage_classification_loss_weight = float(model_params['second_stage_classification_loss_weight'])

        pipeline_config.train_config.optimizer.momentum_optimizer.learning_rate.manual_step_learning_rate.initial_learning_rate = float(model_params['initial_learning_rate'])
        pipeline_config.train_config.optimizer.momentum_optimizer.learning_rate.manual_step_learning_rate.schedule[0].step = int(model_params['schedule_step_1'])
        pipeline_config.train_config.optimizer.momentum_optimizer.learning_rate.manual_step_learning_rate.schedule[0].learning_rate = float(model_params['schedule_lr_1'])
        pipeline_config.train_config.optimizer.momentum_optimizer.learning_rate.manual_step_learning_rate.schedule[1].step = int(model_params['schedule_step_2'])
        pipeline_config.train_config.optimizer.momentum_optimizer.learning_rate.manual_step_learning_rate.schedule[1].learning_rate = float(model_params['schedule_lr_2'])
        pipeline_config.train_config.optimizer.momentum_optimizer.momentum_optimizer_value = float(model_params['momentum_optimizer_value'])
        if int(model_params['batch_size']) <= 1:
            pipeline_config.train_config.batch_size = int(model_params['num_clones'])
        else:
            pipeline_config.train_config.batch_size = int(model_params['num_clones']) * int(model_params['batch_size'])
            pipeline_config.model.faster_rcnn.image_resizer.keep_aspect_ratio_resizer.pad_to_max_dimension = True

    pipeline_config.train_config.fine_tune_checkpoint=model_path
    pipeline_config.train_config.num_steps=int(model_params['epochs'])
    if len(model_params['sys_finetune_checkpoint'])>1:
        pipeline_config.train_config.load_all_detection_checkpoint_vars=True
    pipeline_config.train_input_reader.label_map_path=label_path
    pipeline_config.train_input_reader.tf_record_input_reader.input_path[0]=train_tfrecord_path

    pipeline_config.eval_input_reader[0].label_map_path=label_path
    pipeline_config.eval_input_reader[0].tf_record_input_reader.input_path[0]=eval_tfrecord_path
    pipeline_config.eval_config.eval_interval_secs = int(model_params['eval_interval_secs'])

    config_text = text_format.MessageToString(pipeline_config)
    with tf.gfile.Open(out_pipeline_path, 'wb') as f:
        f.write(config_text)
    return model_params
