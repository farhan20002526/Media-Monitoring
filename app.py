import torch
from read import text_recognizer
from model import Model
from utils import CTCLabelConverter
from ultralytics import YOLO
from PIL import Image, ImageDraw
import os
import mysql.connector
import time
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Database setup
try:
    # Connect to MySQL
    db_connection = mysql.connector.connect(
        host='localhost',        # Replace with your MySQL host
        user='root',             # Replace with your MySQL username
        password='1234',         # Replace with your MySQL password
        database='ocr_results'   # Replace with your MySQL database name
    )
    logging.info("Connected to MySQL database")
    
    # Create cursor object
    db_cursor = db_connection.cursor()

    # Create table for storing OCR results if it doesn't exist
    db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocr_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            file_name VARCHAR(255),
            extracted_text TEXT
        )
    ''')
    db_connection.commit()
    logging.info("Table 'ocr_results' created if not exists")

except mysql.connector.Error as err:
    logging.error(f"Error connecting to MySQL: {err}")
    exit(1)

# Load UrduGlyphs
with open("UrduGlyphs.txt", "r", encoding="utf-8") as file:
    content = file.read().replace('\n', '') + " "

# Model configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
converter = CTCLabelConverter(content)
recognition_model = Model(num_class=len(converter.character), device=device)
recognition_model = recognition_model.to(device)
recognition_model.load_state_dict(torch.load("best_norm_ED.pth", map_location=device))
recognition_model.eval()

detection_model = YOLO("yolov8m_UrduDoc.pt")

# Path to the folder containing images
folder_path = r"D:\Proxima\works\youtube downloader\youtube-stream-downloader\downloads\frames"

# Path to the folder where processed images will be moved
processed_folder = r"D:\Proxima\works\youtube downloader\youtube-stream-downloader\downloads\processed_frames"

# Create the processed folder if it doesn't exist
os.makedirs(processed_folder, exist_ok=True)

# Set to keep track of processed files
processed_files = set()

def process_image(file_path):
    try:
        input_image = Image.open(file_path).convert("RGB")
        
        # Line Detection
        detection_results = detection_model.predict(source=input_image, conf=0.15, imgsz=1280, save=False, device=device)
        bounding_boxes = detection_results[0].boxes.xyxy.cpu().numpy().tolist()
        bounding_boxes.sort(key=lambda x: x[1])
        
        # Draw the bounding boxes (optional)
        draw = ImageDraw.Draw(input_image)
        for box in bounding_boxes:
            from numpy import random
            draw.rectangle(box, outline=tuple(random.randint(0, 255, 3)), width=5)
        
        # Crop the detected lines
        cropped_images = [input_image.crop(box) for box in bounding_boxes]
        
        # Recognize the text
        texts = [text_recognizer(img, recognition_model, converter, device) for img in cropped_images]
        
        # Join the text
        extracted_text = "\n".join(texts)
        
        return extracted_text
    except Exception as e:
        logging.error(f"Error processing image {file_path}: {e}")
        return None

# Main processing loop
while True:
    # Process all images in the folder and save results to the database
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".png") or file_name.endswith(".jpg"):
            file_path = os.path.join(folder_path, file_name)
            
            # Check if file has already been processed
            if file_name in processed_files:
                continue
            
            extracted_text = process_image(file_path)
            
            if extracted_text:
                # Insert OCR results into the database
                try:
                    db_cursor.execute('''
                        INSERT INTO ocr_results (file_name, extracted_text)
                        VALUES (%s, %s)
                    ''', (file_name, extracted_text))
                    db_connection.commit()
                    logging.info(f"Inserted OCR results for {file_name}")
                    
                    # Move the processed image to the processed folder
                    try:
                        shutil.move(file_path, os.path.join(processed_folder, file_name))
                        processed_files.add(file_name)  # Add to processed set after successful processing
                    except Exception as e:
                        logging.error(f"Error moving file {file_path} to {processed_folder}: {e}")
                
                except mysql.connector.Error as err:
                    logging.error(f"Error inserting OCR results into MySQL: {err}")
                    db_connection.rollback()

    # Wait for 5 minutes before checking for new frames again
    time.sleep(300)  # 300 seconds = 5 minutes

# Close the database connection (This will never execute in an infinite loop scenario)
db_connection.close()
