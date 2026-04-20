#layoutparse for OCR regions and sketch areas

import os
import cv2
import layoutparser as lp
from glob import glob
from PIL import Image

# Load pre-trained models
model_publaynet = lp.Detectron2LayoutModel(
    config_path='lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config',
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
    label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
)

model_detectron2 = lp.Detectron2LayoutModel(
    config_path='lp://HJDataset/mask_rcnn_R_50_FPN_3x/config',
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
    label_map={0: "text", 1: "title", 2: "figure", 3: "list", 4: "table"}
)

image_dirs = [os.path.join("staged_data", d, "images") for d in os.listdir("staged_data") if os.path.isdir(os.path.join("staged_data", d, "images"))]

for image_dir in image_dirs:
    for image_path in glob(os.path.join(image_dir, "*.jpg")):
        filename = os.path.basename(image_path)
        item_id = image_path.split("/")[-3]
        page_number = os.path.splitext(filename)[0]

        image = cv2.imread(image_path)
        image_rgb = image[:, :, ::-1]  # Convert BGR to RGB for layoutparser

        for model_name, model in [("publaynet", model_publaynet), ("detectron2", model_detectron2)]:
            layout = model.detect(image_rgb)

            for i, block in enumerate(layout):
                x_1, y_1, x_2, y_2 = map(int, block.block.coordinates)
                crop = image[y_1:y_2, x_1:x_2]
                crop_filename = f"{item_id}_{page_number}_{i}_{model_name}.jpg"
                crop_path = os.path.join(image_dir, crop_filename)
                cv2.imwrite(crop_path, crop)

            # Optionally save overlay visualization
            draw = lp.draw_box(image_rgb, layout, box_width=3)
            overlay_path = os.path.join(image_dir, f"{item_id}_{page_number}_overlay_{model_name}.jpg")
            cv2.imwrite(overlay_path, draw[:, :, ::-1])  # Convert RGB back to BGR