# Visual Cryptography Module

import numpy as np
from PIL import Image
import os
import math
from scipy import signal

def psnr(original, contrast):
    mse = np.mean((original - contrast) ** 2)
    if mse == 0:
        return 100
    PIXEL_MAX = 255.0
    PSNR = 20 * math.log10(PIXEL_MAX / math.sqrt(mse))
    return PSNR

def normxcorr2D(image, template):
    """
    Normalized cross-correlation for 2D images
    """
    t = np.asarray(template, dtype=np.float64)
    t = t - np.mean(t)
    norm = math.sqrt(np.sum(np.square(t)))
    if norm == 0:
        raise ValueError("Norm of the input is 0")
    t = t / norm

    sum_filter = np.ones(np.shape(t))

    a = np.asarray(image, dtype=np.float64)
    aa = np.square(a)

    a_sum = signal.correlate(a, sum_filter, 'same')
    aa_sum = signal.correlate(aa, sum_filter, 'same')

    numer = signal.correlate(a, t, 'same')
    denom = np.sqrt(aa_sum - np.square(a_sum)/np.size(t))

    tol = np.sqrt(np.finfo(denom.dtype).eps)
    nxcorr = np.where(denom < tol, 0, numer/denom)

    nxcorr = np.where(np.abs(nxcorr-1.) > np.sqrt(np.finfo(nxcorr.dtype).eps), nxcorr, 0)

    return np.mean(nxcorr)

def encrypt(input_image, share_size):
    """Encrypt an image into multiple shares using XOR operation"""
    image = np.asarray(input_image)
    (row, column, depth) = image.shape
    shares = np.random.randint(0, 256, size=(row, column, depth, share_size))
    shares[:,:,:,-1] = image.copy()
    for i in range(share_size-1):
        shares[:,:,:,-1] = shares[:,:,:,-1] ^ shares[:,:,:,i]

    return shares, image

def decrypt(shares):
    """Decrypt shares back to original image"""
    (row, column, depth, share_size) = shares.shape
    shares_image = shares.copy()
    for i in range(share_size-1):
        shares_image[:,:,:,-1] = shares_image[:,:,:,-1] ^ shares_image[:,:,:,i]

    final_output = shares_image[:,:,:,share_size-1]
    output_image = Image.fromarray(final_output.astype(np.uint8))
    return output_image, final_output