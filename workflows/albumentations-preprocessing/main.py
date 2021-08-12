import os
import argparse
from val_split import split_dataset
from data_augmentation import data_augmentation
from utils import export_dataset

            
def main(args: argparse.Namespace) -> int:

    train_set, val_set = split_dataset(
        dataset_name=args.annotations_filename, 
        val_split=args.val_split, 
        input_path=args.input_folder, 
        output_path=args.output_folder
    )

    data_augmentation(
        args.data_aug_params, 
        train_set, 
        data_folder=os.path.join(args.output_folder, 'train_set/'),
        aug_steps= args.aug_steps
    )

    export_dataset(train_set, args.format, args.output_folder)
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Data splitting and augmentation pipeline')
    parser.add_argument('--input_folder', default='/mnt/data/datasets/')
    parser.add_argument('--output_folder', default='/mnt/output/')
    parser.add_argument('--annotations_filename', default='instances_default.json')
    parser.add_argument('--val_split', default=20, type=float)
    parser.add_argument('--aug_steps', default=1, type=int)
    parser.add_argument('--data_aug_params', default='')
    parser.add_argument('--format', default=None)
    args = parser.parse_args()
    main(args)