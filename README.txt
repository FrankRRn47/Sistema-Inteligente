
# Sistema Inteligente: Reconocimiento de Emociones

Este sistema integra un backend profesional en Flask (Python) y un frontend moderno en React (HTML/CSS/JS), junto con un modelo de inteligencia artificial para el reconocimiento de emociones faciales y análisis de texto.

## Frontend (React + HTML/CSS/JS)
Interfaz responsiva y moderna que permite:
- Registro y autenticación de usuarios
- Análisis de emociones en imágenes, videos y texto
- Visualización de resultados y métricas en dashboards interactivos
- Integración segura con el backend mediante API REST y JWT

## Backend (Flask + MySQL + JWT)
Servicios robustos para:
- Gestión de usuarios y autenticación
- Procesamiento y análisis de imágenes, videos y texto
- Almacenamiento seguro de resultados y archivos multimedia
- Exposición de endpoints REST para integración con el frontend

### Endpoints principales
**Autenticación:**
- POST /register
- POST /api/register
- POST /login
- POST /api/login

**Perfil de usuario:**
- GET /profile
- PUT /profile

**Media (imágenes, videos, webcam):**
- GET /media/model-metadata
- POST /analyze-image
- POST /analyze-video
- POST /analyze-webcam
- POST /media/live-session/start
- POST /media/live-session/stop
- POST /analyze-webcam-frame
- GET /media/records
- GET /media/files/<path:relative_path>

## Especificaciones del modelo de IA (tracked)
- El modelo principal es una CNN entrenada sobre el dataset FER2013 (Kaggle), con 35,887 imágenes de 48x48 píxeles.
- Las clases de emociones reconocidas son: angry, disgust, fear, happy, neutral, sad, surprise.
- El archivo `model_weights.h5` contiene los pesos entrenados del modelo.
- El sistema permite entrenamiento y evaluación mediante los scripts en `tracked_train_files`.
- Los resultados y métricas se almacenan en la carpeta `plots`.
- El sistema soporta ejecución en GPU (recomendado) y CPU.

## Instalación y ejecución

### Backend
1. Clona el repositorio y entra a la carpeta `backend`.
2. Crea y activa un entorno virtual:
	```bash
	python -m venv .venv
	.venv\Scripts\activate  # Windows
	source .venv/bin/activate  # Linux/Mac
	```
3. Instala dependencias:
	```bash
	pip install -r requirements.txt
	```
4. Configura las variables de entorno en `.env`.
5. Inicializa la base de datos y migraciones:
	```bash
	flask db init
	flask db migrate -m "Initial tables"
	flask db upgrade
	```
6. Ejecuta el backend:
	```bash
	python app.py
	```

### Frontend
1. Entra a la carpeta `frontend`.
2. Copia `.env.example` a `.env` y ajusta la variable `REACT_APP_API_BASE_URL`.
3. Instala dependencias:
	```bash
	npm install
	```
4. Ejecuta la aplicación:
	```bash
	npm start
	```

### Modelo de IA (tracked)
- Para ejecutar el reconocimiento de emociones, asegúrate de tener los archivos de pesos y recursos en la carpeta `tracked`.
- Para entrenamiento, descarga el dataset FER2013 y sigue las instrucciones en los scripts de `tracked_train_files`.
- Puedes usar el entorno Anaconda y el archivo `tf-gpu.yaml` para instalar todas las dependencias necesarias.


***This setup assumes Python is installed and has been added as a PATH to the System Environment Variables (SEV)

===========================
Project Directory Structure
===========================
* tracked		
	* "model_weights.h5"
	===================================
	Emotion Classes for captured images
	===================================
	* emotion_class
		* angry
	* emotion_class
		* disgust
	* emotion_class
		* fear
	* emotion_class
		* happy
	* emotion_class
		* neutral
	* emotion_class
		* sad
	* emotion_class
		* surprise
	* session_stream
		* session_{timestamp}.mp4

* track_train_files
	* DataGenerator 		
		* archive
			* images
	* CNNModel		
		* "model_weights.h5
	* ModelEvaluator 		
		* "conf_matrix.png
		* "conf_matrix_test.png

=============================
QUICK SETUP & RUNNING TrackEd
=============================
For a quick setup that involves minimal installation, users are advised to install the Anaconda3 for TensorFlow environment. This allows the user to simply import the tf-gpu.yaml file which contains all the project dependencies directly into the environment. This will allow the packages to run without any further installation.

====================
Run within Anaconda3
====================
To run TrackEd within Anaconda3 environment, open 'tracked' folder and run the TrackEd.py file. This will run using the device webcam, giving the option to 'Play' or 'Quit' - Application will only run when user clicks the Play button - click the Play button again to stop the program. Quit exits the application.

If user prefers a different IDE, please follow the **Installation Guide** below.

===================
Run on Command Line
===================
To run TrackEd through CMD - if all package requirements are installed and set to active PATHS on the system, open command line (CMD) > navigate to the project folder > type

	python TrackEd.py

If set up correctly, this will start the application as intended.

If using Anaconda3, activate the environment first > open CMD > type

conda activate <env name (tf-gpu if importing preset env)>

Once active type >

	python TrackEd.py

For instructions on how to RUN a Python file through Command Prompt (CMD) and how to SET Python to the SEV, please see: https://www.wikihow.com/Use-Windows-Command-Prompt-to-Run-a-Python-File

======================
TRAIN AND TEST TrackEd
======================

To train, first the data needs to be imported.

The original dataset used in this project is the Oheix FER2013 dataset, which contains 35,887 grayscale images of size 48x48 pixels.
The dataset is split into three sets: training, validation, and test sets. You can download the dataset from:

https://www.kaggle.com/datasets/jonathanoheix/face-expression-recognition-dataset

This particular dataset is split into Train and Validation folders - this needs to be set to Train and Test, with the Train folder using an 80:20 Train-Validation split, with the directory as below:

* tracked_train_files
	* archive	
		* 1.train
		* 2.validation
		* 3.test

Once data has been imported, simply open the Anaconda3 environment, import the tf-gpu.yaml file, open and run __main.py.

==================
Installation Guide
==================

If user is not using the tf-gpu.yaml file then to run this code the following packages and libraries need to be installed:

NumPy
Matplotlib
TensorFlow (tf.keras API)
OpenCV
Pillow
Scikit-learn
IPython

User can install these packages using pip through CMD. For example:

	pip install numpy matplotlib tensorflow keras scikit-learn ipython

============================
Package Version Requirements
============================

ipython==8.29.0
matplotlib==3.9.2
numpy==2.1.3
opencv-python==4.10.0.84
pillow==11.0.0
scikit-learn==1.5.2
tensorflow==2.18.0

For further info and how to utilise GPU or CPU for Tensorflow:

https://www.tensorflow.org/install/pip

**Please note, if running the training program __main.py, GPU is much faster than CPU if you have the ability.

=============
Project Files
=============

TrackEd.py: this class is for the application - run this to run the project application.

__main.py: this is the training model for the project - run this to train the specified dataset.

CNNModel.py		)
ModelEvaluator.py	>  these classes run in conjuction with __main.py
DataGenerator.py	)

tf-gpu.yaml

emotion_class		- store images for emotion classification
plots			- store plots from test and the best model_weights.h5 file
session_stream		- store the session stream
