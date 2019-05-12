from algorithms.cnn_layer_visualization import CNNLayerVisualization
from algorithms.deep_dream import DeepDream

from algorithms.gradcam import GradCam
from algorithms.vanilla_backprop import VanillaBackprop
from algorithms.guided_backprop import GuidedBackprop
from algorithms.smooth_grad import generate_smooth_grad

import PIL
from PIL import Image

from utils.misc_functions import get_example_params, recreate_image, save_image,\
                            save_class_activation_images, apply_colormap_on_image
from utils.misc_functions import format_np_output, save_gradient_images, convert_to_grayscale

from torch.autograd import Variable

import torch
import numpy as np
from torchvision.models import alexnet
#from torchvision.models import resnet34, vgg19

import matplotlib.pyplot as plt

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class VisualInterpretator():

    def __init__(self, model):

        self.model = model
        self.cam_heatmaps = []
        self.grads = []

    def gradcam(self, image, target_layer, target_class):

        if isinstance(image, PIL.Image.Image):
            #image = image.resize((224, 224), Image.ANTIALIAS)
            tensor_image = torch.Tensor(np.array(image)).unsqueeze(0).permute(0, 3, 1, 2)

        if isinstance(image, np.ndarray):
            tensor_image = torch.Tensor(image).unsqueeze(0).permute(0, 3, 1, 2)

        grad_cam = GradCam(self.model, target_layer)
        cam_activation_map = grad_cam.generate_cam(tensor_image, target_class)

        heatmap, heatmap_on_image = apply_colormap_on_image(image, cam_activation_map, 'hsv')

        cam_activation_map = Image.fromarray(format_np_output(cam_activation_map))

        #heatmap = Image.fromarray(format_np_output(heatmap))

        #heatmap_on_image = Image.fromarray(format_np_output(heatmap_on_image))

        self.cam_heatmaps = [cam_activation_map, heatmap, heatmap_on_image]

        return self.cam_heatmaps

    def smooth_grad(self, image, target_class, param_n=50, param_sigma_multiplier=4):

        if isinstance(image, PIL.Image.Image):
            #image = image.resize((224, 224), Image.ANTIALIAS)
            tensor_image = torch.tensor(np.array(image)).unsqueeze(0).permute(0, 3, 1, 2)

        if isinstance(image, np.ndarray):
            tensor_image = torch.tensor(image).unsqueeze(0).permute(0, 3, 1, 2)

        tensor_image = Variable(tensor_image.float(), requires_grad=True)

        vbp = VanillaBackprop(self.model)
        gbp = GuidedBackprop(self.model)

        vanilla_smooth_grad = generate_smooth_grad(vbp, tensor_image, target_class, param_n, param_sigma_multiplier)
        guided_grad = gbp.generate_gradients(tensor_image, target_class)

        guided_grad = guided_grad - guided_grad.min()
        guided_grad /= guided_grad.max()

        vanilla_smooth_grad = Image.fromarray(format_np_output(vanilla_smooth_grad.squeeze()))
        guided_smooth_grad = Image.fromarray(format_np_output(guided_grad.squeeze()))

        self.grads = [vanilla_smooth_grad, guided_smooth_grad]

        return self.grads

    def cnn_vis_layers(self, target_layer, target_position, epochs=300):

        layer_vis = CNNLayerVisualization(self.model.features, target_layer, target_position)

        output = layer_vis.visualise_layer_with_hooks(epochs=epochs)
        output = Image.fromarray(output)

        return output

    def visualization(self, image, target_layer, target_class):

        self.gradcam(image, target_layer, target_class)
        self.smooth_grad(image, target_class)

        fig = plt.figure(figsize=(15, 15), dpi=150)
        ax1 = plt.subplot2grid((4, 4), (0, 0), colspan=2, rowspan=2)
        ax1.axis('off')
        ax1.set_title('Original image')
        ax1.imshow(image)

        ax2 = plt.subplot2grid((4, 4), (0, 2), colspan=1, rowspan=1)
        ax2.axis('off')
        ax2.set_title('GradCam')
        ax2.imshow(self.cam_heatmaps[1])

        ax3 = plt.subplot2grid((4, 4), (0, 3), colspan=1, rowspan=1)
        ax3.axis('off')
        ax3.set_title('GradCam + image')
        ax3.imshow(self.cam_heatmaps[2])

        ax4 = plt.subplot2grid((4, 4), (1, 2), colspan=1, rowspan=1)
        ax4.axis('off')
        ax4.set_title('Vanilla gradient (high contrast)')
        ax4.imshow(self.grads[0])

        ax5 = plt.subplot2grid((4, 4), (1, 3), colspan=1, rowspan=1)
        ax5.axis('off')
        ax5.set_title('Guided gradient')
        ax5.imshow(self.grads[1])

        plt.show()

if __name__ == '__main__':

    cat = Image.open('cute.jpg')
    cat = cat.resize((224, 224), Image.ANTIALIAS)

    prep_image = torch.Tensor(np.array(cat)).unsqueeze(0).permute(0, 3, 1, 2)

    pretrained_model = alexnet(pretrained=True)
    interp = VisualInterpretator(pretrained_model)

    #interp.gradcam(cat, target_layer=11, target_class=16)[0].show()
    #interp.smooth_grad(cat, target_class=4)[0].show()
    interp.cnn_vis_layers(5, 5).show()

    interp.visualization(cat, target_layer=6, target_class=281)
