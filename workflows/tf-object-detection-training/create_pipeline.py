import sys
import tensorflow as tf
from google.protobuf import text_format
from object_detection.protos import pipeline_pb2
import argparse

def create_pipeline(pipeline_path,model_path,label_path,train_tfrecord_path,eval_tfrecord_path,out_pipeline_path,epochs, num_classes,num_clones,format, params):
    print((pipeline_path,model_path,label_path,train_tfrecord_path,eval_tfrecord_path,out_pipeline_path,epochs,format))
    params_n = params
    print(params_n)
    pipeline_config = pipeline_pb2.TrainEvalPipelineConfig()                                                                                                                                                                                                          
    with tf.gfile.GFile(pipeline_path, "r") as f:                                                                                                                                                                                                                     
        proto_str = f.read()                                                                                                                                                                                                                                          
        text_format.Merge(proto_str, pipeline_config) 
    if format == "ssd":
        pipeline_config.model.ssd.num_classes=int(num_classes)
        if 'image-height' in params_n:
            pipeline_config.model.ssd.image_resizer.fixed_shape_resizer.height = int(params_n['image-height'])
        if 'image-width' in params_n:
            pipeline_config.model.ssd.image_resizer.fixed_shape_resizer.width = int(params_n['image-width'])
    else:  #faster-rcnn based models
        pipeline_config.model.faster_rcnn.num_classes=int(num_classes)
        if int(num_clones) != 1:
            pipeline_config.train_config.batch_size = int(num_clones)
        if 'min-dimension' in params_n:
            pipeline_config.model.faster_rcnn.image_resizer.keep_aspect_ratio_resizer.min_dimension = int(params_n['min-dimension'])
        if 'max-dimension' in params_n:
            pipeline_config.model.faster_rcnn.image_resizer.keep_aspect_ratio_resizer.max_dimension = int(params_n['max-dimension'])
        if 'schedule-step-1' in params_n:
            pipeline_config.train_config.optimizer.momentum_optimizer.learning_rate.manual_step_learning_rate.schedule[0].step = int(params_n['schedule-step-1'])
        if 'schedule-step-2' in params_n:
            pipeline_config.train_config.optimizer.momentum_optimizer.learning_rate.manual_step_learning_rate.schedule[1].step = int(params_n['schedule-step-2'])
    
    pipeline_config.train_config.fine_tune_checkpoint=model_path
    pipeline_config.train_config.num_steps=int(epochs)
    pipeline_config.train_input_reader.label_map_path=label_path
    pipeline_config.train_input_reader.tf_record_input_reader.input_path[0]=train_tfrecord_path

    pipeline_config.eval_input_reader[0].label_map_path=label_path
    pipeline_config.eval_input_reader[0].tf_record_input_reader.input_path[0]=eval_tfrecord_path

    config_text = text_format.MessageToString(pipeline_config)                                                                                                                                                                                                        
    with tf.gfile.Open(out_pipeline_path, "wb") as f:                                                                                                                                                                                                                       
        f.write(config_text)                                                                                                                                                                                                                                       

if __name__== "__main__":


    parser = argparse.ArgumentParser()

    parser.add_argument("-in_pipeline", "--input_pipeline_path", dest = "in_pipeline_path", default = "", help="Model Pipeline Path")
    parser.add_argument("-model", "--input_model_path", dest = "model_path", default = "", help="Input Model Path")
    parser.add_argument("-label", "--label_path",dest ="label_path", help="label_path")
    parser.add_argument("-epochs", "--number_epochs",dest ="epoch", help="epochs")
    parser.add_argument("-num_classes", "--num_classes",dest ="num_classes", help="num_classes")
    parser.add_argument("-train_data", "--train_tfrecord_path",dest = "train_tfrecord_path", help="train_tfrecord_path")
    parser.add_argument("-eval_data", "--eval_tfrecord_path",dest = "eval_tfrecord_path", help="eval_tfrecord_path")
    parser.add_argument("-num_clones", "--num_clones", dest="num_clones", help="num of gpus")
    parser.add_argument("-format","--format",dest="format",help="model format")
    parser.add_argument("-out_pipeline", "--output_pipeline_path", dest = "out_pipeline_path", default = "", help="Output Model Pipeline Path")
    parser.add_argument("-extra","--extra",dest="extra",help="extra params")
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    create_pipeline(args.in_pipeline_path,args.model_path,args.label_path,args.train_tfrecord_path,args.eval_tfrecord_path,args.out_pipeline_path,args.epoch, args.num_classes, args.num_clones, args.format, args.extra)
