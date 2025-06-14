import cv2
import numpy as np
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import serial
import time

def load_yolo():
    net = cv2.dnn.readNet(
        r"C:\Users\angel\OneDrive\Desktop\codigos\Semaforos\yolov3.weights",
        r"C:\Users\angel\OneDrive\Desktop\codigos\Semaforos\yolov3.cfg"
    )
    layer_names = net.getLayerNames()
    output_layers_indices = net.getUnconnectedOutLayers()
    output_layers = [layer_names[i - 1] for i in output_layers_indices.flatten()]
    return net, output_layers

def load_coco_names():
    with open(r"C:\Users\angel\OneDrive\Desktop\codigos\Semaforos\coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    return classes

def count_cars_from_image(img, net, output_layers, classes):
    height, width, _ = img.shape
    blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outputs = net.forward(output_layers)

    car_count = 0
    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5 and classes[class_id] == "car":
                car_count += 1
    return car_count

def activate_stoplight(image1_count, image2_count):
    if image1_count > image2_count:
        decision = "Se activa el semáforo 1 (más coches en la cámara 1). El semáforo 2 está apagado."
    elif image2_count > image1_count:
        decision = "Se activa el semáforo 2 (más coches en la cámara 2). El semáforo 1 está apagado."
    else:
        decision = "Ambas cámaras tienen el mismo número de coches. No hay cambios de semáforo."
    return decision

def guardar_decision(decision):
    with open("Decision.txt", "w") as file:
        file.write(decision)

def abrir_archivo_decision():
    if os.path.exists("Decision.txt"):
        os.startfile("Decision.txt")
    else:
        messagebox.showerror("Error", "El archivo Decision.txt no existe.")

# Comunicación con Arduino
try:
    arduino = serial.Serial('COM7', 9600, timeout=1)
    time.sleep(2)
except serial.SerialException:
    arduino = None
    print("No se pudo conectar al Arduino en el puerto COM7.")

def enviar_decision_a_arduino(decision):
    if arduino is None:
        print("Arduino no está conectado, no se envía comando.")
        return

    if "semáforo 1" in decision:
        arduino.write(b'1')
        print("Enviado a Arduino: Semáforo 1 VERDE")
    elif "semáforo 2" in decision:
        arduino.write(b'2')
        print("Enviado a Arduino: Semáforo 2 VERDE")
    else:
        arduino.write(b'0')
        print("Enviado a Arduino: Ambos SEMÁFOROS ROJO o sin cambio")

def main():
    net, output_layers = load_yolo()
    classes = load_coco_names()

    # Rutas de imágenes fijas
    ruta_img1 = r"C:\Users\angel\OneDrive\Desktop\codigos\Semaforos\Imagen1.png"
    ruta_img2 = r"C:\Users\angel\OneDrive\Desktop\codigos\Semaforos\Imagen2.png"

    # Leer las imágenes desde disco
    img1 = cv2.imread(ruta_img1)
    img2 = cv2.imread(ruta_img2)

    if img1 is None or img2 is None:
        print("Error: No se pudieron cargar una o ambas imágenes.")
        return

    root = tk.Tk()
    root.title("Detección de vehículos en imágenes fijas")

    label_img1 = tk.Label(root)
    label_img1.pack()
    label_count1 = tk.Label(root, text="Número de coches en imagen 1: 0")
    label_count1.pack()

    label_img2 = tk.Label(root)
    label_img2.pack()
    label_count2 = tk.Label(root, text="Número de coches en imagen 2: 0")
    label_count2.pack()

    label_decision = tk.Label(root, text="Decisión: ", wraplength=400, justify="center", fg="blue")
    label_decision.pack(pady=10)

    button_abrir = tk.Button(root, text="Abrir archivo Decision.txt", command=abrir_archivo_decision)
    button_abrir.pack()

    # Procesar las imágenes una sola vez (no en bucle)
    car_count1 = count_cars_from_image(img1, net, output_layers, classes)
    car_count2 = count_cars_from_image(img2, net, output_layers, classes)
    decision = activate_stoplight(car_count1, car_count2)

    guardar_decision(decision)
    enviar_decision_a_arduino(decision)

    img1_rgb = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
    img1_pil = Image.fromarray(img1_rgb).resize((300, 200))
    img1_tk = ImageTk.PhotoImage(img1_pil)

    img2_rgb = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)
    img2_pil = Image.fromarray(img2_rgb).resize((300, 200))
    img2_tk = ImageTk.PhotoImage(img2_pil)

    label_img1.config(image=img1_tk)
    label_img1.image = img1_tk
    label_count1.config(text=f"Número de coches en imagen 1: {car_count1}")

    label_img2.config(image=img2_tk)
    label_img2.image = img2_tk
    label_count2.config(text=f"Número de coches en imagen 2: {car_count2}")

    label_decision.config(text=f"Decisión: {decision}")

    def on_closing():
        if arduino is not None:
            arduino.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
