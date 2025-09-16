# Face On
Real Time Face Studio with Virtual Camera support


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
