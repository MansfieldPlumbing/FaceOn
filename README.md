# FaceOn Studio

![Windows 10](https://img.shields.io/badge/Windows-10-0078D6?style=for-the-badge&logo=windows)![Windows 11](https://img.shields.io/badge/Windows-11-0078D6?style=for-the-badge&logo=windows)![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python)![C++](https://img.shields.io/badge/C++-00599C?style=for-the-badge&logo=cplusplus)![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

FaceOn Studio is a real-time virtual camera tool that lets you experiment with face-swapping. You can paint on a source face to create a unique digital avatar and then show the result in other apps that use a webcam, like OBS, Zoom, Discord, or Google Meet.

This is an **experimental and creative tool**, so your results may vary. Think of it as a fun collaboration with an AI. The creative possibilities that come from working with a neural network can be surprising and endless.

It's powered by a deep learning core and the **[VirtuaCam](https://github.com/MansfieldPlumbing/VirtuaCam)** virtual camera, which helps to transform your digital presence.

## A Creative Collaboration

The core of FaceOn Studio uses the `inswapper` deep learning model, which was trained on many real faces. It tries to make your drawings look more photorealistic. This creates an interesting and creative interaction between you and the AI:

*   You could draw cartoon glasses on a picture of Abraham Lincoln, and the AI might render them as realistic-looking glasses on your face in real-time.
*   You can try painting a new hairline, adding digital makeup, or drawing a scar, and the model will try to blend it with your features.

This can be a powerful way to tweak and create avatars, but it helps to see it as a creative partnership. The AI will interpret your work, and sometimes the best results come from these unexpected moments.

<p align="center">
  <img src="https://github.com/user-attachments/assets/bcfbad9b-c0b3-47a5-9964-82fa112efd8d" alt="FaceOn Studio Demo" width="800"/>
</p>

## Features

*   **Real-Time, GPU-Accelerated Swapping:** Uses ONNX Runtime with a DirectML backend for face swapping that should run smoothly on modern GPUs (NVIDIA, AMD, Intel).
*   **AI-Interpreted Painting:** A creative process where you guide an AI. The model tries to interpret your paintings to create a blended result.
*   **Paint Tools:** An interface for modifying your source face. Features include:
    *   Adjustable brush size, opacity, hardness, and step.
    *   A color picker and eyedropper tool.
    *   Symbol stamping for creative effects.
    *   Undo/redo history.
*   **Virtual Camera Broadcasting:** Integration with the **[VirtuaCam](https://github.com/MansfieldPlumbing/VirtuaCam)** driver creates a new webcam on your system, letting you send your modified video to other applications.
*   **Create & Save Avatars:** When you're happy with a look, you can save the face embedding as a `.safetensors` file. This lets you load the avatar again later.
*   **Fine-Grained Controls:** The External Preview window has advanced sliders to help perfect the blend. You can adjust the ROI, feathering, mask expansion, and the position/scale for a better result.

## How It Works

FaceOn Studio uses a hybrid approach for its real-time performance and system integration:

1.  **The Python Core:** The main application is built in Python with **Tkinter** for the UI. It uses **OpenCV** for the webcam feed and **ONNX Runtime** for the deep learning models (`det_10g`, `w600k_r50`, and `inswapper_128`).
2.  **The C++ Virtual Camera:** The **[VirtuaCam](https://github.com/MansfieldPlumbing/VirtuaCam)** driver is written in C++. It registers a new software camera with Windows so other applications can see it.
3.  **The `directport` Bridge:** A communication bridge sends the processed video frames from the Python application to a shared memory texture, which the C++ driver reads from. This is designed to reduce latency.

## Getting Started on Windows

There are two options for getting started. Both include the necessary models and libraries.

**Prerequisites:**
*   Windows 10 or Windows 11 (Build 22000 or higher)
*   *   A GPU with DirectX 12 support (NVIDIA, AMD, or Intel)
*   A webcam

---

### Option 1: Easy Installation

This method uses a standard installer and creates shortcuts. It installs to your user account and does not need administrator privileges.

1.  Go to the [**Latest Release**](https://github.com/MansfieldPlumbing/FaceOn/releases/latest) page.
2.  Download the `FaceOn-Studio-Setup.exe` file.
3.  Run the installer.
4.  Launch **FaceOn Studio** from the desktop or Start Menu.

---

### Option 2: Portable (ZIP)

This is for users who prefer not to install software.

1.  Go to the [**Latest Release**](https://github.com/MansfieldPlumbing/FaceOn/releases/latest) page.
2.  Download the `FaceOn-Studio.zip` file.
3.  Extract the ZIP file to a folder.
4.  Run `FaceOn Studio.exe` from that folder.

## Basic Usage

1.  Launch **FaceOn Studio**.
2.  Click the **📂 (Folder)** icon to load an image with a face. This will be the face you swap onto your webcam.
3.  Use the paint tools to customize the image.
4.  (Optional) Click the **💾 (Save)** icon to save your creation as a `.safetensors` avatar in the `embeddings` folder.
5.  Open your streaming or video-conferencing app (OBS, Zoom, Discord, etc.).
6.  In the other application's settings, change the camera to **"VirtuaCam"**.
7.  Your face-swapped video should now be broadcasting.

## For Developers (Linux & macOS)

The pre-built executables are for Windows because of the custom virtual camera. Users on other platforms can try building and running the core Python application from the source code, but the virtual camera part won't be available.

You will need:
*   A C++ compiler and CMake to build the `directport` library.
*   Python 3.10+
*   The Python packages listed in `requirements.txt`.
*   A virtual camera solution for your OS (like v4l2loopback on Linux).

## Technology Stack

*   **Core Logic:** Python
*   **GUI:** Tkinter
*   **AI/ML:** ONNX Runtime with DirectML
*   **Virtual Camera:** C++, Windows Media Foundation, COM
*   **Image Processing:** OpenCV, Pillow
*   **Packaging:** PyInstaller, Inno Setup
