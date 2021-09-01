from flask import Flask, request, jsonify, redirect
import numpy as np
import onnxruntime

import math
import matplotlib.pyplot as plt
import cv2
import json
import base64

app = Flask(__name__,
            static_url_path='/', 
            static_folder='web')

ort_session = onnxruntime.InferenceSession("efficientnet-lite4-11.onnx")

# load the labels text file
labels = json.load(open("labels_map.txt", "r"))

# set image file dimensions to 224x224 by resizing and cropping image from center
def pre_process_edgetpu(img, dims):
    output_height, output_width, _ = dims
    img = resize_with_aspectratio(img, output_height, output_width, inter_pol=cv2.INTER_LINEAR)
    img = center_crop(img, output_height, output_width)
    img = np.asarray(img, dtype='float32')
    # converts jpg pixel value from [0 - 255] to float array [-1.0 - 1.0]
    img -= [127.0, 127.0, 127.0]
    img /= [128.0, 128.0, 128.0]
    return img

# resize the image with a proportional scale
def resize_with_aspectratio(img, out_height, out_width, scale=87.5, inter_pol=cv2.INTER_LINEAR):
    height, width, _ = img.shape
    new_height = int(100. * out_height / scale)
    new_width = int(100. * out_width / scale)
    if height > width:
        w = new_width
        h = int(new_height * height / width)
    else:
        h = new_height
        w = int(new_width * width / height)
    img = cv2.resize(img, (w, h), interpolation=inter_pol)
    return img

# crop the image around the center based on given height and width
def center_crop(img, out_height, out_width):
    height, width, _ = img.shape
    left = int((width - out_width) / 2)
    right = int((width + out_width) / 2)
    top = int((height - out_height) / 2)
    bottom = int((height + out_height) / 2)
    img = img[top:bottom, left:right]
    return img

@app.route("/", methods=["GET"])
def index():
    return redirect("/index.html")

@app.route("/analyze", methods=["POST"])
def analyze():

    # read the image
    content = request.files.get('0', '').read()

    # build numpy array from uploaded data
    img = cv2.imdecode(np.fromstring(content, np.uint8), cv2.IMREAD_UNCHANGED)

    # pre-process, see https://github.com/onnx/models/tree/master/vision/classification/efficientnet-lite4
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # pre-process the image like mobilenet and resize it to 224x224
    img = pre_process_edgetpu(img, (224, 224, 3))

    # create a batch of 1 (that batch size is buned into the saved_model)
    img_batch = np.expand_dims(img, axis=0)

    # run inference
    results = ort_session.run(["Softmax:0"], {"images:0": img_batch})[0]
    result = reversed(results[0].argsort()[-5:])
    resultStr = ""
    first = True
    for r in result:
        if first: 
            resultStr = labels[str(r)] + " (" + str(results[0][r]) + ")"
            first = False
        else:     
            # TODO use proper JSON as result       
            resultStr =  resultStr + "<br>" + labels[str(r)] + " (" + str(results[0][r]) + ")"
        
        print(r, labels[str(r)], results[0][r])

    return resultStr

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
