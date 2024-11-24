import os
import sqlite3
import cv2
import numpy as np
from nudenet import NudeDetector
from apps import db
from apps.authentication.models import Porn_Data
import hashlib



detector = NudeDetector(model_path=os.path.join(os.getcwd(), "apps", "analyze", "Porn", "640m.onnx"), inference_resolution=640)

def string_to_md5(input_string):
    encoded_string = input_string.encode()
    md5_hash = hashlib.md5(encoded_string)
    return md5_hash.hexdigest()

def porn_behavior(case_id, db_path) :
    if Porn_Data.query.filter_by(case_id = case_id).first() :
        pass
    else :
        user_upload_folder = os.path.dirname(db_path)
        folder_file_list = (os.listdir(user_upload_folder))
        attachments_file = ""
        for i in folder_file_list :
            if ".attachments" in i and "-shm" not in i and "-wal" not in i :
                attachments_file = i
        case_mdfb = os.path.join(os.path.dirname(db_path), "Case.mfdb")
        case_attachments_file = os.path.join(os.path.dirname(db_path), attachments_file)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT hit_id, File_Name FROM Videos WHERE File_Name IS NOT NULL AND Skin_Tone_Percentage >= 10")
        all_data = cursor.fetchall()
        conn.close()
        
        mfdb_conn = sqlite3.connect(case_mdfb)
        cursor = mfdb_conn.cursor()
        hit_fragment_id_datas = []
        for i in all_data :
            cursor.execute(f"SELECT hit_fragment_id FROM hit_fragment WHERE hit_id = {i[0]} AND value = 'image/jpeg'")
            hit_fragment_id_datas.append([cursor.fetchall(), i[1]])
        mfdb_conn.close()

        attachments_conn = sqlite3.connect(case_attachments_file)
        cursor = attachments_conn.cursor()

        real_names = {}
        for i in hit_fragment_id_datas :
            cursor.execute(f"SELECT segment_id FROM segment_map WHERE hit_fragment_id = {i[0][0][0]}")
            hit_fragment_id = cursor.fetchall()[0][0]
            cursor.execute(f"SELECT content FROM segment WHERE segment_id = '{hit_fragment_id}'")
            image_data = (cursor.fetchall())

            output_folder = "Porn"
            if not os.path.exists(os.path.join(user_upload_folder, output_folder)) :
                os.makedirs(os.path.join(user_upload_folder, output_folder))

            replaced_file_name = string_to_md5(i[1])
            real_names[str(replaced_file_name)] = i[1]
            save_image_path = os.path.join(user_upload_folder, output_folder, replaced_file_name + ".jpg")
            with open(save_image_path, 'wb') as f:
                for content in image_data:
                    f.write(content[0])
            img_array = np.fromfile(save_image_path, np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if image is None:
                print("이미지를 로드할 수 없습니다.")
                os.remove(save_image_path)
                continue

            height, width, _ = image.shape
            if height != 514 or width != 1282:
                os.remove(save_image_path)
            else:
                crop_images = crop_image(save_image_path, user_upload_folder)

        crop_image_folders = os.listdir(os.path.join(user_upload_folder, "Crop"))
        for index, value in enumerate(crop_image_folders):
            crop_images = os.listdir(os.path.join(user_upload_folder, "Crop", value))
            image_paths = [os.path.join(user_upload_folder, "Crop", value, j) for j in crop_images]
            detection_datas = (detect_and_merge(image_paths, user_upload_folder, value))
            data = Porn_Data(case_id = case_id,
                            file_original_name = real_names[str(value)],
                            file_original_name_md5 = value,
                            results = detection_datas)
            db.session.add(data)
            db.session.commit()



def crop_image(image_path, user_upload_folder):
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_dir = os.path.join(user_upload_folder, "Crop", base_name)
    cropped_images_list = []
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    image = cv2.imread(image_path)
    if image is None:
        print("이미지를 로드할 수 없습니다.")
        exit()

    height, width, _ = image.shape

    crop_width = width // 5
    crop_height = height // 2

    count = 0
    for row in range(2):
        for col in range(5): 
            x_start = col * crop_width
            y_start = row * crop_height
            x_end = x_start + crop_width
            y_end = y_start + crop_height

            cropped_image = image[y_start:y_end, x_start:x_end]
            if cropped_image.size == 0:
                print(f"Crop {count + 1}에서 유효하지 않은 이미지 조각입니다.")
                continue

            output_path = os.path.join(output_dir, f"crop_{count + 1}.jpg")
            cv2.imwrite(output_path, cropped_image)
            count += 1
            cropped_images_list.append(f"crop_{count + 1}.jpg")

    # print(f"이미지를 총 {count}개의 파일로 저장했습니다. 저장 경로: {output_dir}")
    return cropped_images_list

def detect_and_merge(image_paths, user_upload_folder, md5_strings):
    output_folder = "Detect"
    if not os.path.exists(os.path.join(user_upload_folder, output_folder)):
        os.makedirs(os.path.join(user_upload_folder, output_folder))
    
    output_folder = "Results"
    if not os.path.exists(os.path.join(user_upload_folder, output_folder)):
        os.makedirs(os.path.join(user_upload_folder, output_folder))

    # 이미지 저장을 위한 리스트
    images = []
    detection_datas = []
    for image_path in image_paths:
        # 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            print(f"이미지를 로드할 수 없습니다: {image_path}")
            continue  # 이미지 로드 실패 시 다음 이미지로 넘어감

        detections = detector.detect(image_path)

        output_folder = md5_strings
        print(user_upload_folder)
        if not os.path.exists(os.path.join(user_upload_folder, "Detect", output_folder)):
            os.makedirs(os.path.join(user_upload_folder, "Detect", output_folder))
        # output_path_detect = os.path.join(user_upload_folder, "Detect", md5_strings, image_path)
        output_path_detect = os.path.join(user_upload_folder, "Detect", md5_strings, image_path.replace("Crop", "Detect"))
        # print(f"감지된 객체: {detections}")  # 감지된 객체 출력
        print(output_path_detect)
        class_colors = {
            "FEMALE_GENITALIA_COVERED": (255, 200, 200),  # 연한 빨간색
            "FACE_FEMALE": (255, 0, 0),  # 빨간색
            "BUTTOCKS_EXPOSED": (255, 165, 0),  # 주황색
            "FEMALE_BREAST_EXPOSED": (0, 255, 0),  # 초록색
            "FEMALE_GENITALIA_EXPOSED": (128, 0, 128),  # 보라색
            "MALE_BREAST_EXPOSED": (0, 255, 255),  # 청록색
            "ANUS_EXPOSED": (255, 105, 180),  # 핑크색
            "FEET_EXPOSED": (128, 128, 0),  # 올리브색
            "BELLY_COVERED": (0, 128, 128),  # 어두운 청록색
            "FEET_COVERED": (100, 149, 237),  # 코발트 블루
            "ARMPITS_COVERED": (238, 130, 238),  # 바이올렛
            "ARMPITS_EXPOSED": (255, 223, 0),  # 노란색
            "FACE_MALE": (0, 0, 255),  # 파란색
            "BELLY_EXPOSED": (0, 255, 127),  # 밝은 초록색
            "MALE_GENITALIA_EXPOSED": (255, 69, 0),  # 다홍색
            "ANUS_COVERED": (139, 69, 19),  # 갈색
            "FEMALE_BREAST_COVERED": (75, 0, 130),  # 인디고
            "BUTTOCKS_COVERED": (169, 169, 169),  # 다크 그레이
        }

        

        for detection in detections:
            x, y, w, h = detection['box']
            class_name = detection['class']
            score = detection['score']

            # 클래스에 해당하는 색상 가져오기 (없으면 기본값: 흰색)
            color = class_colors.get(class_name, (255, 255, 255))

            # 좌표 계산 (x, y, x+w, y+h)
            top_left = (x, y)
            bottom_right = (x + w, y + h)

            # 클래스별 색상 박스와 텍스트 추가
            cv2.rectangle(image, top_left, bottom_right, color, 2)  # 박스 (2픽셀 두께)
            text = f"{class_name} ({score:.2f})"
            cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        print(output_path_detect)
        if cv2.imwrite(output_path_detect, image):
            print(f"결과 이미지가 저장되었습니다 > : {output_path_detect}")
        else:
            print(f"이미지 저장에 실패했습니다: {output_path_detect}")

        images.append(image)  # 감지된 이미지를 리스트에 추가
        detection_datas.append(detections)

    # 5x2 형태로 이미지를 합치기
    if len(images) > 0:
        merged_image = np.vstack([np.hstack(images[i:i + 5]) for i in range(0, len(images), 5)])
        
        # 결과 저장
        output_path = os.path.join(user_upload_folder, "Results", f"{md5_strings}_detect_result.jpg")
        cv2.imwrite(output_path, merged_image)
        print(f"결과 이미지가 저장되었습니다: {output_path}")
    else:
        print("합칠 이미지가 없습니다.")
    return detection_datas

