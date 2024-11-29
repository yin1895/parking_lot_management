import onnxruntime as ort
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import copy

class PlateRecognizer:
    def __init__(self, detect_model_path, rec_model_path):
        # 加载ONNX模型
        providers = ['CPUExecutionProvider']
        self.detect_session = ort.InferenceSession(detect_model_path, providers=providers)
        self.rec_session = ort.InferenceSession(rec_model_path, providers=providers)
        self.camera = None
        self.plate_color_list = ['黑色', '蓝色', '绿色', '白色', '黄色']
        self.plateName = r"#京沪津渝冀晋蒙辽吉黑苏浙皖闽赣鲁豫鄂湘粤桂琼川贵云藏陕甘青宁新学警港澳挂使领民航危0123456789ABCDEFGHJKLMNPQRSTUVWXYZ险品"
        self.mean_value, self.std_value = (0.588, 0.193)  # 识别模型均值标准差

    def preprocess_image(self, image):
        # 检测前处理
        img, r, left, top = self.my_letter_box(image, (640, 640))
        img = img[:, :, ::-1].transpose(2, 0, 1).copy().astype(np.float32)
        img = img / 255
        img = img.reshape(1, *img.shape)
        return img, r, left, top

    def my_letter_box(self, img, size=(640, 640)):
        h, w, c = img.shape
        r = min(size[0] / h, size[1] / w)
        new_h, new_w = int(h * r), int(w * r)
        top = int((size[0] - new_h) / 2)
        left = int((size[1] - new_w) / 2)
        bottom = size[0] - new_h - top
        right = size[1] - new_w - left
        img_resize = cv2.resize(img, (new_w, new_h))
        img = cv2.copyMakeBorder(img_resize, top, bottom, left, right, borderType=cv2.BORDER_CONSTANT, value=(114, 114, 114))
        return img, r, left, top

    def detect_plate(self, image):
        # 使用检测模型找到车牌
        img, r, left, top = self.preprocess_image(image)
        y_onnx = self.detect_session.run([self.detect_session.get_outputs()[0].name], {self.detect_session.get_inputs()[0].name: img})[0]
        outputs = self.post_processing(y_onnx, r, left, top)
        return outputs

    def post_processing(self, dets, r, left, top, conf_thresh=0.3, iou_thresh=0.5):
        choice = dets[:, :, 4] > conf_thresh
        dets = dets[choice]
        dets[:, 13:15] *= dets[:, 4:5]
        box = dets[:, :4]
        boxes = self.xywh2xyxy(box)
        score = np.max(dets[:, 13:15], axis=-1, keepdims=True)
        index = np.argmax(dets[:, 13:15], axis=-1).reshape(-1, 1)
        output = np.concatenate((boxes, score, dets[:, 5:13], index), axis=1)
        reserve_ = self.my_nms(output, iou_thresh)
        output = output[reserve_]
        output = self.restore_box(output, r, left, top)
        return output

    def xywh2xyxy(self, boxes):
        xywh = copy.deepcopy(boxes)
        xywh[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
        xywh[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
        xywh[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
        xywh[:, 3] = boxes[:, 1] + boxes[:, 3] / 2
        return xywh

    def my_nms(self, boxes, iou_thresh):
        index = np.argsort(boxes[:, 4])[::-1]
        keep = []
        while index.size > 0:
            i = index[0]
            keep.append(i)
            x1 = np.maximum(boxes[i, 0], boxes[index[1:], 0])
            y1 = np.maximum(boxes[i, 1], boxes[index[1:], 1])
            x2 = np.minimum(boxes[i, 2], boxes[index[1:], 2])
            y2 = np.minimum(boxes[i, 3], boxes[index[1:], 3])
            w = np.maximum(0, x2 - x1)
            h = np.maximum(0, y2 - y1)
            inter_area = w * h
            union_area = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1]) + (boxes[index[1:], 2] - boxes[index[1:], 0]) * (boxes[index[1:], 3] - boxes[index[1:], 1])
            iou = inter_area / (union_area - inter_area)
            idx = np.where(iou <= iou_thresh)[0]
            index = index[idx + 1]
        return keep

    def restore_box(self, boxes, r, left, top):
        boxes[:, [0, 2, 5, 7, 9, 11]] -= left
        boxes[:, [1, 3, 6, 8, 10, 12]] -= top
        boxes[:, [0, 2, 5, 7, 9, 11]] /= r
        boxes[:, [1, 3, 6, 8, 10, 12]] /= r
        return boxes

    def recognize_text(self, plate_image):
        # 使用识别模型提取车牌文字
        img = self.rec_pre_processing(plate_image)
        y_onnx_plate, y_onnx_color = self.rec_session.run([self.rec_session.get_outputs()[0].name, self.rec_session.get_outputs()[1].name], {self.rec_session.get_inputs()[0].name: img})
        index = np.argmax(y_onnx_plate, axis=-1)
        index_color = np.argmax(y_onnx_color)
        plate_color = self.plate_color_list[index_color]
        plate_no = self.decode_plate(index[0])
        return plate_no, plate_color

    def rec_pre_processing(self, img, size=(48, 168)):
        img = cv2.resize(img, (168, 48))
        img = img.astype(np.float32)
        img = (img / 255 - self.mean_value) / self.std_value
        img = img.transpose(2, 0, 1)
        img = img.reshape(1, *img.shape)
        return img

    def decode_plate(self, preds):
        pre = 0
        new_preds = []
        for i in range(len(preds)):
            if preds[i] != 0 and preds[i] != pre:
                new_preds.append(preds[i])
            pre = preds[i]
        plate = ""
        for i in new_preds:
            plate += self.plateName[int(i)]
        return plate

    def capture_and_recognize(self):
        # 使用摄像头捕获图像并识别车牌
        if self.camera is None:
            self.camera = cv2.VideoCapture(0)

        ret, frame = self.camera.read()
        if not ret:
            return False, "无法从摄像头读取图像"

        outputs = self.detect_plate(frame)
        if outputs is not None:
            for output in outputs:
                rect = output[:4].astype(int)
                plate_image = frame[rect[1]:rect[3], rect[0]:rect[2]]
                plate_no, plate_color = self.recognize_text(plate_image)
                return True, f"车牌号: {plate_no}, 颜色: {plate_color}"

        return False, "未检测到车牌"

    def stop_camera(self):
        # 停止摄像头
        if self.camera is not None:
            self.camera.release()
            self.camera = None
