# Face On
## Real Time Face Studio with Virtual Camera support

Face On is a high-performance, real-time face swapping and management application for Windows. It allows you to swap faces from your image library onto a live webcam feed, or create entirely new personas by blending and morphing between different source faces in real-time.



<img width="495" height="566" alt="image" src="https://github.com/user-attachments/assets/3e57fe43-3223-4f29-859d-437d9471f2cc" />



It's designed as a stable and powerful control panel for anyone who wants to reliably manage and fine-tune their digital appearance for streaming, video calls, or creative projects.
(Recommended: Replace this text with a screenshot or GIF of the application in action. Show the UI and perhaps the live preview window.)
![Face On Interface](LINK_TO_YOUR_SCREENSHOT.png)
## Features

Real-Time Swapping: Instantly swap faces from your source images onto a live webcam feed.

Face Blending: Use a simple slider to seamlessly blend between two selected source faces, creating a unique hybrid.

Automated Morphing: Activate a continuous, smooth morph between all of the faces in your source library.

EMAP Mode: Don't have source images? Use the built-in "Emap Archetype" face to get started immediately.

Fine-Tuning Control Panel: A full suite of sliders lets you adjust the ROI (Region of Interest) margin, mask feathering, core tightness, 
and affine "nudge" controls (X/Y offset, scale) for a perfect blend.

DirectPort Native Output: Broadcasts its output using DirectPort, ensuring low-latency and seamless integration with virtual camera software like VirtuaCam.

GPU Accelerated: Utilizes ONNX Runtime with the DirectML execution provider for high-performance, hardware-accelerated processing on modern Windows systems.

## A Tale of Two Tools

Face On is one half of a two-part release. It is the stable, control-focused tool designed for reliable performance and fine-tuning.

If you want a control panel to manage, blend, and perfect face swaps, you are in the right place.

Its creative counterpart is PaintShop Studio, an experimental tool that lets you paint a source face in real-time and wear it like a digital mask.

If you want an art canvas for creating surreal and bizarre effects, check out PaintShop Studio.

## Installation

Prerequisites:

Windows 10 or 11

A DirectML-compatible GPU (most modern AMD, NVIDIA, or Intel GPUs)

Python 3.8+

## Instructions:

Clone the repository:

```
git clone https://github.com/your-username/face-on.git
cd face-on
```

Set up a Python virtual environment (recommended):

```
python -m venv venv
.\venv\Scripts\activate
```

Install the required packages:

```
pip install -r requirements.txt
```

Download the Models:
The required ONNX model files are not included in the repository. They must be downloaded from the project's releases page.

a. Go to the Releases Page.
b. Under the "Assets" section of the latest release, download the models.zip file.
c. Create a folder named models in the root of your project directory.
d. Unzip the contents of models.zip directly into the models folder.

Your final folder structure should look like this:

```
face-on/
├── models/
│   ├── det_10g.onnx
│   ├── inswapper_128.onnx
│   └── w600k_r50.onnx
├── faceonmain.py
└── ... (etc.)
```

## How to Use

Add Source Images: Place any face images (e.g., .jpg, .png) you want to use into the /sources folder. The application will automatically find them when it starts.
Run the Application:

```
python faceonmain.py
```

## Control the UI:

Mode Selection: Use the radio buttons on the left to select your desired mode (Swap, Blend, Morph, etc.).

Source Selection: Hover your mouse cursor over the source image thumbnails and use the mouse scroll wheel to cycle through your library. 

In Blend mode, you can select which thumbnail (A or B) is the active scroll target by clicking on it.

Adjust Sliders: Use the sliders in the bottom half of the window to fine-tune the face-swapping parameters in real-time.

View the Live Output: To see the results, you need a DirectPort viewer like VirtuaCam.

Open your virtual camera software (e.g., VirtuaCam Studio).

Add a new "DirectPort Source" layer.

The producer, named TegrityEngine_Output, should appear in the source list. Select it.

You will now see your live, modified webcam feed. You can use this virtual camera in any other application like OBS, Discord, Zoom, etc.

## License

This project is licensed under the MIT License. See the LICENSE file for details.



## PaintShop Studio: A Real-Time FaceSwap Playground

PaintShop Studio is an experimental, real-time face-swapping tool for Windows. Its core feature is a "paint shop" interface that lets you dynamically edit your source face image with a brush, and instantly see the results applied to your own face on a live webcam feed.

It's not a polished "makeup booth." It's a weird, digital Cronenberg machine. If you've ever wanted to paint a new face onto a historical figure and then wear it in a video call, this is for you.

<img width="828" height="1195" alt="Screenshot 2025-09-16 074922" src="https://github.com/user-attachments/assets/6015ab09-a347-4b13-b5c5-5d9173691578" />

## Key Features
Live Source Painting: The main attraction. Load a source face, then paint, smudge, and modify it in real-time. Every brush stroke on the source image is reflected in the live face-swap.

DirectPort Native Output: Designed specifically for the Windows ecosystem. It broadcasts its output via DirectPort, making it instantly compatible with virtual camera software like VirtuaCam. This allows for low-latency use in OBS, Discord, Zoom, or any other application that accepts a webcam input.

GPU Accelerated: Uses ONNX Runtime with the DirectML execution provider for hardware-accelerated performance on modern Windows systems.
Simple & Focused: No complex menus or configuration. Just load an image and start painting.

## The Vibe (Managing Expectations)

I initially thought this could be a neat virtual makeup tool. It is not. The results are often surreal, uncanny, and artistically strange. The strength of this tool lies in its experimental nature. It's for creating bizarre effects, crafting uncanny new personas for a stream, or just exploring the strange side of AI face-swapping.

## Installation
Prerequisites:

Windows 10 or 11

A DirectML-compatible GPU (most modern AMD, NVIDIA, or Intel GPUs)

Python 3.8+

##Instructions:
C
lone the repository:


git clone https://github.com/your-username/paintshop-studio.git
cd paintshop-studio
Set up a Python virtual environment (recommended):

python -m venv venv
.\venv\Scripts\activate
Install the required packages:

pip install -r requirements.txt
Download the Models:
The required ONNX model files are not included in the repository.
a. Go to the Releases Page on this repository.
b. Download the models.zip file from the latest release.
c. Create a models folder in the project's root directory.
d. Unzip the contents of models.zip into this models folder.
How to Use
Run the application:

python paintshopmain.py
(Assuming your main script is paintshopmain.py)
Load a Source Image: Click the "Load Image" button and select an image file containing a face.
Start Painting: Use the sliders to adjust brush size, hardness, and opacity. Click the color swatch to change colors. Paint directly on the main canvas.
View the Live Output: To see the results, you need a DirectPort viewer.
Open your virtual camera software (e.g., VirtuaCam Studio).
Add a new "DirectPort Source" layer.
The producer, named something like PaintShopStudio_[PID], should appear in the list. Select it.
You will now see your webcam feed with the modified source face swapped onto it. This feed can now be used in any other application like OBS or Discord.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
