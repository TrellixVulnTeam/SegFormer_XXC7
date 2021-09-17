from argparse import ArgumentParser
import os

import torch
from mmseg.apis import inference_segmentor, init_segmentor, show_result_pyplot
from mmseg.core.evaluation import get_palette
import mmcv
from PIL import Image
import numpy as np
import time
import tqdm



def main():
    parser = ArgumentParser()
    parser.add_argument('config', help='Config file') # default='local_configs/segformer/B2/segformer.b2.1024x1024.sber.160k.py'
    parser.add_argument('checkpoint', help='Checkpoint file') #  default='work_dirs/segformer.b2.1024x1024.sber.160k/iter_160000.pth'
    parser.add_argument('--images', help='Images path', default='/home/ghadeer/Projects/Datasets/SberMerged/test/images/')
    parser.add_argument('--save-path', help='Path to save resulted images', default='results/')
    parser.add_argument(
        '--device', default='cuda:0', help='Device used for inference')
    parser.add_argument(
        '--palette',
        default='sber',
        help='Color palette used for segmentation map')
    parser.add_argument('--num-classes', help='Number of classes', default=6, choices=['6','7'])
    parser.add_argument('--save-tensor', action='store_true', help='Save tensor data into file')
    args = parser.parse_args()
    if args.save_path == "results/":
        save_path = "results/" + str(time.time()) + '/'
    else:
        save_path = args.save_path
    os.makedirs(save_path, exist_ok=True)
    os.makedirs(save_path+'semantic/', exist_ok=True)
    os.makedirs(save_path+'confidence/', exist_ok=True)
    os.makedirs(save_path+'data/', exist_ok=True)

    # build the model from a config file and a checkpoint file
    model = init_segmentor(args.config, args.checkpoint, device=args.device)
    # Create a list of all images:
    images = [x for x in os.listdir(args.images) if "." in x]

    if int(args.num_classes) == 7:
        #           -- Void --     -- Mirror --      -- FUO --      -- Glass --      -- OOP --     -- Floor --   -- background  --
        palette = [[255,255,255],[102, 255, 102], [245, 147, 49], [51, 221, 255], [184, 61, 245], [250, 50, 83], [0, 0, 0]]
    elif int(args.num_classes) == 6:
        #           -- Mirror --      -- Glass --      -- FUO --      -- OOP --     -- Floor --   -- background  --
        palette = [[102, 255, 102], [51, 221, 255], [245, 147, 49], [184, 61, 245], [250, 50, 83], [0, 0, 0], [255, 255, 255]]
    else:
        raise AssertionError('Wrong number of classes')
    print(f"Number of classes was set to {args.num_classes}")
    print(f"Flag for saving tensors was set to {args.save_tensor}")
    palette = np.array(palette)

    bar = tqdm.tqdm(total=len(images), desc="Making masks...")
    for name in images:
        path_to_img = args.images + name

        # Getting the results from the model
        result, output = inference_segmentor(model, path_to_img)
        seg = result[0]

        color_seg = np.zeros((seg.shape[0], seg.shape[1], 3), dtype=np.uint8)

        # Recolor the resulted image to match the needed colors
        for label, color in enumerate(palette):
            color_seg[seg == label, :] = color
        
        color_seg = color_seg[..., ::-1]
        img = color_seg.astype(np.uint8)


        # Saving the resulted image
        image = Image.fromarray(mmcv.bgr2rgb(img))
        confidence = Image.fromarray((255*torch.max(output.squeeze(), 0)[0]).cpu().detach().numpy().astype('uint8'), mode='L')
        image.save(save_path+'semantic/'+name)
        confidence.save(save_path+'confidence/'+name)
        if args.save_tensor:    
            torch.save(output.squeeze().cpu(),save_path+'data/'+name[:-4]+'.pt')
        bar.update()
    bar.close()


if __name__ == '__main__':
    main()
