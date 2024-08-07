import cv2
import os
import threading
import csv
from collections import Counter

import torch
from torchvision import transforms
from PIL import Image
from night_enhancer.data_loader import DarkenerDataset
from torchvision.transforms.functional import InterpolationMode

import matplotlib.pyplot as plt
import numpy as np
import random

###############################################################################################################################

# Esta función recibe como entrada un directorio con videos y obtiene los frames de cada uno de esos videos,
# Lo guarda en un directorio con el nombre del video, los redimensiona a 480p
# Además, solamente guarda un frame por segundo para alivianar el proceso.


def process_video(video_path, output_directory):
    video_name = os.path.basename(video_path)
    frame_directory = os.path.join(output_directory, video_name[:-4])

    # Validación para evitar procesar si ya fue procesado previamente
    if os.path.exists(frame_directory):
        return

    if not os.path.exists(frame_directory):
        os.makedirs(frame_directory)

    print(f"Processing {video_name}")
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)  # Obtener el número de FPS del video
    frame_count = 0
    saved_frame_count = 0  # Contador para los frames guardados

    interval = int(fps * 0.5)  # Calcular el número de frames que equivalen a 2 segundos

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Guardar un frame cada intervalo calculado (cada 2 segundos)
        if frame_count % interval == 0:
            frame = cv2.resize(frame, (852, 480))  # Redimensionar el frame a 480p
            frame_file = os.path.join(frame_directory, f"{saved_frame_count:09d}.png")
            cv2.imwrite(frame_file, frame)
            saved_frame_count += 1

        frame_count += 1

    cap.release()
    print(f"Frames extracted for {video_name}: {saved_frame_count} frames")


def video_to_frames(video_directory, output_directory):
    print(f"Processing {video_directory} directory.")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    threads = []
    for video_name in os.listdir(video_directory):
        if video_name.lower().endswith(".mov") or video_name.lower().endswith(".mp4"):
            video_path = os.path.join(video_directory, video_name)
            t = threading.Thread(
                target=process_video, args=(video_path, output_directory)
            )
            t.start()
            threads.append(t)

    # Esperar a que todos los hilos terminen
    for t in threads:
        t.join()


def convert_videos_dir_to_frame():
    # Asegúrate de ajustar las rutas de video_directory y output_directory según sea necesario
    output_directory = "datasets\Results_datasets\\tagger\\frames"

    video_directory = "datasets\Results_datasets\\tagger"
    video_to_frames(video_directory, output_directory)


"""
    video_directory = "E:\DashCam_videos\\uncommon_rides"
    video_to_frames(video_directory, output_directory)

    video_directory = "E:\DashCam_videos\\rest"
    video_to_frames(video_directory, output_directory)
"""

###############################################################################################################################


def create_csv_from_directory(base_dir, output_csv):
    """
    Recorre todos los subdirectorios en base_dir, lista los frames y crea un CSV.

    :param base_dir: Directorio base con subdirectorios que contienen imágenes.
    :param output_csv: Path del archivo CSV de salida.
    """
    header = ["Path", "noche", "soleado", "nublado", "lluvia", "neblina", "sombras"]

    with open(output_csv, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)  # Escribir el encabezado en el CSV

        for root, dirs, files in os.walk(base_dir):
            for file in files:
                # Asumiendo que todos los archivos en los directorios son imágenes relevantes
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    # Construir el path relativo para cada imagen
                    rel_path = os.path.relpath(os.path.join(root, file), start=base_dir)
                    # Inicializar todas las condiciones ambientales en 0
                    row = [rel_path] + [""] * (len(header) - 1)
                    writer.writerow(row)


def create_csv():
    # Reemplaza 'directorioA' con tu path relativo o absoluto al directorio base
    base_dir = "datasets\\Results_datasets\\tagger\\frames"
    output_csv = "datasets\\Results_datasets\\tagger\\frames\\frames_labels.csv"

    create_csv_from_directory(base_dir, output_csv)


###############################################################################################################################


def csv_mainteinence_with_directory(base_dir, csv_path):
    """
    Actualiza el archivo CSV con los frames en base_dir:
    1. Agrega nuevos frames al final del CSV.
    2. Elimina filas del CSV si la imagen correspondiente no existe.

    :param base_dir: Directorio base con subdirectorios que contienen imágenes.
    :param csv_path: Path del archivo CSV a actualizar.
    """
    existing_images = set()
    new_rows = []
    header = ["Path", "noche", "soleado", "nublado", "lluvia", "neblina", "sombras"]

    # Paso 1: Recolectar todos los paths de imagen existentes
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                rel_path = os.path.relpath(os.path.join(root, file), start=base_dir)
                existing_images.add(rel_path)

    # Paso 2: Leer el CSV existente y mantener solo las filas con imágenes existentes
    try:
        with open(csv_path, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["Path"] in existing_images:
                    new_rows.append(row)
                    existing_images.remove(
                        row["Path"]
                    )  # Eliminar para no agregarlo nuevamente después
    except FileNotFoundError:
        print(f"No se encontró el archivo CSV: {csv_path}. Creando uno nuevo.")

    # Paso 3: Agregar nuevas imágenes al CSV
    for image_path in sorted(existing_images):  # Ordenar para mantener consistencia
        new_row = dict.fromkeys(header, "")  # Inicializar todas las columnas en blanco
        new_row["Path"] = image_path
        new_rows.append(new_row)

    # Paso 4: Escribir de nuevo al archivo CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
        writer.writerows(new_rows)


def csv_mainteinence():
    base_dir = "datasets\\Results_datasets\\tagger\\frames"
    csv_path = "datasets\\Results_datasets\\tagger\\frames\\frames_labels.csv"
    csv_mainteinence_with_directory(base_dir, csv_path)


###############################################################################################################################


def count_rows_with_data(csv_path):
    """
    Cuenta el número de filas en el archivo CSV que tienen datos en los campos de tags.

    :param csv_path: Ruta al archivo CSV.
    :return: Número de filas con datos.
    """
    count = 0
    with open(csv_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Saltar el encabezado
        for row in reader:
            # Verificar si alguna de las columnas de tags tiene datos
            if any(tag for tag in row[1:] if tag.strip()):
                count += 1

    return count


def print_data_rows_counter():
    csv_path = "datasets\\Results_datasets\\tagger\\frames\\frames_labels.csv"  # Reemplaza esto con la ruta real a tu archivo CSV
    num_rows_with_data = count_rows_with_data(csv_path)
    print(f"Número de filas con datos: {num_rows_with_data}")


###############################################################################################################################


def update_csv_tags(csv_path, image_prefix, tags):
    """
    Actualiza los tags de las imágenes en un archivo CSV.

    :param csv_path: Ruta al archivo CSV.
    :param image_prefix: Prefijo del path de las imágenes a actualizar.
    :param tags: Diccionario con los nombres de los tags como claves y booleanos como valores.
    """
    updated_rows = []
    with open(csv_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Path"].startswith(image_prefix):
                for tag, value in tags.items():
                    row[tag] = "1" if value else "0"
            updated_rows.append(row)

    # Escribir los datos actualizados de nuevo al archivo CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = updated_rows[
            0
        ].keys()  # Tomar los nombres de las columnas del primer row actualizado
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)


def update_specific_csv_tags(csv_path, image_prefix, frames, tags):
    """
    Actualiza los tags de imágenes específicas en un archivo CSV.

    :param csv_path: Ruta al archivo CSV.
    :param image_prefix: Prefijo del path de las imágenes a actualizar.
    :param frames: Lista de números de frame específicos para actualizar.
    :param tags: Diccionario con los nombres de los tags como claves y booleanos como valores.
    """
    updated_rows = []
    with open(csv_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Extraer el número de frame del nombre del archivo
            frame_number = int(row["Path"].split("\\")[-1].split(".")[0])
            # Verificar si el path de la imagen coincide con el prefijo y si el frame está en la lista
            if row["Path"].startswith(image_prefix) and frame_number in frames:
                for tag, value in tags.items():
                    row[tag] = "1" if value else "0"
            updated_rows.append(row)

    # Escribir los datos actualizados de nuevo al archivo CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = updated_rows[
            0
        ].keys()  # Tomar los nombres de las columnas del primer row actualizado
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)


def update_csv():
    csv_mainteinence()
    # Ejemplo de uso
    csv_path = "datasets\\Results_datasets\\tagger\\frames\\frames_labels.csv"  # Asegúrate de reemplazar 'tu_archivo.csv' con la ruta real de tu archivo CSV
    image_prefix = "rain"  # Prefijo del path de las imágenes a actualizar
    frames = []
    tags = {
        "noche": False,
        "soleado": False,
        "nublado": False,
        "lluvia": True,
        "neblina": False,
        "sombras": False,
    }
    if frames == []:
        update_csv_tags(csv_path, image_prefix, tags)
    else:
        update_specific_csv_tags(csv_path, image_prefix, frames, tags)

    print_data_rows_counter()
    print_label_counts()


###############################################################################################################################


def count_label_combinations(csv_path):
    """
    Cuenta las combinaciones únicas de etiquetas en el archivo CSV.

    :param csv_path: Ruta al archivo CSV.
    """
    combinations = Counter()
    with open(csv_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Construir una lista de etiquetas activas para esta fila
            labels = [
                label
                for label, value in row.items()
                if value.strip() == "1"
                and label
                != "Path"  # Asegúrate de que los valores se comparen correctamente como strings
            ]

            # Añadir la combinación de etiquetas al contador
            if labels:
                combination = ", ".join(sorted(labels))
                combinations[combination] += 1

    # Imprimir el conteo de cada combinación de etiquetas
    total = 0
    for combination, count in combinations.items():
        total += count
        print(f"Total {combination}: {count}")
    print(total)


def print_label_counts():
    csv_path = "datasets\\Results_datasets\\tagger\\frames\\frames_labels.csv"  # Reemplaza esto con la ruta real a tu archivo CSV
    count_label_combinations(csv_path)


###############################################################################################################################


def find_and_remove_empty_directories_aux(root_dir):
    """
    Busca y imprime los nombres de los directorios vacíos dentro de root_dir.
    """
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Un directorio se considera vacío si no contiene subdirectorios ni archivos
        if not dirnames and not filenames:
            print(f"Directorio vacío encontrado: {dirpath}")
            os.rmdir(dirpath)


def find_and_remove_empty_directories():
    root_dir = "custom_dataset"
    find_and_remove_empty_directories_aux(root_dir)


###############################################################################################################################


def rename_directories(root_dir):
    """
    Renombra los directorios bajo root_dir para eliminar tildes y cambiar 'ñ' por 'n'.
    """
    for dirpath, dirnames, _ in os.walk(root_dir, topdown=False):
        for dirname in dirnames:
            print(dirname)
            new_dirname = dirname.translate(
                str.maketrans("áéíóúñÁÉÍÓÚÑ", "aeiounAEIOUN")
            )
            if dirname != new_dirname:
                original_path = os.path.join(dirpath, dirname)
                new_path = os.path.join(dirpath, new_dirname)
                print(f"Renombrando '{original_path}' a '{new_path}'")
                os.rename(original_path, new_path)


def remove_accents_and_rename_directories():

    root_dir = "E:\DashCam_videos\\common_rides"
    rename_directories(root_dir)

    root_dir = "E:\DashCam_videos\\uncommon_rides"
    rename_directories(root_dir)

    root_dir = "E:\DashCam_videos\\rest"
    rename_directories(root_dir)


#########################################################################################################################################


def cleaning_wrong_directories_pipeline():
    find_and_remove_empty_directories()
    remove_accents_and_rename_directories()
    convert_videos_dir_to_frame()


###############################################################################################################################


def calculate_mean_std():
    # Define tus transformaciones sin la normalización
    transform = transforms.Compose(
        [
            transforms.Resize(232, interpolation=InterpolationMode.BILINEAR),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
        ]
    )

    # Carga del dataset
    dataset = DarkenerDataset(
        csv_file=".\\frames_labels.csv",
        root_dir=".\\datasets\\custom_dataset\\Processed",
        transform=transform,
    )

    loader = torch.utils.data.DataLoader(
        dataset, batch_size=64, shuffle=False, num_workers=4
    )

    mean = 0.0
    std = 0.0
    nb_samples = 0.0
    for bright, dark in loader:
        bright_flat = bright.view(bright.size(0), bright.size(1), -1)
        dark_flat = dark.view(dark.size(0), dark.size(1), -1)

        mean += bright_flat.mean(2).sum(0) + dark_flat.mean(2).sum(0)
        std += bright_flat.std(2).sum(0) + dark_flat.std(2).sum(0)
        nb_samples += bright_flat.size(0) + dark_flat.size(0)

    mean /= nb_samples
    std /= nb_samples

    print(f"Mean: {mean}")
    print(f"Std: {std}")


###############################################################################################################################


def process_and_save_images():

    input_dir = "datasets\\custom_dataset\\Processed"
    output_dir = "datasets\\custom_dataset\\Processed_cropped"
    # Definir las transformaciones
    transformations = transforms.Compose(
        [
            transforms.Resize(232, interpolation=Image.BILINEAR),
            transforms.CenterCrop(224),
        ]
    )

    # Crear el directorio de salida si no existe
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Recorrer el directorio de entrada
    for subdir, dirs, files in os.walk(input_dir):
        for file in files:
            # Ignorar archivos que no sean imágenes
            if not file.lower().endswith((".png", ".jpg", ".jpeg")):
                continue

            # Construir la ruta completa del archivo
            file_path = os.path.join(subdir, file)

            # Cargar la imagen
            with Image.open(file_path) as img:
                # Aplicar las transformaciones
                transformed_img = transformations(img)

            # Construir la ruta del subdirectorio en el directorio de salida
            relative_path = os.path.relpath(subdir, input_dir)
            save_subdir = os.path.join(output_dir, relative_path)

            # Crear el subdirectorio si no existe
            if not os.path.exists(save_subdir):
                os.makedirs(save_subdir)

            # Guardar la imagen transformada
            save_path = os.path.join(save_subdir, file)
            transformed_img.save(save_path)

            # print(f"Image saved to {save_path}")


###############################################################################################################################


def save_feature_map_combined(feature_map, filepath):
    # Asegúrate de que el directorio existe
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Convierte el tensor a un numpy array
    feature_map_np = feature_map.detach().cpu().numpy()

    # Promedia los canales
    combined_feature_map = np.mean(feature_map_np[0], axis=0)

    # Normaliza la característica para visualización
    combined_feature_map = (combined_feature_map - combined_feature_map.min()) / (
        combined_feature_map.max() - combined_feature_map.min()
    )

    # Convierte a RGB si es una imagen de una sola canal
    if combined_feature_map.ndim == 2:
        combined_feature_map = np.stack([combined_feature_map] * 3, axis=-1)

    # Guarda la imagen combinada
    plt.imshow(combined_feature_map, cmap="viridis")
    plt.axis("off")
    plt.savefig(filepath, bbox_inches="tight", pad_inches=0)
    plt.close()


###############################################################################################################################


def save_random_feature_map(tensor, filepath):
    # Asegúrate de que el directorio existe
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Convierte el tensor a un numpy array
    tensor_np = tensor.detach().cpu().numpy()

    # Selecciona un canal aleatorio
    num_channels = tensor_np.shape[1]
    random_channel = random.randint(0, num_channels - 1)

    # Obtén el feature map del canal aleatorio
    feature_map = tensor_np[0, random_channel, :, :]

    # Normaliza la característica para visualización
    feature_map = (feature_map - feature_map.min()) / (
        feature_map.max() - feature_map.min()
    )

    # Guarda la imagen
    plt.imshow(feature_map, cmap="viridis")
    plt.axis("off")
    plt.savefig(filepath, bbox_inches="tight", pad_inches=0)
    plt.close()


###############################################################################################################################


def main():

    # cleaning_wrong_directories_pipeline()
    # create_csv()
    # update_csv()
    # csv_mainteinence()
    # find_and_remove_empty_directories()
    #  remove_accents_and_rename_directories()
    # convert_videos_dir_to_frame()
    print_data_rows_counter()
    print_label_counts()
    # calculate_mean_std()
    # process_and_save_images()


if __name__ == "__main__":
    main()
